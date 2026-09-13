import copy
import json
from pathlib import Path
import tempfile
import unittest

from grok_codex_bridge.catalog import extend_native_catalog, refresh_catalog, read_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.native = {'models': [{'slug': 'native-one', 'context_window': 800000,
                                  'base_instructions': 'native instruction', 'service_tiers': ['priority']}],
                       'fetched_at': 'native-date', 'opaque': {'future': True}}
        self.grok = {'slug': 'xai/grok-test', 'context_window': 500000,
                     'auto_compact_token_limit': 450000, 'effective_context_window_percent': 95}
        self.routed = {'models': [{'slug': 'native-one', 'context_window': 272000}, self.grok]}

    def test_native_rows_and_top_level_fields_are_preserved(self):
        before = copy.deepcopy((self.native, self.routed))
        merged, receipt = extend_native_catalog(self.native, self.routed, 'xai/grok-test')
        self.assertEqual(merged['models'][:-1], self.native['models'])
        self.assertEqual(merged['opaque'], self.native['opaque'])
        self.assertEqual(merged['fetched_at'], 'native-date')
        self.assertEqual(merged['models'][-1], self.grok)
        self.assertEqual((self.native, self.routed), before)
        self.assertTrue(receipt['native_rows_unchanged'])
        merged['models'][0]['base_instructions'] = 'changed'
        self.assertEqual(self.native['models'][0]['base_instructions'], 'native instruction')

    def test_bad_selection_and_contaminated_native_source_are_rejected(self):
        for selection in ['native-one', 'xai/grok-missing']:
            with self.assertRaises(ValueError):extend_native_catalog(self.native, self.routed, selection)
        for rows in [[], [self.grok], self.native['models'] * 2]:
            with self.assertRaises(ValueError):extend_native_catalog({'models': rows}, self.routed, 'xai/grok-test')

    def test_missing_or_invalid_limits_fail_before_write(self):
        for window, limit in [(None, 450000), (True, 1), (500000, 500000), (500000, 0), (500000, False)]:
            routed = {'models': [dict(self.grok, context_window=window, auto_compact_token_limit=limit)]}
            with self.assertRaises(ValueError):extend_native_catalog(self.native, routed, 'xai/grok-test')

    def test_refresh_is_idempotent_and_never_overwrites_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);native = root/'native.json';routed = root/'routed.json';out = root/'result.json'
            native.write_text(json.dumps(self.native), encoding='utf-8')
            routed.write_text(json.dumps(self.routed), encoding='utf-8')
            originals = native.read_bytes(), routed.read_bytes()
            first = refresh_catalog(native, routed, out, 'xai/grok-test');stamp = out.stat().st_mtime_ns
            second = refresh_catalog(native, routed, out, 'xai/grok-test')
            self.assertTrue(first['changed']);self.assertFalse(second['changed'])
            self.assertEqual(out.stat().st_mtime_ns, stamp)
            self.assertEqual((native.read_bytes(), routed.read_bytes()), originals)
            self.assertEqual(read_catalog(out)['models'][0], self.native['models'][0])
            with self.assertRaises(ValueError):refresh_catalog(native, routed, native, 'xai/grok-test')
