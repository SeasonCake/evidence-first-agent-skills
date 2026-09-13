"""Bounded read-only projection of tool records omitted by some app-server views."""
import json
from pathlib import Path

from .trace import RpcError, clip

TOOL_TYPES = frozenset({'function_call', 'function_call_output', 'custom_tool_call', 'custom_tool_call_output'})
MAX_HEADER_BYTES = 2 * 1024 * 1024
DEFAULT_WINDOW_BYTES = 256 * 1024


def read_raw_tools(path, thread_id, limit=20, cursor=None, include_content=False,
                   window_bytes=DEFAULT_WINDOW_BYTES):
    if type(limit) is not int or not 1 <= limit <= 50 or not 4096 <= window_bytes <= 1024 * 1024:
        raise ValueError('Raw tool pages require 1–50 entries and a bounded byte window')
    selected = Path(path)
    with selected.open('rb') as handle:
        header = handle.readline(MAX_HEADER_BYTES + 1)
        if len(header) > MAX_HEADER_BYTES:
            raise RpcError('Selected rollout header exceeds the bounded identity read')
        try:
            identity = json.loads(header)
        except (ValueError, UnicodeDecodeError) as error:
            raise RpcError('Selected rollout header is not readable JSON') from error
        if identity.get('type') != 'session_meta' or identity.get('payload', {}).get('id') != thread_id:
            raise RpcError('Selected raw rollout identity does not match this task; no alternate history scan')
        handle.seek(0, 2)
        file_size = handle.tell()
        end = file_size
        if cursor is not None:
            prefix = 'raw-v1:' + thread_id + ':'
            if not cursor.startswith(prefix) or not cursor[len(prefix):].isdigit():
                raise ValueError('Raw cursor must belong to this task')
            end = int(cursor[len(prefix):])
            if end > file_size:
                raise RpcError('Raw source shrank or cursor is invalid; inspect identity before continuing')
        start = max(0, end - window_bytes)
        preceding = b'\n'
        if start:
            handle.seek(start - 1)
            preceding = handle.read(1)
        handle.seek(start)
        data = handle.read(end - start)
    skipped_partial = start > 0 and preceding != b'\n'
    read_start = start
    if skipped_partial:
        boundary = data.find(b'\n')
        advance = len(data) if boundary < 0 else boundary + 1
        data = data[advance:]
        read_start += advance
    partial_tail = bool(data) and not data.endswith(b'\n')
    if partial_tail:
        last_boundary = data.rfind(b'\n')
        data = data[:last_boundary + 1]
    events = []
    offset = read_start
    malformed = 0
    names = {}
    for line in data.splitlines(keepends=True):
        position = offset
        offset += len(line)
        try:
            record = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            malformed += 1
            continue
        if not isinstance(record, dict):
            malformed += 1
            continue
        item = record.get('payload', {})
        if not isinstance(item, dict):
            malformed += 1
            continue
        if record.get('type') != 'response_item' or item.get('type') not in TOOL_TYPES:
            continue
        call_id = item.get('call_id')
        if item.get('name') and call_id:
            names[call_id] = item['name']
        event = {'timestamp': record.get('timestamp'), 'type': item['type'], 'callId': call_id,
                 'name': item.get('name') or names.get(call_id), 'byteOffset': position}
        if item.get('namespace') is not None:
            event['namespace'] = item['namespace']
        if include_content:
            for field in ('arguments', 'input', 'output'):
                if field in item:
                    value = item[field]
                    if not isinstance(value, str):
                        value = json.dumps(value, ensure_ascii=False)
                    event[field] = clip(value, 1600)
        events.append(event)
    chosen = events[-limit:]
    if len(events) > limit:
        before = chosen[0]['byteOffset']
    elif start:
        # Include the skipped boundary line in the next older window when possible.
        before = read_start if read_start < end else start
    else:
        before = 0
    return {'source': 'bounded canonical rollout tool records, read-only', 'threadId': thread_id,
            'data': list(reversed(chosen)), 'fileBytesAtRead': file_size,
            'windowBytes': end - start, 'headerBytes': len(header),
            'partialBoundarySkipped': skipped_partial, 'incompleteTailSkipped': partial_tail,
            'malformedLines': malformed, 'wholeFileCovered': start == 0 and not partial_tail and malformed == 0,
            'allToolEventsReturned': start == 0 and not partial_tail and malformed == 0 and len(events) <= limit,
            'nextCursor': 'raw-v1:' + thread_id + ':' + str(before) if before else None,
            'contentIncluded': include_content}
