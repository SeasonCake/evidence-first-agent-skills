# Evidence-first agent skills (public candidate)

Four small, explicit Codex skills distilled from real release, UI, CLI, and handoff
failures:

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

Upstream inspirations and adaptations are documented in `UPSTREAM.md` and in each skill's
`ATTRIBUTION.md`. The final repository license remains an author decision.
