# Evidence-first agent skills

Four small, explicit Codex skills distilled from engineering experience building and
maintaining the private BidKing calculator and its public mathematical companion,
[`bidking-inference`](https://github.com/SeasonCake/bidking-inference). The reusable
lessons cover evidence levels, release continuity, CLI contracts, UI verification,
handoff recovery, and fresh-clone truth. No private source, customer data, raw incident
record, credential, or production topology is included; see `PROJECT_ORIGIN.md`.

| Skill | Purpose |
| --- | --- |
| `architecture-survey` | Find a few evidence-backed structural opportunities without starting a refactor. |
| `verify-claim` | Verify one falsifiable behavior with matched baseline/treatment evidence. |
| `cli-contract-review` | Review non-interactive, fail-fast, idempotent CLI and receipt contracts. |
| `agent-compatibility` | Test whether a fresh agent can orient, run, verify, and recover from tracked repository truth. |

All four are explicit-only. They do not grant permission to edit, publish, deploy, or
delete anything, and their reports are not substitutes for product-specific formal gates.

## Verify

```powershell
python scripts/verify.py
```

## Install and invoke

See `INSTALL.md` for a copy-only installation into a personal Codex skills directory.
Every skill remains explicit-only and is invoked by name, for example:

```text
Use $verify-claim to verify that this CLI behaves identically after a clean install.
```

Each skill links one synthetic known-good/known-fail example. The machine-readable case
matrix is `examples/synthetic_cases.json`.

## Project maintenance

See `CONTRIBUTING.md`, `MAINTAINING.md`, `SUPPORT.md`, `SECURITY.md`, and `CHANGELOG.md`.
Public issue and pull-request templates reject private incident material and require
reproducible synthetic evidence.

Upstream inspirations and adaptations are documented in `UPSTREAM.md` and in each skill's
`ATTRIBUTION.md`.

Copyright (c) 2026 SeasonCake. Released under the MIT License. Contributions use the
Developer Certificate of Origin 1.1 (`git commit -s`); no CLA is required.
