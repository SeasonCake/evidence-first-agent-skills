"""Refresh the small public source inventory; does not run/configure/publish the bridge."""

import hashlib
import json
from pathlib import Path
from verify import integration_files

ROOT = Path(__file__).resolve().parents[1] / "integrations/grok-codex-bridge"
payload = {
    "schema_version": 1,
    "origin": "SeasonCake local integration research, public desktop subset",
    "files": {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in integration_files(ROOT)
    },
}
(ROOT / "SOURCE_MANIFEST.json").write_text(
    json.dumps(payload, indent=2) + "\n", encoding="utf-8"
)
print(
    json.dumps(
        {"files": len(payload["files"]), "model_calls": 0, "publication_actions": 0}
    )
)
