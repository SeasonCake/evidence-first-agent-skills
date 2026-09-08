from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from examples.claim_receipts import LINE_SEPARATORS, classify  # noqa: E402


class ClaimReceiptTest(unittest.TestCase):
    def test_local_examples_win_over_an_unrelated_installed_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            shadow = Path(directory)
            package = shadow / "examples"
            package.mkdir()
            (package / "__init__.py").write_text(
                "raise RuntimeError('unrelated examples package was imported')\n",
                encoding="utf-8",
            )
            script = (
                "import sys; sys.path[:0] = " + repr([str(ROOT), str(shadow)])
                + "; import examples.claim_receipts as target; print(target.__file__)"
            )
            completed = subprocess.run(
                [sys.executable, "-c", script], cwd=ROOT, capture_output=True,
                text=True, timeout=10,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(Path(completed.stdout.strip()).resolve(),
                             (ROOT / "examples" / "claim_receipts.py").resolve())

    def receipt(self, **changes) -> dict[str, object]:
        result = {"kind": "search", "scope": "fixture-alpha", "query": "step-five",
                  "status": "complete", "complete": True, "matches": 0}
        return {**result, **changes}

    def test_synthetic_matrix_exact_results(self) -> None:
        document = json.loads((ROOT / "examples" / "claim_receipts.json").read_text(encoding="utf-8"))
        self.assertIs(document["synthetic"], True)
        self.assertEqual(len(document["cases"]), 8)
        self.assertEqual(len({case["id"] for case in document["cases"]}), 8)
        for case in document["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(classify(case["receipt"]), case["expected"])

    def test_complete_positive_and_negative_do_not_claim_global_truth(self) -> None:
        positive = classify(self.receipt(matches=1))
        negative = classify(self.receipt())
        self.assertEqual(positive["verdict"], "observed_in_selected_scope")
        self.assertFalse(positive["absence_supported"])
        self.assertTrue(negative["absence_supported"])
        self.assertFalse(negative["proves_event_never_happened"])

    def test_incomplete_and_error_cases_cannot_prove_absence(self) -> None:
        for status in ("partial", "timeout", "refused", "error"):
            with self.subTest(status=status):
                self.assertFalse(classify(self.receipt(status=status, complete=False))["absence_supported"])

    def test_every_line_separator_is_rejected_as_a_negative(self) -> None:
        for separator in LINE_SEPARATORS:
            with self.subTest(separator=repr(separator)):
                result = classify(self.receipt(query="first" + separator + "next"))
                self.assertEqual(result["verdict"], "unsupported_query")
                self.assertFalse(result["absence_supported"])

    def test_invalid_receipts_are_not_silent_negatives(self) -> None:
        for changes in ({"matches": True}, {"matches": -1}, {"matches": 0.0},
                        {"scope": ""}, {"status": "partial"}, {"complete": "true"},
                        {"status": "refused", "complete": False, "matches": 1},
                        {"unknown_field": "unexpected"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                classify(self.receipt(**changes))

    def test_every_gate_maturity_is_separate_from_release(self) -> None:
        for maturity in ("schema_only", "implemented", "measured"):
            result = classify({"kind": "maturity", "gate": "toy-check", "maturity": maturity})
            self.assertEqual(result["ready"], maturity == "measured")
            self.assertFalse(result["release_assessed"])
        with self.assertRaises(ValueError):
            classify({"kind": "maturity", "gate": "toy-check", "maturity": "approved"})

    def test_cli_replays_only_the_committed_synthetic_fixture(self) -> None:
        completed = subprocess.run([sys.executable, "examples/claim_receipts.py"], cwd=ROOT,
                                   check=True, capture_output=True, timeout=10)
        result = json.loads(completed.stdout)
        self.assertIs(result["synthetic"], True)
        self.assertEqual(len(result["cases"]), 8)


if __name__ == "__main__":
    unittest.main()
