"""One real no-tools initialization turn before the native app takes ownership."""
from collections import deque
import queue
import time

from .trace import RpcError

READY_MARKER = 'GROK_TASK_READY'
INITIAL_PROMPT = (
    'This is the bridge initialization turn for the new dedicated Grok Codex task the user requested. '
    'A real first turn is needed to materialize this host\'s persistent history before the creator exits. '
    'Do not call tools, read or edit files, create agents, inspect configuration, or take other actions. '
    'Reply only GROK_TASK_READY. The user or coordinating task will provide the actual work afterwards.')


class InitialTurnMixin:
    def on_notification(self, message):
        if hasattr(self, 'initial_events'):
            self.initial_events.append(message)

    def initialize_task(self, thread_id, request_key, on_started):
        self.initial_events = deque(maxlen=128)
        response = self._request('turn/start', {'threadId': thread_id,
            'clientUserMessageId': 'grok-bridge-init-' + request_key,
            'input': [{'type': 'text', 'text': INITIAL_PROMPT}]})
        turn_id = response.get('turn', {}).get('id')
        if not turn_id:
            raise RpcError('Initialization turn ID missing')
        on_started(turn_id)
        deadline = time.monotonic() + 45
        replies = []
        tool_items = []
        while True:
            if self.initial_events:
                message = self.initial_events.popleft()
            else:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Initialization turn deadline; retain task/turn ID and reconcile, do not recreate')
                try:
                    message = self.incoming.get(timeout=remaining)
                except queue.Empty as error:
                    raise TimeoutError('Initialization turn deadline') from error
            if message is None:
                raise RpcError('Creator connection ended before initialization completed')
            if isinstance(message, Exception):
                raise message
            if not isinstance(message, dict):
                continue
            if 'method' in message and 'id' in message:
                self._send({'id': message['id'], 'error': {
                    'code': -32601, 'message': 'The no-tools initialization does not authorize this action'}})
                raise RpcError('Unexpected action request during initialization')
            params = message.get('params', {})
            if params.get('threadId') != thread_id:
                continue
            if message.get('method') == 'item/completed' and params.get('turnId') == turn_id:
                item = params.get('item', {})
                kind = item.get('type')
                if kind == 'agentMessage':
                    replies.append(item.get('text', ''))
                elif kind not in {'userMessage', 'reasoning'}:
                    tool_items.append(kind)
            if message.get('method') == 'turn/completed' and params.get('turn', {}).get('id') == turn_id:
                status = params['turn'].get('status')
                if status != 'completed' or tool_items or not any(text.strip() == READY_MARKER for text in replies):
                    raise RpcError('Initialization did not complete with the expected no-tools reply')
                return {'initialTurnId': turn_id, 'initialReply': READY_MARKER,
                        'initialToolItems': 0, 'initialModelTurnsStarted': 1}
