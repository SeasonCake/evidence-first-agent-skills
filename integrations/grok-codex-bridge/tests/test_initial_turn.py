import queue
import unittest
from unittest.mock import Mock

from grok_codex_bridge.initial_turn import InitialTurnMixin
from grok_codex_bridge.trace import RpcError


class InitialTurnTests(unittest.TestCase):
    def run_case(self, reply='GROK_TASK_READY', status='completed', extra=None):
        client = InitialTurnMixin()
        client.incoming = queue.Queue()
        client._send = Mock()
        def request(method, params):
            self.assertEqual(method, 'turn/start')
            self.assertEqual(params['threadId'], 'task-id')
            # Notifications can precede the RPC reply; the collector must preserve them.
            client.on_notification({'method': 'item/completed', 'params': {
                'threadId': 'task-id', 'turnId': 'turn-id', 'item': {'type': 'agentMessage', 'text': reply}}})
            if extra:
                client.incoming.put(extra)
            client.incoming.put({'method': 'turn/completed', 'params': {
                'threadId': 'task-id', 'turn': {'id': 'turn-id', 'status': status}}})
            return {'turn': {'id': 'turn-id'}}
        client._request = request
        callback = Mock()
        result = client.initialize_task('task-id', 'request-01', callback)
        callback.assert_called_once_with('turn-id')
        return result

    def test_exact_real_reply_and_early_notification(self):
        result = self.run_case()
        self.assertEqual(result['initialReply'], 'GROK_TASK_READY')
        self.assertEqual(result['initialToolItems'], 0)

    def test_wrong_reply_is_not_ready(self):
        with self.assertRaises(RpcError):
            self.run_case(reply='different')

    def test_failed_turn_is_not_ready(self):
        with self.assertRaises(RpcError):
            self.run_case(status='failed')

    def test_tool_item_is_not_a_no_tools_success(self):
        with self.assertRaises(RpcError):
            self.run_case(extra={'method': 'item/completed', 'params': {
                'threadId': 'task-id', 'turnId': 'turn-id', 'item': {'type': 'commandExecution'}}})

    def test_unexpected_approval_is_rejected(self):
        with self.assertRaises(RpcError):
            self.run_case(extra={'method': 'item/commandExecution/requestApproval', 'id': 5,
                                 'params': {'threadId': 'task-id'}})


if __name__ == '__main__':
    unittest.main()
