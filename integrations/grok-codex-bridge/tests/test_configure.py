import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bridge_configure", ROOT / "configure.py")
configure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure)


class ConfigureTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.adapter = self.home / "grok-adapter"
        self.config = 'model="native-model"\nmodel_context_window=800000\n[features]\ncustom=true\n'
        (self.home / "config.toml").write_text(self.config, encoding="utf-8")
        (self.home / "models_cache.json").write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "slug": "native-model",
                            "context_window": 800000,
                            "tools": ["keep"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.routed = self.root / "routed.json"
        self.routed.write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "slug": "xai/grok-test",
                            "context_window": 500000,
                            "auto_compact_token_limit": 450000,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def plan(self):
        return configure.plan(
            self.home,
            self.adapter,
            Path(sys.executable),
            self.routed,
            "xai/grok-test",
            "high",
            "http://127.0.0.1:10100/v1",
        )

    def test_dry_run_no_writes_and_apply_preserves_native_settings(self):
        writes = self.plan()
        self.assertFalse(self.adapter.exists())
        result = configure.apply_plan(writes, self.adapter)
        self.assertEqual(result["model_calls"], 0)
        native = tomllib.loads((self.home / "config.toml").read_text("utf-8"))
        self.assertEqual(native["model"], "native-model")
        self.assertEqual(native["model_context_window"], 800000)
        self.assertEqual(native["features"], {"custom": True})
        catalog = json.loads(
            (self.adapter / "runtime/native-plus-grok-catalog.json").read_text("utf-8")
        )
        self.assertEqual(catalog["models"][0]["tools"], ["keep"])
        self.assertEqual(
            configure.apply_plan(self.plan(), self.adapter)["changed_paths"], []
        )

    def test_existing_catalog_or_provider_conflict_does_not_mutate(self):
        for extra in [
            'model_catalog_json="other.json"\n',
            '[model_providers.ocx-grok]\nbase_url="http://127.0.0.1:9999/v1"\n',
        ]:
            path = self.home / "config.toml"
            path.write_text(extra + self.config, encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                self.plan()
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(self.adapter.exists())

    def test_existing_foreign_bridge_file_is_preserved(self):
        self.adapter.mkdir()
        p = self.adapter / "settings.json"
        p.write_text('{"other":"installation"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            self.plan()
        self.assertEqual(p.read_text("utf-8"), '{"other":"installation"}')

    def test_nonlocal_or_credential_url_is_rejected(self):
        for url in [
            "https://example.com/v1",
            "http://user:password@localhost/v1",
            "http://127.0.0.1/v1?key=example",
        ]:
            with self.assertRaises(ValueError):
                configure.plan(
                    self.home,
                    self.adapter,
                    Path(sys.executable),
                    self.routed,
                    "xai/grok-test",
                    "high",
                    url,
                )

    def test_concurrent_config_edit_is_not_overwritten(self):
        writes = self.plan()
        path = self.home / "config.toml"
        path.write_text(self.config + "\n# another editor\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            configure.apply_plan(writes, self.adapter)
        self.assertIn("another editor", path.read_text("utf-8"))
        self.assertFalse(self.adapter.exists())
