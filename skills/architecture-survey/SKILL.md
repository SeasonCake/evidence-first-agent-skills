---
name: architecture-survey
description: Produce a bounded, read-only, evidence-backed architecture survey for a named subsystem before a planned major change. Do not use it as a refactor task or release gate.
---

# Architecture Survey

Find a small number of structural opportunities that would make future changes easier
without turning the survey into implementation.

## Boundaries

- Treat the target repository as read-only. Do not edit source, tests, decisions, ADRs,
  plans, records, or Git state.
- Do not run builds, packaging, deployment, destructive commands, or external actions.
- Prefer a named subsystem. If none is supplied, use a bounded recent-churn window to
  select one narrow area; never perform an unbounded repository scan.
- Large files, high churn, and dependency counts are discovery leads, not findings.

## Method

1. Freeze repository identity, scope, exclusions, and current project stage.
2. Inspect at most 30 days or 30 commits and 50 related paths unless evidence justifies a
   smaller explicit expansion.
3. Trace candidates through callers, state/data flow, tests, and user-visible consumers.
4. Apply the deletion test: a useful boundary concentrates complexity behind a smaller
   interface; deleting a shallow wrapper should not leave the same complexity scattered.
5. Check current decisions and rejected alternatives. Historical incidents are leads,
   not current-source truth.
6. Prove repeated consumer friction or a real seam before recommending work. An identity
   or dependency update with no semantic delta should end as `no action`.

## Output

Return at most five candidates labeled `Strong`, `Worth exploring`, or `Speculative`.
For each, include files, observed friction, current seam, proposed deepening, expected
leverage, tests that become simpler, migration risk, confidence, and relation to existing
decisions. End with one recommendation or `no action recommended`, plus the heavy and
external stages not run. Implementation requires a separate authorized task.
