---
name: cli-contract-review
description: Review a build, test, packaging, deployment, or maintenance CLI for reliable agent execution. Use for non-interactive, dry-run, receipt, recovery, and compatibility contracts; not to execute the external operation.
---

# CLI Contract Review

Review the command surface, not the product implementation.

## Criteria

- Inputs are non-interactive; missing values fail quickly with a copyable example and no
  partial side effect.
- Help is layered and reports shell/interpreter, source identity, input fingerprints,
  environment assumptions, output paths, and stage authority.
- Preflight is side-effect free. Destructive or external actions have an exact preview,
  dry-run, bounded confirmation, safe retry, and rollback path.
- Repeating success is idempotent or reports `already complete`.
- Exit codes and machine receipts separate pass, product failure, setup/input failure,
  timeout, partial result, and not-run.
- A yielded command handle remains running. Recovery continues that handle; only the
  defined terminal receipt establishes completion/timeout. Requesting stop does not prove
  the owned process/thread was reaped, and its business error is separate from successful cleanup.
- Paths are literal and containment-checked; temporary output has an owner, lifecycle,
  cleanup disposition, and recovery source.
- Supported shells and missing/asymmetric TEMP/TMP combinations are explicit.
- Process/service state uses exact structured identity. Blank rows, stale handles, or
  missing fields are `unknown`; absence is rechecked before replacement.
- Health deadlines use measured production-scale startup and distinguish loading,
  not-ready, and failed; rollback has independent time.
- Focused or changed-module modes cannot masquerade as full gates.
- Read/search budgets limit actual entries, depth, bytes, elapsed time, and owned
  processes, not just displayed output. Cancellation reaps the owned job; partial
  coverage is not absence. Non-interactive flags do not supply missing user intent
  or replace required host permissions.

## Output

Inspect entrypoint, callers, help, tests, and one successful and one negative path. Return
at most six prioritized gaps with evidence, operational impact, smallest change,
verification, and stage risk. End each gap with `adopt as SOP`, `implement in CLI`, or
`no change`. Do not execute a release or external operation unless separately authorized.
If the user selected a concrete reversible endpoint, flag needless re-authorization
between its normal local steps while preserving unselected external or destructive stages.

For a setup-failure versus product-failure contract, read
[the synthetic example](references/synthetic-example.md).
