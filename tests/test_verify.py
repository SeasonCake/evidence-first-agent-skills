from __future__ import annotations

import importlib.util
import json
import hashlib
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("skill_verifier", ROOT / "scripts" / "verify.py")
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class VerifyTest(unittest.TestCase):
    def test_integration_manifest_and_private_content_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);sample = root/'example.py';sample.write_text('print("synthetic")\n',encoding='utf-8')
            def manifest():
                (root/'SOURCE_MANIFEST.json').write_text(json.dumps({'schema_version':1,
                    'files':{'example.py':hashlib.sha256(sample.read_bytes()).hexdigest()}}),encoding='utf-8')
            manifest();self.assertEqual(VERIFIER.integration_errors(root),[])
            sample.write_text('changed\n',encoding='utf-8')
            self.assertIn('Integration source manifest differs from actual maintained files',VERIFIER.integration_errors(root))
            sample.write_text(VERIFIER.BANNED[0],encoding='utf-8');manifest()
            self.assertTrue(any('Private fragment' in e for e in VERIFIER.integration_errors(root)))

    def test_repository_verifier_passes(self) -> None:
        subprocess.run([sys.executable, "scripts/verify.py"], cwd=ROOT, check=True)

    def test_csharp_review_is_limited_to_the_bootstrap_source(self) -> None:
        for relative, accepted in (("scripts/model_router_bootstrap.cs", True),
                                   ("scripts/unreviewed.cs", False)):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / relative
                source.parent.mkdir()
                source.write_text("// synthetic source fixture\n", encoding="utf-8")
                (root / "SOURCE_MANIFEST.json").write_text(json.dumps({
                    "schema_version": 1,
                    "files": {relative: hashlib.sha256(source.read_bytes()).hexdigest()},
                }), encoding="utf-8")
                errors = VERIFIER.integration_errors(root)
                if accepted:
                    self.assertEqual(errors, [])
                else:
                    self.assertEqual(errors, ["Unreviewed integration file type: " + relative])

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

    def test_declared_invocation_modes_are_distinct(self) -> None:
        self.assertTrue(VERIFIER.INVOCATION_POLICIES["intent-checkpoint"])
        self.assertTrue(VERIFIER.INVOCATION_POLICIES["browser-workflow"])
        for name in (
            "architecture-survey", "verify-claim", "cli-contract-review",
            "agent-compatibility",
        ):
            with self.subTest(skill=name):
                self.assertFalse(VERIFIER.INVOCATION_POLICIES[name])
                self.assertEqual(VERIFIER.validate_skill(name), [])
        self.assertEqual(VERIFIER.validate_skill("intent-checkpoint"), [])
        self.assertEqual(VERIFIER.validate_skill("browser-workflow"), [])

    def test_scalar_policy_reads_actual_boolean(self) -> None:
        for value, expected in (("true", True), ("false", False)):
            with self.subTest(value=value):
                document = (
                    'interface:\n  display_name: "Example"\n'
                    f"policy:\n  allow_implicit_invocation: {value}\n"
                )
                self.assertIs(VERIFIER.parse_invocation_policy(document), expected)

    def test_comment_or_other_section_is_not_policy(self) -> None:
        for document in (
            "# policy:\n#   allow_implicit_invocation: false\n",
            "interface:\n  allow_implicit_invocation: false\n",
            'policy:\n  note: "allow_implicit_invocation: false"\n',
        ):
            with self.subTest(document=document):
                self.assertIsNone(VERIFIER.parse_invocation_policy(document))

    def test_duplicate_or_invalid_policy_is_rejected(self) -> None:
        for document in (
            "policy:\n  allow_implicit_invocation: true\n  allow_implicit_invocation: false\n",
            "policy:\n  allow_implicit_invocation: true\npolicy:\n  allow_implicit_invocation: false\n",
            'policy:\n  allow_implicit_invocation: "false"\n',
            "policy:\n  nested:\n    allow_implicit_invocation: false\n",
        ):
            with self.subTest(document=document):
                self.assertIsNone(VERIFIER.parse_invocation_policy(document))

    def test_real_skill_policy_mismatch_is_reported(self) -> None:
        original_read = Path.read_text
        for name, wrong in (
            ("intent-checkpoint", "false"),
            ("browser-workflow", "false"),
            ("verify-claim", "true"),
        ):
            target = ROOT / "skills" / name / "agents" / "openai.yaml"

            def substitute(path: Path, *args, **kwargs) -> str:
                if path == target:
                    return (
                        f'interface:\n  default_prompt: "Use ${name}"\n'
                        f"policy:\n  allow_implicit_invocation: {wrong}\n"
                    )
                return original_read(path, *args, **kwargs)

            with self.subTest(skill=name), patch.object(Path, "read_text", substitute):
                errors = VERIFIER.validate_skill(name)
                self.assertEqual(len(errors), 1)
                self.assertIn("invocation policy", errors[0])

    def test_conditional_reference_private_fragment_is_reported(self) -> None:
        original_read = Path.read_text
        target = ROOT / "skills" / "browser-workflow" / "references" / "cli.md"

        def substitute(path: Path, *args, **kwargs) -> str:
            if path == target:
                return "Synthetic negative control: " + VERIFIER.BANNED[0]
            return original_read(path, *args, **kwargs)

        self.assertEqual(VERIFIER.validate_skill("browser-workflow"), [])
        with patch.object(Path, "read_text", substitute):
            errors = VERIFIER.validate_skill("browser-workflow")
        self.assertEqual(len(errors), 1)
        self.assertIn("private fragment", errors[0])


if __name__ == "__main__":
    unittest.main()
