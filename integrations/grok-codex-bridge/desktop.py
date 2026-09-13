"""Installed launcher: resolve the selected local source, without changing its cwd."""
import json
import argparse
import os
from pathlib import Path
import sys


def main():
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument('--adapter-root')
    options.add_argument('--codex-home', default=os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    chosen, _ = options.parse_known_args()
    adapter = Path(chosen.adapter_root or os.environ.get('GROK_BRIDGE_ADAPTER_ROOT') or
                   str(Path(chosen.codex_home) / 'grok-adapter'))
    settings = json.loads((adapter / 'desktop-settings.json').read_text(encoding='utf-8'))
    source = Path(settings['source_root'])
    if not source.is_absolute() or not (source / 'grok_codex_bridge/cli.py').is_file():
        raise ValueError('The installed desktop bridge source path is unavailable; do not substitute another task/model')
    sys.path.insert(0, str(source))
    if chosen.adapter_root is None:
        sys.argv[1:1] = ['--adapter-root', str(adapter)]
    from grok_codex_bridge.cli import run_cli as run
    run()


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
