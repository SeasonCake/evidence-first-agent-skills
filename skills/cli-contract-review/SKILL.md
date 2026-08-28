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
- Paths are literal and containment-checked; temporary output has an owner, lifecycle,
  cleanup disposition, and recovery source.
- Supported shells and missing/asymmetric TEMP/TMP combinations are explicit.
- Process/service state uses exact structured identity. Blank rows, stale handles, or
  missing fields are `unknown`; absence is rechecked before replacement.
- Health deadlines use measured production-scale startup and distinguish loading,
  not-ready, and failed; rollback has independent time.
- Focused or changed-module modes cannot masquerade as full gates.

## Output

Inspect entrypoint, callers, help, tests, and one successful and one negative path. Return
at most six prioritized gaps with evidence, operational impact, smallest change,
verification, and stage risk. End each gap with `adopt as SOP`, `implement in CLI`, or
`no change`. Do not execute a release or external operation unless separately authorized.
