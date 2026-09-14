"""Exercise the actual Windows bootstrap against a synthetic, non-model child."""

import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPILER = Path(os.environ.get("WINDIR", "C:/Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"


@unittest.skipUnless(os.name == "nt" and COMPILER.is_file(), "Windows .NET Framework compiler required")
class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="grok-bootstrap-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.folder = Path(cls.temporary.name) / "synthetic source with spaces"
        cls.folder.mkdir()
        cls.executable = cls.folder / "bootstrap.exe"
        completed = subprocess.run(
            [str(COMPILER), "/nologo", "/target:exe", "/out:" + str(cls.executable),
             "/reference:System.Web.Extensions.dll", str(ROOT / "scripts/model_router_bootstrap.cs")],
            capture_output=True, timeout=30,
        )
        if completed.returncode:
            raise RuntimeError(completed.stdout.decode(errors="replace") + completed.stderr.decode(errors="replace"))
        cls.fixture = cls.folder / "fixture router.py"
        cls.fixture.write_text(
            "import base64,json,sys\n"
            "data=sys.stdin.buffer.read()\n"
            "sys.stdout.buffer.write(json.dumps({'args':sys.argv[1:],'input':base64.b64encode(data).decode()},ensure_ascii=False).encode('utf-8'))\n"
            "sys.stderr.buffer.write(b'synthetic-stderr\\x00\\xff')\n"
            "sys.exit(23 if '--fixture-exit' in sys.argv else 0)\n",
            encoding="utf-8",
        )
        cls.settings = cls.folder / "synthetic settings.json"
        cls.settings.write_text("{}", encoding="utf-8")

    def setUp(self):
        self.bootstrap = {
            "python_executable": sys.executable,
            "router_entry": str(self.fixture),
            "router_settings": str(self.settings),
        }
        self.write_bootstrap()

    def write_bootstrap(self):
        (self.folder / "bootstrap.json").write_text(json.dumps(self.bootstrap), encoding="utf-8")

    def run_bootstrap(self, arguments, payload=b""):
        return subprocess.run(
            [str(self.executable), *arguments], input=payload, capture_output=True,
            timeout=20, creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def test_quotes_unicode_trailing_slashes_and_raw_stdio_survive(self):
        arguments = ["", "with spaces", 'quote"inside', "trailing\\", "two\\\\", "中文目录\\", "line\nbreak"]
        payload = b"synthetic-stdin\x00\xff\r\n"
        result = self.run_bootstrap(arguments, payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(data["args"], ["--settings", str(self.settings), "--", *arguments])
        self.assertEqual(base64.b64decode(data["input"]), payload)
        self.assertEqual(result.stderr, b"synthetic-stderr\x00\xff")

    def test_child_failure_exit_code_is_retained(self):
        result = self.run_bootstrap(["--fixture-exit"])
        self.assertEqual(result.returncode, 23)
        self.assertIn("--fixture-exit", json.loads(result.stdout)["args"])

    def test_missing_child_is_reported_without_execution(self):
        self.bootstrap["router_entry"] = str(self.folder / "missing.py")
        self.write_bootstrap()
        result = self.run_bootstrap([])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"router_entry", result.stderr)


if __name__ == "__main__":
    unittest.main()
