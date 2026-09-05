# Evidence-first agent skills

Turn engineering claims into reproducible evidence with four focused Codex skills.
Survey an architecture, verify a behavior, review a CLI contract, or test whether a
fresh agent can run and recover a project. The workflows grew from building BidKing
and its mathematical companion, [`bidking-inference`](https://github.com/SeasonCake/bidking-inference),
and include synthetic examples you can run and adapt.

| Skill | Purpose |
| --- | --- |
| `architecture-survey` | Identify evidence-backed structural improvements and their affected consumers. |
| `verify-claim` | Verify one falsifiable behavior with matched baseline/treatment evidence. |
| `cli-contract-review` | Review non-interactive, fail-fast, idempotent CLI and receipt contracts. |
| `agent-compatibility` | Test whether a fresh agent can orient, run, verify, and recover from tracked repository truth. |

Invoke each skill explicitly by name; installation and usage are below.

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

## Hotfix1 engineering case study

Learn how incomplete exports, unsupported queries, and maturity receipts can lead to
overstated conclusions: [English](docs/HOTFIX1_CLAIM_REVIEW.md) ·
[简体中文](docs/HOTFIX1_CLAIM_REVIEW.zh-CN.md).
Eight executable receipt cases show how to turn an ambiguous observation into a precise,
testable conclusion. Pair them with the companion toolkit's versioned-evidence example.

```powershell
python examples/claim_receipts.py
python -m unittest discover -s tests -p test_claim_receipts.py -v
```

## Project maintenance

See `CONTRIBUTING.md`, `MAINTAINING.md`, `SUPPORT.md`, `SECURITY.md`, and `CHANGELOG.md`.
Issue and pull-request templates help you provide a small reproducible example.

Upstream inspirations and adaptations are documented in `UPSTREAM.md` and in each skill's
`ATTRIBUTION.md`.

Copyright (c) 2026 SeasonCake. Released under the MIT License. Contributions use the
Developer Certificate of Origin 1.1 (`git commit -s`); no CLA is required.

See [project origin](PROJECT_ORIGIN.md) for the relationship and scope. If a workflow
helps your project, a Star, reproducible Issue, or improvement PR is welcome.
