# Evidence-first agent skills

Turn engineering claims, consequential choices, and browser edits into clear next actions with six focused Codex skills.
Survey an architecture, verify a behavior, review a CLI contract, or test whether a
fresh agent can run and recover a project. The workflows grew from building BidKing
and its mathematical companion, [`bidking-inference`](https://github.com/SeasonCake/bidking-inference),
and include synthetic examples you can run and adapt.

| Skill | Purpose | Invocation |
| --- | --- | --- |
| `browser-workflow` | Complete multi-step browser edits with persisted readback and recover without duplicate submissions. | Explicit or context-matched |
| `intent-checkpoint` | Resolve consequential scope choices with a short native question form, without approval loops. | Explicit or context-matched |
| `architecture-survey` | Identify evidence-backed structural improvements and their affected consumers. | Explicit |
| `verify-claim` | Verify one falsifiable behavior with matched baseline/treatment evidence. | Explicit |
| `cli-contract-review` | Review non-interactive, fail-fast, idempotent CLI and receipt contracts. | Explicit |
| `agent-compatibility` | Test whether a fresh agent can orient, run, verify, and recover from tracked repository truth. | Explicit |

Every skill can be invoked by name. `browser-workflow` and `intent-checkpoint` allow
automatic matching; the original four review skills remain explicit-only.

## Verify

```powershell
python scripts/verify.py
```

## Install and invoke

See `INSTALL.md` for a copy-only installation into a personal Codex skills directory.
The original four review skills remain explicit-only, for example:

```text
Use $verify-claim to verify that this CLI behaves identically after a clean install.
```

Each skill links one synthetic known-good/known-fail example. The machine-readable case
matrix is `examples/synthetic_cases.json`.

## Short questions, clear decisions

`intent-checkpoint` helps an agent notice when the next action needs your choice: a scope
expansion, an owner handoff, or an optional protection proposal. It also teaches when
**not** to ask: clear, reversible work should continue.

```text
Use $intent-checkpoint to separate this release fix from the optional signing proposal.
Ask me only about decisions that would change the selected scope.
```

The skill prefers a native question form when the host permits one, including Codex's
`request_user_input_async` when available, and uses a short text question otherwise.
See [the workflow](skills/intent-checkpoint/SKILL.md) and
[twelve synthetic cases](skills/intent-checkpoint/references/synthetic-example.md), including
delayed answers, forwarded scope statements, and local completion within an unfinished goal.
It is an instruction-only skill, not a new form service.

## Browser edits that finish with saved evidence

```text
Use $browser-workflow to update these three descriptions in my selected browser.
Keep prices unchanged and verify the saved results before moving on.
```

The workflow covers draft verification, uncertain save outcomes, stale pages and compact
evidence. It preserves the chosen browser and current provider permissions; CLI use is
conditional, not a forced replacement. See the [workflow](skills/browser-workflow/SKILL.md),
[six synthetic cases](skills/browser-workflow/references/synthetic-example.md), and the
[optional AGENTS routing example](INSTALL.md#optional-standing-route).

Skill discovery, a scenario review and real browser execution are different checks.
This skill does not promise a native focus fix or universal speed improvement.

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

Share useful progress while a release is unfinished with the
[interim-maintenance guide](docs/INTERIM_MAINTENANCE.md): a bounded review, a dated
status packet, synthetic examples of evolving evidence, and explicit publishing boundaries.

See `CONTRIBUTING.md`, `MAINTAINING.md`, `SUPPORT.md`, `SECURITY.md`, and `CHANGELOG.md`.
Issue and pull-request templates help you provide a small reproducible example.

Upstream inspirations and adaptations are documented in `UPSTREAM.md` and in each skill's
`ATTRIBUTION.md`.

Copyright (c) 2026 SeasonCake. Released under the MIT License. Contributions use the
Developer Certificate of Origin 1.1 (`git commit -s`); no CLA is required.

See [project origin](PROJECT_ORIGIN.md) for the relationship and scope. If a workflow
helps your project, a Star, reproducible Issue, or improvement PR is welcome.
