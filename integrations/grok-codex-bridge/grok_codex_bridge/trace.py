"""Read a bounded page of persisted Codex task history, without running a model."""
import argparse
from collections import Counter
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from urllib.parse import quote

READ_METHODS = frozenset({'thread/read', 'thread/turns/list', 'thread/items/list', 'thread/list'})
MAX_LINE_BYTES = 8 * 1024 * 1024


class RpcError(RuntimeError):
    pass


class ReadOnlyAppServer:
    """Own one stdio transport; never attach to or stop an existing process."""
    def __init__(self, binary, cwd, timeout=15):
        self.binary = Path(binary)
        self.cwd = Path(cwd)
        if not self.binary.is_file() or not self.cwd.is_dir():
            raise ValueError('An existing Codex binary and explicit cwd are required')
        if not 1 <= timeout <= 30:
            raise ValueError('Timeout must be between 1 and 30 seconds')
        self.timeout = timeout
        self.incoming = queue.Queue(maxsize=128)
        self.counter = 0
        self.process = None
        self.reader = None

    def __enter__(self):
        self.process = subprocess.Popen(
            [str(self.binary), 'app-server', '--stdio'], cwd=self.cwd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self._request('initialize', {
                'clientInfo': {'name': 'grok_codex_trace', 'version': '0.1.0'},
                'capabilities': {'experimentalApi': True}})
            self._send({'method': 'initialized'})
            return self
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            while True:
                line = self.process.stdout.readline(MAX_LINE_BYTES + 1)
                if not line:
                    break
                if len(line) > MAX_LINE_BYTES:
                    raise RpcError('Response line exceeds the 8 MiB bound')
                try:
                    self.incoming.put(json.loads(line), timeout=self.timeout)
                except json.JSONDecodeError:
                    continue
        except (OSError, ValueError, queue.Full, RpcError) as error:
            try:
                self.incoming.put(error, timeout=1)
            except queue.Full:
                pass
        finally:
            try:
                self.incoming.put(None, timeout=1)
            except queue.Full:
                pass

    def _send(self, value):
        self.process.stdin.write((json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8'))
        self.process.stdin.flush()

    def _request(self, method, params):
        self.counter += 1
        request_id = self.counter
        self._send({'id': request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Read-only app-server request timed out')
            try:
                message = self.incoming.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError('Read-only app-server request timed out') from error
            if message is None:
                raise RpcError('App-server closed before replying')
            if isinstance(message, Exception):
                raise message
            if not isinstance(message, dict):
                continue
            if 'method' in message and 'id' in message:
                self._send({'id': message['id'], 'error': {
                    'code': -32601, 'message': 'This trace reader does not authorize actions'}})
                raise RpcError('Unexpected action request during read-only history inspection')
            if message.get('id') != request_id:
                if 'method' in message:
                    self.on_notification(message)
                continue
            if 'error' in message:
                failure = message['error']
                raise RpcError(f"{method}: {str(failure.get('message', 'RPC rejected'))[:500]}")
            if 'result' not in message:
                raise RpcError('RPC reply has no result')
            return message['result']

    def on_notification(self, message):
        """Read-only clients need no live events; a creation client can collect its own."""

    def call(self, method, params):
        if method not in READ_METHODS:
            raise ValueError('Only bounded read-only task methods are allowed')
        if method.endswith('/list') and not 1 <= params.get('limit', 0) <= 50:
            raise ValueError('A list page must contain between 1 and 50 entries')
        if method == 'thread/read' and params.get('includeTurns') is not False:
            raise ValueError('Read metadata first; full-history hydration is not allowed')
        if method == 'thread/list' and params.get('useStateDbOnly') is not True:
            raise ValueError('Task discovery must use bounded metadata-only listing without rollout scan/repair')
        return self._request(method, params)

    def close(self):
        if self.process is None:
            return
        try:
            self.process.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        if self.reader:
            self.reader.join(timeout=1)
        if self.process.stdout:
            self.process.stdout.close()

    def __exit__(self, *unused):
        self.close()


def clip(value, limit):
    text = str(value)
    return {'text': text[:limit], 'truncated': len(text) > limit, 'characters': len(text)}


def read_thread_metadata(client, thread_id):
    """A fresh reader can briefly report not-loaded; retry only that exact condition."""
    expected = 'thread/read: thread not loaded: ' + thread_id
    for attempt in range(3):
        try:
            result = client.call('thread/read', {'threadId': thread_id, 'includeTurns': False})
            return {**result, '_bridgeReadAttempts': attempt + 1}
        except RpcError as error:
            if str(error) != expected or attempt == 2:
                raise
            time.sleep((0.15, 0.5)[attempt])


def project_item(entry, include_content=False, content_limit=1600):
    item = entry.get('item')
    if not isinstance(item, dict):
        raise RpcError('Unexpected item entry shape; refusing to turn it into empty history')
    output = {key: entry[key] for key in ['turnId', 'cursor'] if key in entry}
    output.update({key: item[key] for key in ['id', 'type', 'status', 'exitCode', 'durationMs'] if key in item})
    if item.get('type') == 'functionCallOutput':
        output.update({key: item[key] for key in ['name', 'namespace'] if key in item})
    if include_content:
        kind = item.get('type')
        # User-visible messages/actions only. Never export reasoning or encrypted items.
        if kind == 'agentMessage':
            output['content'] = clip(item.get('text', ''), content_limit)
        elif kind == 'userMessage':
            parts = item.get('content', [])
            output['content'] = clip('\n'.join(x.get('text', '') for x in parts
                if isinstance(x, dict) and x.get('type') == 'text'), content_limit)
        elif kind == 'commandExecution':
            output['command'] = clip(item.get('command', ''), content_limit)
            output['output'] = clip(item.get('aggregatedOutput', ''), content_limit)
        elif kind == 'functionCallOutput' and item.get('name') == 'send_message_to_thread':
            # Preserve coordinator-message provenance. This is a raw tool envelope,
            # not a direct user message or proof of authority for its instructions.
            output['contentKind'] = 'rawCoordinatorToolEnvelope'
            output['output'] = clip(item.get('output', ''), content_limit)
    return output


def read_trace(client, thread_id, turn_limit=3, item_limit=30,
               turns_cursor=None, items_cursor=None, expected_provider=None, include_content=False,
               include_raw_tools=False, raw_cursor=None):
    if not thread_id or not 1 <= turn_limit <= 20 or not 1 <= item_limit <= 50:
        raise ValueError('A task ID and bounded page sizes are required')
    if raw_cursor is not None and not include_raw_tools:
        raise ValueError('A raw cursor requires the raw-tools option')
    meta = read_thread_metadata(client, thread_id)
    thread = meta.get('thread')
    if not isinstance(thread, dict) or thread.get('id') != thread_id:
        raise RpcError('Returned task identity does not match the requested task')
    if expected_provider is not None and thread.get('modelProvider') != expected_provider:
        raise RpcError('Provider mismatch or unavailable provider metadata; no fallback')
    turns_params = {'threadId': thread_id, 'limit': turn_limit,
                    'sortDirection': 'desc', 'itemsView': 'notLoaded'}
    items_params = {'threadId': thread_id, 'limit': item_limit, 'sortDirection': 'desc'}
    if turns_cursor is not None:
        turns_params['cursor'] = turns_cursor
    if items_cursor is not None:
        items_params['cursor'] = items_cursor
    turns = client.call('thread/turns/list', turns_params)
    items = client.call('thread/items/list', items_params)
    if not isinstance(turns.get('data'), list) or not isinstance(items.get('data'), list):
        raise RpcError('Unexpected pagination response; this is not an empty-history result')
    result = {
        'schemaVersion': 1,
        'scope': 'bounded persisted-history snapshot, not a live stream or full transcript',
        'thread': {key: thread[key] for key in ['id', 'name', 'model', 'modelProvider',
            'reasoningEffort', 'canAcceptDirectInput', 'ephemeral', 'historyMode', 'cwd',
            'parentThreadId', 'source', 'threadSource', 'status'] if key in thread},
        'openInCodex': 'codex://threads/' + quote(thread_id, safe=''),
        'turns': {'data': [{key: t[key] for key in ['id', 'status', 'startedAt', 'completedAt',
            'durationMs', 'itemsView'] if key in t} for t in turns['data']],
            'nextCursor': turns.get('nextCursor')},
        'items': {'data': [project_item(i, include_content) for i in items['data']],
            'typeCounts': dict(Counter(i.get('item', {}).get('type', 'unknown') for i in items['data'])),
            'nextCursor': items.get('nextCursor')},
        'contentIncluded': include_content,
        'modelRequestsStarted': 0,
        'metadataReadAttempts': meta['_bridgeReadAttempts'],
    }
    if include_raw_tools:
        from .raw_tools import read_raw_tools
        try:
            if not thread.get('path'):
                raise RpcError('This host did not provide a raw rollout locator')
            result['rawToolEvents'] = read_raw_tools(thread['path'], thread_id, min(item_limit, 50),
                                                    raw_cursor, include_content)
        except (OSError, RpcError, ValueError) as error:
            result['rawToolEvents'] = {'errorClass': type(error).__name__, 'message': str(error)[:500],
                                       'wholeFileCovered': False, 'dataUnavailable': True}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-binary', required=True)
    parser.add_argument('--thread-id', required=True)
    parser.add_argument('--cwd', default=str(Path.cwd()))
    parser.add_argument('--turn-limit', type=int, default=3)
    parser.add_argument('--item-limit', type=int, default=30)
    parser.add_argument('--turns-cursor')
    parser.add_argument('--items-cursor')
    parser.add_argument('--expect-provider')
    parser.add_argument('--raw-tools', action='store_true')
    parser.add_argument('--raw-cursor')
    parser.add_argument('--include-content', action='store_true',
                        help='Opt in to clipped visible text/tool output; keep private task data out of public logs')
    args = parser.parse_args()
    with ReadOnlyAppServer(args.codex_binary, args.cwd) as client:
        result = read_trace(client, args.thread_id, args.turn_limit, args.item_limit,
            args.turns_cursor, args.items_cursor, args.expect_provider, args.include_content,
            args.raw_tools, args.raw_cursor)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
