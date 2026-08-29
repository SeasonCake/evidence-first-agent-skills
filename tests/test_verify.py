from __future__ import annotations

import subprocess
import sys
import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VerifyTest(unittest.TestCase):
    def test_repository_verifier_passes(self) -> None:
        subprocess.run([sys.executable, "scripts/verify.py"], cwd=ROOT, check=True)

    def test_synthetic_case_matrix_covers_every_skill(self) -> None:
        document = json.loads(
            (ROOT / "examples" / "synthetic_cases.json").read_text(encoding="utf-8")
        )
        expected = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
        self.assertTrue(document["synthetic"])
        self.assertEqual(set(document["cases"]), expected)

    def test_each_skill_links_a_tracked_synthetic_example(self) -> None:
        for skill_root in (ROOT / "skills").iterdir():
            if not skill_root.is_dir():
                continue
            text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("references/synthetic-example.md", text)
            self.assertTrue((skill_root / "references" / "synthetic-example.md").is_file())


if __name__ == "__main__":
    unittest.main()
