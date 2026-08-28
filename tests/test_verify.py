from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VerifyTest(unittest.TestCase):
    def test_repository_verifier_passes(self) -> None:
        subprocess.run([sys.executable, "scripts/verify.py"], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
