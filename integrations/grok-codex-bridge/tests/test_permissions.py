import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from grok_codex_bridge.permissions import inspect_permissions, read_turn_permissions
from grok_codex_bridge.trace import RpcError

THREAD = 'fixture-task-001'
TURN = 'fixture-turn-001'


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='permission-inspection-')
        self.path = Path(self.temp.name) / 'synthetic.jsonl'

    def tearDown(self):
        self.temp.cleanup()

    def write(self, records):
        header = {'type': 'session_meta', 'payload': {'id': THREAD}}
        self.path.write_text(''.join(json.dumps(r) + '\n' for r in [header, *records]), encoding='utf-8')

    def context(self, **changes):
        return {'type': 'turn_context', 'timestamp': 'fixture-time', 'payload': {
            'turn_id': TURN, 'approval_policy': 'on-request',
            'sandbox_policy': {'type': 'read-only'}, 'private': 'NEVER_EXPORT', **changes}}

    def test_readonly_is_visible_without_mutation(self):
        self.write([self.context()])
        before = self.path.read_bytes()
        result = read_turn_permissions(self.path, THREAD, TURN)
        self.assertEqual(result['approval_policy'], 'on-request')
        self.assertTrue(result['write_restriction_observed'])
        self.assertFalse(result['permissions_changed'])
        self.assertEqual(result['approval_actions'], 0)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertNotIn('NEVER_EXPORT', json.dumps(result))

    def test_other_turn_not_substituted(self):
        self.write([self.context(turn_id='another-turn-001')])
        result = read_turn_permissions(self.path, THREAD, TURN)
        self.assertEqual(result['status'], 'unavailable-in-bounded-window')
        self.assertNotIn('approval_policy', result)

    def test_unknown_fields_stay_unknown(self):
        self.write([self.context(approval_policy=None, sandbox_policy=None)])
        result = read_turn_permissions(self.path, THREAD, TURN)
        self.assertIsNone(result['approval_policy'])
        self.assertIsNone(result['sandbox_type'])
        self.assertIsNone(result['write_restriction_observed'])
        self.assertFalse(result['parent_permissions_inferred'])

    def test_wrong_history_identity_rejected(self):
        self.write([])
        with self.assertRaises(RpcError):
            read_turn_permissions(self.path, 'wrong-task-001', TURN)

    def test_last_exact_context_selected(self):
        self.write([self.context(), self.context(sandbox_policy={'type': 'workspace-write'})])
        result = read_turn_permissions(self.path, THREAD, TURN)
        self.assertEqual(result['sandbox_type'], 'workspace-write')
        self.assertFalse(result['write_restriction_observed'])

    def test_window_does_not_claim_absence_or_export_messages(self):
        self.write([self.context(), {'type': 'response_item', 'payload': {'text': 'PRIVATE' * 2000}}])
        result = read_turn_permissions(self.path, THREAD, TURN, window_bytes=4096)
        self.assertEqual(result['status'], 'unavailable-in-bounded-window')
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_incomplete_tail_is_explicit(self):
        self.write([self.context()])
        with self.path.open('ab') as stream:
            stream.write(b'{"incomplete":')
        self.assertTrue(read_turn_permissions(self.path, THREAD, TURN)['incomplete_tail'])

    def test_only_metadata_rpc_is_used(self):
        self.write([self.context()])
        client = Mock()
        client.call.return_value = {'thread': {'id': THREAD, 'path': str(self.path)}}
        self.assertEqual(inspect_permissions(client, THREAD, TURN)['status'], 'observed')
        client.call.assert_called_once_with('thread/read', {'threadId': THREAD, 'includeTurns': False})

    def test_invalid_input_and_locator_rejected(self):
        self.write([])
        for task, turn in (('../escape', TURN), (THREAD, '')):
            with self.assertRaises(ValueError):
                read_turn_permissions(self.path, task, turn)
        with self.assertRaises(ValueError):
            read_turn_permissions(Path('relative'), THREAD, TURN)


if __name__ == '__main__':
    unittest.main()
