---
name: agent-compatibility
description: Audit a sanitized repository for fresh-agent onboarding, startup, focused verification, execution continuity, recovery, and documentation reliability. Use before opening a public repository or after major tooling changes.
---

# Agent Compatibility

Determine whether a fresh coding agent can understand the repository and safely verify a
small change without hidden private context or an unnecessarily heavy loop.

## Boundaries

- Target a sanitized/public candidate or explicitly approved read-only simulation.
- Do not publish, push, open issues, install dependencies, mutate Git, or run unrelated
  heavy product gates.
- Missing private inputs are expected; judge whether docs provide a safe public substitute.
- This is a compatibility report, not a security certification or release verdict.

## Surfaces

Inspect sequentially unless the user explicitly authorizes parallel work:

1. Inventory: tracked content, ignored residue, and intended export are distinct.
2. Orientation: README, license, contribution path, guidance, architecture, vocabulary,
   and public/private boundary.
3. Startup: one documented, non-interactive fixture path without credentials, GUI clicks,
   or machine-specific paths.
4. Validation: one focused positive/negative check that finishes quickly.
5. Docs reliability: commands, paths, versions, expected output, and failure guidance agree.
6. Continuity: a selected reversible endpoint proceeds without repeated authorization;
   runtime input is not misclassified as authority, while external/destructive stages stop.
7. Recovery: stale jobs recover from durable receipts, process absence uses exact identity,
   staged new files receive checks, and links are validated from the Git index/fresh clone.

Archived chat, screenshots, local caches, and ignored files must not be required for a fresh
agent. When execution is prohibited, statically trace dependencies -> entrypoint -> input
provenance -> expected output without claiming runtime proof.

## Output

Return `READY`, `READY WITH FRICTION`, or `NOT READY`, followed by at most six top fixes.
Each fix includes evidence, affected workflow, smallest improvement, and verification.
List all heavy or external stages not run; do not hide evidence behind a single score.

For a fresh-clone and stale-job recovery example, read
[the synthetic example](references/synthetic-example.md).
