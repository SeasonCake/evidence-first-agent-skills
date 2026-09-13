"""Inspect an exact turn's recorded permissions; never change or approve them."""
import json
from pathlib import Path
import re

from .trace import RpcError, read_thread_metadata

MAX_BYTES = 2 * 1024 * 1024
IDENTIFIER = re.compile(r'[A-Za-z0-9_-]{8,100}')


def read_turn_permissions(path, thread_id, turn_id, window_bytes=MAX_BYTES):
    if not all(IDENTIFIER.fullmatch(value) for value in (thread_id, turn_id)):
        raise ValueError('Exact task and turn IDs are required')
    if not 4096 <= window_bytes <= MAX_BYTES:
        raise ValueError('Permission inspection requires a 4KiB–2MiB window')
    selected = Path(path)
    if not selected.is_absolute():
        raise ValueError('An absolute host-provided history locator is required')
    for part in (selected, *selected.parents):
        if part.is_symlink() or getattr(part.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Permission inspection cannot follow link/reparse paths')
    with selected.open('rb') as stream:
        header = stream.readline(MAX_BYTES + 1)
        if len(header) > MAX_BYTES:
            raise RpcError('History identity header exceeds the read budget')
        identity = json.loads(header)
        if (not isinstance(identity, dict) or identity.get('type') != 'session_meta'
                or not isinstance(identity.get('payload'), dict)
                or identity['payload'].get('id') != thread_id):
            raise RpcError('History identity mismatch; no alternate history search')
        stream.seek(0, 2)
        size = stream.tell()
        start = max(0, size - window_bytes)
        stream.seek(max(0, start - 1))
        prior = stream.read(1) if start else b'\n'
        stream.seek(start)
        data = stream.read(size - start)
    skipped_start = bool(start and prior != b'\n')
    offset = start
    if skipped_start:
        boundary = data.find(b'\n')
        advance = len(data) if boundary < 0 else boundary + 1
        offset += advance
        data = data[advance:]
    skipped_tail = bool(data and not data.endswith(b'\n'))
    if skipped_tail:
        data = data[:data.rfind(b'\n') + 1]
    result = {'schema': 'grok-turn-permissions/v1', 'thread_id': thread_id,
              'turn_id': turn_id, 'status': 'unavailable-in-bounded-window',
              'permissions_changed': False, 'approval_actions': 0,
              'parent_permissions_inferred': False, 'model_requests_started': 0,
              'history_path': str(selected), 'header_bytes': len(header),
              'window_bytes': min(size, window_bytes), 'partial_start': skipped_start,
              'incomplete_tail': skipped_tail, 'malformed_lines': 0,
              'evidence_scope': 'Persisted exact-turn context, not a live UI setting or authority grant'}
    for line in data.splitlines(keepends=True):
        position = offset
        offset += len(line)
        try:
            record = json.loads(line)
        except (ValueError, UnicodeError):
            result['malformed_lines'] += 1
            continue
        if not isinstance(record, dict) or record.get('type') != 'turn_context':
            continue
        payload = record.get('payload')
        if not isinstance(payload, dict) or payload.get('turn_id') != turn_id:
            continue
        policy = payload.get('approval_policy')
        sandbox = payload.get('sandbox_policy')
        profile = payload.get('permission_profile')
        result.update(status='observed', context_timestamp=record.get('timestamp'),
                      byte_offset=position,
                      approval_policy=policy if isinstance(policy, str) else
                      'granular' if isinstance(policy, dict) else None,
                      sandbox_type=sandbox.get('type') if isinstance(sandbox, dict) else None,
                      permission_profile_type=profile.get('type') if isinstance(profile, dict) else None)
    if result['status'] == 'observed':
        result['write_restriction_observed'] = (None if result['sandbox_type'] is None
                                               else result['sandbox_type'] == 'read-only')
        result['next_action'] = (
            'Preserve pending work. Review this task in the host permission UI with the user; '
            'do not auto-approve, change settings, or use another writer to bypass the restriction.'
            if result['write_restriction_observed'] else
            'Apply the recorded limits and current host decisions; this snapshot does not authorize an operation.')
    return result


def inspect_permissions(client, thread_id, turn_id):
    metadata = read_thread_metadata(client, thread_id)['thread']
    if metadata.get('id') != thread_id or not metadata.get('path'):
        raise RpcError('Exact task history locator unavailable')
    return read_turn_permissions(metadata['path'], thread_id, turn_id)
