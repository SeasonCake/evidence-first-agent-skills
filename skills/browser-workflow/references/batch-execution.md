# Repeated-item execution

Use this reference for repeated forms, editors or import-plus-edit workflows. Keep the
active provider's documented API, session and confirmation rules. This is not a reason
to install a browser, import credentials, replay an old command or call an undocumented API.

## Prepare once, preserve each item

Build one compact operation table before the first write: stable business key, selected
fields/delta, distinguishing type/quantity/batch identity, surrounding fields to preserve,
and the source revision of the author's requirements. Shared copy is a template, not a
replacement for each tier's entitlements. Validate every rendered tier before filling;
missing or conflicting types/quantities are not defaults to guess.

The optional [transaction helper](../scripts/transaction-kit.js) provides pure JavaScript
`prepareBatch`, `checkDraft`, `judgeReadback` and `summarize`. It performs no browser,
filesystem or network operations. Read it before use. Load it only through mechanisms
the active execution provider permits, or translate its checks into the current session.
Its `createBrowserWorkflowKit()` factory can live once in a persistent JavaScript session;
reuse it instead of resending it for each item. Use ordinary declarations or a supported
module loader; do not rely on string evaluation/code generation being available. Do not use page evaluation to inject it
into application state, or treat its result as permission to submit.

Each adapter supplies ordinary observed records: `{key, fields}`. Fields are JSON scalar
values with explicit types; normalize observed UI strings to the chosen schema in the
adapter, not in a permissive equality checker. Preserve raw evidence for rejected parses.
Plan items contain `key`, `owned` (per-item overrides of prepared `shared` fields), optional
`protected` (expected surrounding fields), and `requirementRevision`. Shared and owned
maps are selected writes only. Identity/type/batch/quantity checks belong in `protected`
when unchanged, or in `owned` only if the author selected that field change.

## Prove one item, reuse immediately

Inspect one live item and its editor first. Once navigation, field mapping and persistence
checks work, bind a short reusable item function to that current session. Locate every
next item by stable key and fresh semantic state. A previous AX number, row order, title
or success toast is not sufficient identity or readiness.

Pass the current plan/checker and mutable result state explicitly, or keep them in one
session object. After changing a helper, reconcile the active item's saved state and
recreate dependent functions together; do not assume previously bound closures see a
new top-level binding. This avoids stale checks and split result tables in persistent REPLs.

An item function may keep this known sequence within one tool call:

1. Open the selected key; wait, within a bounded deadline, for that key, loaded fields and
   enabled required controls. Observe a mismatched key or changed editor as a branch.
2. Read its baseline; apply only the selected fields through supported controls; reread
   the draft and compare owned plus protected fields. A draft mismatch stops this save.
3. Respect any provider/user confirmation boundary. Submit once, record that attempt
   immediately, then wait for settled save state. Do not click again while pending.
4. Use a fresh read-only persisted view or reopen after settling. Verify key, every owned
   value and protected value, then retain the compact result plus necessary evidence.

Internal observations and assertions must execute even when only the final compact
record is returned. Return to the model on unknown structure, contradictory evidence,
new user input, permission requirements or failure; never hide a branch inside a blind
loop. Bound both item count and wall clock of each call so the host can deliver new input.
Do not write concurrently into the same form or race a saved-state check against saving.

For coupled import-and-description tasks, preserve the author's selected sequence.
An import is a separate external action: bind its receipt to the correct product, batch,
card type and count. Record completion before moving to description fields. A later
description repair must not replay the import. The generic helper does not infer that
an import occurred from a stock number; use the actual import receipt and stock readback.

## Resolve uncertainty narrowly

Separate operation outcome from notification delivery. Read authoritative persisted
state before deciding whether a missing toast, locator timeout or lost response needs
another save. Keep intended delta and baseline available without overwriting the draft.

| Observed result | Next action |
| --- | --- |
| Save still pending or no authoritative outcome | Do not resubmit. Bounded non-mutating status/readback; return unknown if unresolved. |
| Persisted key, owned and protected values match | Complete this item even if the toast was missed. |
| Authoritative settled readback still equals the verified baseline | Mark not-saved. If the original edit remains authorized and no concurrent change exists, reacquire current state and retry only the missing owned delta once, subject to provider confirmations. |
| Mixed old/new values, another version or changed surrounding data | Conflict/partial state. Return the differences; do not replay or overwrite the full item. |
| Input contains unexpected or unrelated text | Do not save that item; preserve the input and inspect ownership. Independent items may continue if their state is unambiguous. |
| Wrong identity, loading page, denied access or failed extraction | Preserve the exact category and last known step. Do not report success or change channels to evade a denial. |

If an item was already in the desired state before submission, record it as unchanged;
do not invent a save. `judgeReadback` requires an adapter-supplied authoritative/settled
classification; the helper cannot prove those flags or inspect a hidden backend itself.
It returns a narrow decision, never a retry loop. A second unsuccessful save ends the
automatic repair attempt; expose what is known and the recovery point.

## Accept new requirements without duplicating work

At tool-call boundaries reconcile newly delivered user input before the next mutation.
Update the operation table's requirement revision and only affected deltas. Completed
imports stay completed; a new copy style or warning threshold revisits only those fields.
Keep old receipts attached to their old revision and record the new request separately
from error-driven rework. Do not treat an unanswered preselection as an author decision.
No additional confirmation is needed for ordinary reversible intermediate steps already
covered by the chosen endpoint; actual provider confirmations remain in force.

## One fact table, one finish

Keep result rows as work finishes: key/revision, outcome, changed or unchanged fields,
save attempts, authoritative readback and evidence locator, and any next step. Build the
receipt and short final report from one current row per business key. Keep superseded
rows in history; current save-attempt counts cover all attempts for that item in this run.
`summarize` preserves failures and unknowns and refuses duplicate business keys, including
two revisions of the same item; do not count one item or action twice. Redact sensitive content in outward reports, not the identity
needed for internal recovery. Do not return full business field maps or secret imports.

Reverify only when a row is stale, uncertain, affected by new input or required by the
task. Do not add a fresh all-page sweep, another ledger or a second ceremonial report.
Close when the selected endpoint is established; legitimate new requests are not wasted
work and should be accounted for separately.

When measuring, hold input, provider/session, model settings and acceptance endpoint
constant. Include preparation, recovery, readback and closing time. Report tool runtime,
model-visible calls/round-trips, returned text/images and whole-task latency separately;
use measured token counters if available, otherwise report unavailable. A local synthetic
comparison cannot establish real-shop reliability, native input-focus repair or universal
speed/account-usage savings.
