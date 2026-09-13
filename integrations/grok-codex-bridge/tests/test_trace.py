import unittest
from unittest.mock import Mock, patch

from grok_codex_bridge.trace import ReadOnlyAppServer, RpcError, clip, project_item, read_trace, read_thread_metadata


class TraceTests(unittest.TestCase):
    def client(self, provider='ocx-grok'):
        client = Mock()
        client.call.side_effect = [
            {'thread': {'id': 'fixture-task', 'modelProvider': provider,
                        'canAcceptDirectInput': True, 'ephemeral': False}},
            {'data': [{'id': 'turn-1', 'status': 'completed', 'itemsView': 'notLoaded'}], 'nextCursor': 'turn-cursor'},
            {'data': [{'turnId': 'turn-1', 'item': {'id': 'msg-1', 'type': 'agentMessage',
                        'text': 'fixture answer'}}], 'nextCursor': 'item-cursor'},
        ]
        return client

    def test_bounded_metadata_and_separate_item_page(self):
        client = self.client()
        result = read_trace(client, 'fixture-task', expected_provider='ocx-grok')
        self.assertEqual(result['items']['typeCounts'], {'agentMessage': 1})
        self.assertEqual(result['turns']['nextCursor'], 'turn-cursor')
        self.assertNotIn('content', result['items']['data'][0])
        self.assertEqual(result['modelRequestsStarted'], 0)
        self.assertEqual(client.call.call_args_list[1].args[1]['itemsView'], 'notLoaded')

    def test_mismatched_provider_stops_before_history(self):
        client = self.client('openai')
        with self.assertRaises(RpcError):
            read_trace(client, 'fixture-task', expected_provider='ocx-grok')
        self.assertEqual(client.call.call_count, 1)

    def test_identity_mismatch_rejected(self):
        client = self.client()
        with self.assertRaises(RpcError):
            read_trace(client, 'another-task')

    def test_missing_page_is_not_empty_history(self):
        client = self.client()
        client.call.side_effect = [{'thread': {'id': 'fixture-task'}}, {}, {'data': []}]
        with self.assertRaises(RpcError):
            read_trace(client, 'fixture-task')

    def test_explicit_empty_pages_are_valid(self):
        client = self.client()
        client.call.side_effect = [{'thread': {'id': 'fixture-task'}}, {'data': []}, {'data': []}]
        self.assertEqual(read_trace(client, 'fixture-task')['items']['data'], [])

    def test_opaque_cursors_are_forwarded_unchanged(self):
        client = self.client()
        read_trace(client, 'fixture-task', turns_cursor='opaque-t', items_cursor='opaque-i')
        self.assertEqual(client.call.call_args_list[1].args[1]['cursor'], 'opaque-t')
        self.assertEqual(client.call.call_args_list[2].args[1]['cursor'], 'opaque-i')

    def test_content_is_explicit_and_bounded(self):
        item = {'item': {'type': 'agentMessage', 'text': 'abcdef'}}
        result = project_item(item, True, 3)
        self.assertEqual(result['content'], {'text': 'abc', 'truncated': True, 'characters': 6})

    def test_reasoning_and_unknown_types_never_export_contents(self):
        for kind in ['reasoning', 'futureItem']:
            result = project_item({'item': {'type': kind, 'text': 'private', 'encryptedContent': 'opaque'}}, True)
            self.assertEqual(result, {'type': kind})

    def test_bad_item_shape_is_an_error(self):
        with self.assertRaises(RpcError):
            project_item({'text': 'not an item'})

    def test_unicode_content_remains_text(self):
        self.assertEqual(clip('你好', 3)['text'], '你好')

    def test_coordinator_envelope_is_opt_in_and_bounded(self):
        entry = {'turnId': 't', 'item': {'type': 'functionCallOutput',
            'name': 'send_message_to_thread', 'namespace': 'codex', 'output': '<input>fixture</input>'}}
        metadata = project_item(entry)
        self.assertEqual(metadata['name'], 'send_message_to_thread')
        self.assertNotIn('output', metadata)
        detailed = project_item(entry, True, 7)
        self.assertEqual(detailed['contentKind'], 'rawCoordinatorToolEnvelope')
        self.assertEqual(detailed['output']['text'], '<input>')
        self.assertTrue(detailed['output']['truncated'])
        self.assertEqual(detailed['type'], 'functionCallOutput')

    def test_other_function_outputs_remain_metadata_only(self):
        result = project_item({'item': {'type': 'functionCallOutput',
            'name': 'unknown_tool', 'output': 'not selected for export'}}, True)
        self.assertEqual(result, {'type': 'functionCallOutput', 'name': 'unknown_tool'})

    def test_page_limits_are_required(self):
        with self.assertRaises(ValueError):
            read_trace(self.client(), 'fixture-task', item_limit=51)

    def test_transport_rejects_mutations(self):
        client = ReadOnlyAppServer.__new__(ReadOnlyAppServer)
        client._request = Mock()
        for method in ['thread/start', 'thread/resume', 'turn/start', 'config/value/write']:
            with self.assertRaises(ValueError):
                client.call(method, {})
        client._request.assert_not_called()

    def test_transport_rejects_unbounded_history_and_pages(self):
        client = ReadOnlyAppServer.__new__(ReadOnlyAppServer)
        with self.assertRaises(ValueError):
            client.call('thread/read', {'includeTurns': True})
        with self.assertRaises(ValueError):
            client.call('thread/items/list', {'limit': 0})

    @patch('grok_codex_bridge.trace.time.sleep')
    def test_exact_transient_not_loaded_has_bounded_same_connection_retry(self, sleep):
        client = Mock()
        client.call.side_effect = [RpcError('thread/read: thread not loaded: fixture-task'),
                                  {'thread': {'id': 'fixture-task'}}]
        result = read_thread_metadata(client, 'fixture-task')
        self.assertEqual(result['_bridgeReadAttempts'], 2)
        sleep.assert_called_once_with(0.15)
        self.assertEqual(client.call.call_count, 2)

    @patch('grok_codex_bridge.trace.time.sleep')
    def test_not_loaded_retries_stop_and_other_errors_are_not_retried(self, sleep):
        client = Mock()
        client.call.side_effect = RpcError('thread/read: thread not loaded: fixture-task')
        with self.assertRaises(RpcError):
            read_thread_metadata(client, 'fixture-task')
        self.assertEqual(client.call.call_count, 3)
        for message in ['permission denied', 'thread/read: thread not loaded: another-task']:
            client = Mock()
            client.call.side_effect = RpcError(message)
            with self.assertRaises(RpcError):
                read_thread_metadata(client, 'fixture-task')
            self.assertEqual(client.call.call_count, 1)

    def test_raw_cursor_requires_selected_raw_read(self):
        with self.assertRaises(ValueError):
            read_trace(self.client(), 'fixture-task', raw_cursor='raw-v1:fixture-task:0')

    def test_discovery_rejects_unselected_rollout_scan(self):
        client = ReadOnlyAppServer.__new__(ReadOnlyAppServer)
        with self.assertRaises(ValueError):
            client.call('thread/list', {'limit': 20})


if __name__ == '__main__':
    unittest.main()
