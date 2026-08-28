#!/usr/bin/env python3
"""Validate skill structure and public-candidate boundaries without dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("architecture-survey", "verify-claim", "cli-contract-review", "agent-compatibility")
BANNED = (
    "bidking-",
    "c:\\users\\",
    "c:\\tmp\\",
    "hero_ref",
    "activation_core",
    "release_zip_contract",
)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated YAML frontmatter")
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    return values


def validate_skill(name: str) -> list[str]:
    errors: list[str] = []
    root = ROOT / "skills" / name
    skill = root / "SKILL.md"
    agent = root / "agents" / "openai.yaml"
    attribution = root / "ATTRIBUTION.md"
    for required in (skill, agent, attribution):
        if not required.is_file():
            errors.append(f"missing {required.relative_to(ROOT)}")
    if errors:
        return errors
    text = skill.read_text(encoding="utf-8")
    metadata = parse_frontmatter(text)
    if metadata.get("name") != name:
        errors.append(f"frontmatter name mismatch for {name}")
    if not metadata.get("description"):
        errors.append(f"description missing for {name}")
    yaml = agent.read_text(encoding="utf-8")
    if "allow_implicit_invocation: false" not in yaml:
        errors.append(f"{name} is not explicit-only")
    if f"${name}" not in yaml:
        errors.append(f"default prompt does not name ${name}")
    combined = "\n".join((text, yaml, attribution.read_text(encoding="utf-8"))).casefold()
    for fragment in BANNED:
        if fragment.casefold() in combined:
            errors.append(f"private fragment {fragment!r} in {name}")
    if len(text.splitlines()) > 500:
        errors.append(f"{name} exceeds 500 lines")
    return errors


def main() -> int:
    errors: list[str] = []
    observed = tuple(sorted(path.name for path in (ROOT / "skills").iterdir() if path.is_dir()))
    if observed != tuple(sorted(SKILLS)):
        errors.append(f"unexpected skill set: {observed}")
    for name in SKILLS:
        errors.extend(validate_skill(name))
    upstream = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
    if "bdf7aa355337897f167153e05069aca505dae17c" not in upstream:
        errors.append("Cursor upstream commit is not pinned")
    if not re.search(r"(?i)recorded license: MIT", upstream):
        errors.append("upstream license evidence is missing")
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({"result": "PASS", "skills": len(SKILLS), "errors": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
