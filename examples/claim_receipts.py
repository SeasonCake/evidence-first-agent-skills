#!/usr/bin/env python3
"""Classify synthetic receipts, not the truth of real-world events."""

from __future__ import annotations

import json
from pathlib import Path

LINE_SEPARATORS = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"


def _text(value: object, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def classify(receipt: dict[str, object]) -> dict[str, object]:
    """State the narrow claim supported by a caller-supplied receipt."""
    if type(receipt) is not dict:
        raise ValueError("receipt must be an exact object")
    kind = receipt.get("kind")
    if kind == "maturity" and set(receipt) == {"kind", "gate", "maturity"}:
        _text(receipt["gate"], "gate")
        if receipt["maturity"] not in ("schema_only", "implemented", "measured"):
            raise ValueError("invalid maturity")
        return {
            "assessment_scope": "explicit_gate_maturity_only",
            "gate": receipt["gate"],
            "ready": receipt["maturity"] == "measured",
            "release_assessed": False,
        }
    if kind != "search" or set(receipt) != {"kind", "scope", "query", "status", "complete", "matches"}:
        raise ValueError("invalid receipt shape")
    _text(receipt["scope"], "scope")
    _text(receipt["query"], "query")
    status = receipt["status"]
    if status not in ("complete", "partial", "timeout", "refused", "error"):
        raise ValueError("invalid search status")
    if type(receipt["complete"]) is not bool or receipt["complete"] != (status == "complete"):
        raise ValueError("status and completeness disagree")
    matches = receipt["matches"]
    if type(matches) is not int or matches < 0:
        raise ValueError("matches must be a non-negative integer")
    if status in ("refused", "error") and matches:
        raise ValueError("failed receipt cannot assert a match count")

    if any(separator in receipt["query"] for separator in LINE_SEPARATORS):
        verdict = "unsupported_query"
    elif status != "complete":
        verdict = "inconclusive"
    elif matches:
        verdict = "observed_in_selected_scope"
    else:
        verdict = "not_observed_in_selected_scope"
    return {"assessment_scope": receipt["scope"], "verdict": verdict,
            "absence_supported": verdict == "not_observed_in_selected_scope",
            "proves_event_never_happened": False}


def main() -> int:
    fixture = Path(__file__).with_name("claim_receipts.json")
    document = json.loads(fixture.read_text(encoding="utf-8"))
    if document.get("synthetic") is not True:
        raise ValueError("this demonstration accepts only the synthetic fixture")
    rows = []
    for case in document["cases"]:
        actual = classify(case["receipt"])
        if actual != case["expected"]:
            raise ValueError(f"fixture expectation mismatch: {case['id']}")
        rows.append({"id": case["id"], "result": actual})
    print(json.dumps({"synthetic": True, "cases": rows}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
