"""Entry point used by the local Windows stdio bootstrap."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grok_codex_bridge.model_router import main

if __name__ == '__main__':
    raise SystemExit(main())
