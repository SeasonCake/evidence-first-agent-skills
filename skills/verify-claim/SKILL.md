---
name: verify-claim
description: Verify one falsifiable behavior or performance claim with matched baseline and treatment evidence. Use for before/after fixes, package behavior, UI, startup, or workflow claims; not for broad audits.
---

# Verify Claim

Verification proves or disproves one claim; it is not a progress recap.

## Workflow

1. Restate the claim as condition, measured outcome, threshold, and evidence tier.
2. Select a valid baseline/treatment or condition/falsifying-control comparison. Freeze
   source or artifact identity, input population, checker, environment, public entrypoint,
   process/window/session identity, warmup, units, timeout, and visible baseline.
3. Run the cheapest check that can falsify the claim. Preserve raw evidence or immutable
   identity before summarizing it.
4. Use the same checker in both arms. Identical arms, universal zeroes, missing inputs,
   setup errors, and unexpected skips are instrumentation alarms.
5. Preserve intermediate states; a correct final frame cannot erase an earlier visible
   or same-event failure.
6. Return exactly `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE`.

## Evidence boundaries

Keep source tests, package-shaped tests, native/ABI, immutable artifacts, real UI, author
operation, upload/readback, and production evidence distinct. A hidden launcher, mock,
synthetic widget, or owner-written screenshot cannot replace a claim about a public entry,
real process, or user-visible output. A skip, timeout, setup error, or missing baseline is
not a pass.

Preserve the user's reported event order and sample provenance. A missing event in an
incomplete export does not prove it never occurred; a later review screen does not prove
an earlier completion screen was absent. Align session, version, path, and timestamps.

Keep canonical local evidence and reproducibility metadata within the selected workflow.
Paths, hashes, filenames, and non-secret identifiers are not secret by shape alone; derive
external views by content and destination without rewriting the original evidence.
Use bounded reads; failed or partial lookup cannot prove absence. A verified finding
does not by itself authorize a fix or a new release requirement.

## Output

Return the claim, verdict, comparison identities, matched metrics/artifacts, threshold or
delta, confounds, and `not-run`. If only static inspection is authorized, label it clearly
and keep the verdict `INCONCLUSIVE` unless the claim itself is static.

For a matched installed-CLI example and verdict boundaries, read
[the synthetic example](references/synthetic-example.md).
