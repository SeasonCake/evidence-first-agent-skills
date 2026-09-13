import json
from pathlib import Path
import tempfile
import unittest

from grok_codex_bridge.raw_tools import read_raw_tools
from grok_codex_bridge.trace import RpcError


class RawToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grok-raw-test-')
        self.path = Path(self.temp.name) / 'synthetic.jsonl'

    def tearDown(self):
        self.temp.cleanup()

    def write(self, entries):
        rows = [{'type': 'session_meta', 'payload': {'id': 'task-id'}}] + entries
        self.path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')

    def event(self, kind, **fields):
        return {'timestamp': 'fixture-time', 'type': 'response_item', 'payload': {'type': kind, **fields}}

    def test_actual_call_output_linkage_and_no_default_content(self):
        self.write([self.event('function_call', name='spawn_agent', call_id='call-1', arguments='{}'),
                    self.event('function_call_output', call_id='call-1', output='Unknown model')])
        page = read_raw_tools(self.path, 'task-id')
        self.assertEqual(page['data'][0]['name'], 'spawn_agent')
        self.assertNotIn('output', page['data'][0])
        self.assertTrue(page['wholeFileCovered'])

    def test_opt_in_output_is_clipped(self):
        self.write([self.event('function_call_output', call_id='call-1', output='字' * 1700)])
        value = read_raw_tools(self.path, 'task-id', include_content=True)['data'][0]['output']
        self.assertEqual(len(value['text']), 1600)
        self.assertTrue(value['truncated'])

    def test_reasoning_and_messages_are_not_raw_tool_output(self):
        self.write([self.event('reasoning', text='private', encrypted_content='opaque'),
                    self.event('message', content='not a tool')])
        self.assertEqual(read_raw_tools(self.path, 'task-id', include_content=True)['data'], [])

    def test_header_identity_mismatch_rejected(self):
        self.write([])
        with self.assertRaises(RpcError):
            read_raw_tools(self.path, 'other-task')

    def test_pagination_without_tool_duplicates(self):
        self.write([self.event('function_call', name='fixture', call_id=f'call-{i}') for i in range(5)])
        first = read_raw_tools(self.path, 'task-id', limit=2)
        second = read_raw_tools(self.path, 'task-id', limit=2, cursor=first['nextCursor'])
        self.assertEqual([e['callId'] for e in first['data']], ['call-4', 'call-3'])
        self.assertEqual([e['callId'] for e in second['data']], ['call-2', 'call-1'])

    def test_large_boundary_line_and_partial_tail_are_explicit(self):
        self.write([self.event('message', content='x' * 9000),
                    self.event('function_call', name='fixture', call_id='call-1')])
        with self.path.open('ab') as handle:
            handle.write(b'{"unfinished":')
        page = read_raw_tools(self.path, 'task-id', window_bytes=4096)
        self.assertTrue(page['partialBoundarySkipped'])
        self.assertTrue(page['incompleteTailSkipped'])
        self.assertFalse(page['wholeFileCovered'])
        self.assertEqual(page['data'][0]['callId'], 'call-1')

    def test_cursor_bound_to_task(self):
        self.write([])
        with self.assertRaises(ValueError):
            read_raw_tools(self.path, 'task-id', cursor='raw-v1:other:0')

    def test_cursor_past_truncated_file_rejected(self):
        self.write([])
        with self.assertRaises(RpcError):
            read_raw_tools(self.path, 'task-id', cursor='raw-v1:task-id:9999999')

    def test_malformed_shape_is_reported_not_claimed_complete(self):
        self.write([self.event('function_call', name='fixture', call_id='call-1'),
                    {'type': 'response_item', 'payload': None}])
        result = read_raw_tools(self.path, 'task-id')
        self.assertEqual(result['malformedLines'], 1)
        self.assertFalse(result['allToolEventsReturned'])


if __name__ == '__main__':
    unittest.main()
