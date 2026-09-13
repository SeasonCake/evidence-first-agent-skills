#!/usr/bin/env python3
"""Validate skill structure and public-candidate boundaries without dependencies."""

from __future__ import annotations

import json
import hashlib
import re
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVOCATION_POLICIES = {
    "architecture-survey": False,
    "verify-claim": False,
    "cli-contract-review": False,
    "agent-compatibility": False,
    "intent-checkpoint": True,
    "browser-workflow": True,
    "grok-bridge": True,
}
SKILLS = tuple(INVOCATION_POLICIES)
REQUIRED_PUBLIC_FILES = (
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "DCO",
    "INSTALL.md",
    "LICENSE",
    "MAINTAINING.md",
    "SECURITY.md",
    "SUPPORT.md",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/skill_proposal.yml",
    "examples/synthetic_cases.json",
)
BANNED = (
    "bidking_lab",
    "c:\\users\\",
    "c:/users/",
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


def parse_invocation_policy(text: str) -> bool | None:
    """Read this repository's scalar policy declaration, not arbitrary YAML."""
    headers = list(re.finditer(r"(?m)^policy:[ \t]*(?:#[^\n]*)?$", text))
    if len(headers) != 1:
        return None
    values: list[bool] = []
    for line in text[headers[0].end() :].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            break
        match = re.fullmatch(
            r"  allow_implicit_invocation: *(true|false) *(?:#.*)?", line
        )
        if match:
            values.append(match.group(1) == "true")
        elif re.match(r"[ \t]+allow_implicit_invocation\b", line):
            return None
    return values[0] if len(values) == 1 else None


def validate_skill(name: str) -> list[str]:
    errors: list[str] = []
    root = ROOT / "skills" / name
    skill = root / "SKILL.md"
    agent = root / "agents" / "openai.yaml"
    attribution = root / "ATTRIBUTION.md"
    example = root / "references" / "synthetic-example.md"
    for required in (skill, agent, attribution, example):
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
    if "references/synthetic-example.md" not in text:
        errors.append(f"synthetic example is not linked for {name}")
    yaml = agent.read_text(encoding="utf-8")
    expected_policy = INVOCATION_POLICIES[name]
    if parse_invocation_policy(yaml) is not expected_policy:
        errors.append(
            f"{name} invocation policy must be explicitly {str(expected_policy).lower()}"
        )
    if f"${name}" not in yaml:
        errors.append(f"default prompt does not name ${name}")
    attribution_text = attribution.read_text(encoding="utf-8")
    if "Project origin:" not in attribution_text:
        errors.append(f"project origin missing for {name}")
    if "bidking-inference" not in attribution_text:
        errors.append(f"public companion link missing for {name}")
    reference_texts = [
        path.read_text(encoding="utf-8")
        for path in sorted((root / "references").glob("*.md"))
    ]
    script_texts = [path.read_text(encoding="utf-8") for path in sorted((root / "scripts").glob("*"))
                    if path.is_file() and path.suffix in {".py", ".js", ".ts"}]
    combined = "\n".join((text, yaml, attribution_text, *reference_texts, *script_texts)).casefold()
    for fragment in BANNED:
        if fragment.casefold() in combined:
            errors.append(f"private fragment {fragment!r} in {name}")
    if len(text.splitlines()) > 500:
        errors.append(f"{name} exceeds 500 lines")
    return errors


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED_PUBLIC_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"required public-maintenance file is missing: {relative}")
    if not (ROOT / "LICENSE").is_file():
        errors.append("final LICENSE is missing")
    if (ROOT / "LICENSE-DECISION.md").exists():
        errors.append("obsolete license decision placeholder is still present")
    origin = (ROOT / "PROJECT_ORIGIN.md").read_text(encoding="utf-8")
    if "bidking-inference" not in origin or "private BidKing" not in origin:
        errors.append("project origin does not identify the BidKing/public companion relationship")
    observed = tuple(sorted(path.name for path in (ROOT / "skills").iterdir() if path.is_dir()))
    if observed != tuple(sorted(SKILLS)):
        errors.append(f"unexpected skill set: {observed}")
    for name in SKILLS:
        errors.extend(validate_skill(name))
    errors.extend(integration_errors(ROOT / "integrations" / "grok-codex-bridge"))
    cases_document = json.loads(
        (ROOT / "examples" / "synthetic_cases.json").read_text(encoding="utf-8")
    )
    if cases_document.get("synthetic") is not True:
        errors.append("case matrix is not explicitly synthetic")
    cases = cases_document.get("cases")
    if not isinstance(cases, dict) or set(cases) != set(SKILLS):
        errors.append("case matrix does not exactly cover the public skill set")
    else:
        for name, case in cases.items():
            if not isinstance(case, dict) or set(case) != {"known_good", "known_fail"}:
                errors.append(f"case matrix shape is invalid for {name}")
            elif not all(isinstance(value, str) and value.strip() for value in case.values()):
                errors.append(f"case matrix text is empty for {name}")
    upstream = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
    if "93b00b89ef425a9c1bac0d0b317dfc49c930ac99" not in upstream:
        errors.append("Cursor upstream commit is not pinned")
    if not re.search(r"(?i)recorded license: MIT", upstream):
        errors.append("upstream license evidence is missing")
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({"result": "PASS", "skills": len(SKILLS), "errors": 0}))
    return 0


def integration_files(root: Path) -> list[Path]:
    """The maintained integration is small; runtime/output trees are not source."""
    files = [];pending = [(root, 0)];entries = 0;total = 0
    while pending:
        directory, depth = pending.pop()
        if depth > 8:raise ValueError('Integration directory depth exceeded')
        if directory.is_symlink() or getattr(directory.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Integration source contains a link/reparse point')
        with os.scandir(directory) as children:
            for child in children:
                entries += 1
                if entries > 500:raise ValueError('Integration directory-entry bound exceeded')
                if child.name == '__pycache__':continue
                path = Path(child.path)
                info = child.stat(follow_symlinks=False)
                if child.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                    raise ValueError('Integration source contains a link/reparse point')
                if child.is_dir(follow_symlinks=False):pending.append((path, depth + 1))
                elif child.is_file(follow_symlinks=False) and path.name != 'SOURCE_MANIFEST.json':
                    total += info.st_size
                    if info.st_size > 4 * 1024 * 1024 or total > 8 * 1024 * 1024 or len(files) >= 300:
                        raise ValueError('Integration source exceeds its review inventory bound')
                    files.append(path)
    return sorted(files)


def integration_errors(root: Path) -> list[str]:
    errors = []
    try:
        manifest = json.loads((root/'SOURCE_MANIFEST.json').read_text('utf-8'))
        if manifest.get('schema_version') != 1 or not isinstance(manifest.get('files'), dict):
            return ['Invalid integration source manifest']
        files = integration_files(root)
    except (OSError, ValueError) as error:
        return [f'Integration inventory error: {error}']
    actual = {}
    allowed = {'.py', '.md', '.json', '.ts', '.js', '.patch', '.toml', '.yml', '.yaml', '.txt'}
    for path in files:
        relative = path.relative_to(root).as_posix()
        if any(part in {'runtime', 'backups', 'sessions', '.local'} for part in Path(relative).parts):
            errors.append(f'Private runtime tree in integration: {relative}')
        raw = path.read_bytes()
        actual[relative] = hashlib.sha256(raw).hexdigest()
        if path.suffix not in allowed and path.name != 'LICENSE.opencodex':
            errors.append(f'Unreviewed integration file type: {relative}')
            continue
        try: text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            errors.append(f'Non-text integration source: {relative}')
            continue
        for fragment in BANNED:
            if fragment.casefold() in text.casefold():
                errors.append(f'Private fragment in integration: {relative}')
    if actual != manifest['files']:
        errors.append('Integration source manifest differs from actual maintained files')
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
