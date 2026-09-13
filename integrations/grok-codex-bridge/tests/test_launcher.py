import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class LauncherTests(unittest.TestCase):
    def test_explicit_adapter_root_controls_settings_lookup(self):
        root = Path(__file__).resolve().parents[1]
        script = root/'desktop.py' if (root/'desktop.py').is_file() else root/'scripts/desktop.py'
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory);adapter = fixture/'adapter';source = fixture/'source'
            adapter.mkdir();(source/'grok_codex_bridge').mkdir(parents=True)
            (source/'grok_codex_bridge/__init__.py').write_text('', encoding='utf-8')
            (source/'grok_codex_bridge/cli.py').write_text(
                'import json,sys\ndef run_cli(): print(json.dumps(sys.argv[1:]))\n', encoding='utf-8')
            (adapter/'desktop-settings.json').write_text(json.dumps({'source_root':str(source)}), encoding='utf-8')
            env = dict(os.environ, GROK_BRIDGE_ADAPTER_ROOT=str(fixture/'wrong-default'))
            run = subprocess.run([sys.executable,str(script),'--adapter-root',str(adapter),'list'],
                env=env,cwd=fixture,capture_output=True,text=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout), ['--adapter-root',str(adapter),'list'])

    def test_custom_codex_home_is_default_adapter_location(self):
        root = Path(__file__).resolve().parents[1]
        script = root/'desktop.py' if (root/'desktop.py').is_file() else root/'scripts/desktop.py'
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory);adapter=home/'grok-adapter';source=home/'source'
            adapter.mkdir();(source/'grok_codex_bridge').mkdir(parents=True)
            (source/'grok_codex_bridge/__init__.py').write_text('',encoding='utf-8')
            (source/'grok_codex_bridge/cli.py').write_text('def run_cli(): print("CUSTOM_HOME_OK")\n',encoding='utf-8')
            (adapter/'desktop-settings.json').write_text(json.dumps({'source_root':str(source)}),encoding='utf-8')
            env=dict(os.environ);env.pop('GROK_BRIDGE_ADAPTER_ROOT',None)
            run=subprocess.run([sys.executable,str(script),'--codex-home',str(home),'list'],
                env=env,cwd=home,capture_output=True,text=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stdout.strip(),'CUSTOM_HOME_OK')
