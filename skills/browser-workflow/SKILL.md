---
name: browser-workflow
description: "Execute multi-step or repeated browser workflows with reliable edits, saved-result verification, and compact evidence. Use for form/editor workflows, browser-task recovery, or browser efficiency tuning; not one-off navigation, ordinary web research, or website implementation by itself."
license: MIT
---

# Browser Workflow

Keep the user's selected browser/session and business outcome intact. This skill adds
workflow discipline; it does not replace the active browser provider's API, permissions,
confirmation requirements, or tool-specific skill. Read those instructions before control.

## Choose the narrowest working route

- Prefer an already available purpose-built connector for the requested operation when
  it preserves the selected account/session and outcome. An explicit browser choice wins.
- For an unfamiliar or authenticated external site, reuse the authorized built-in session
  when available. Observe the actual page before choosing selectors or grouping actions.
- For a user's own web project or a proven repeated flow, a permitted, already installed
  CLI can be appropriate. Read [conditional CLI use](references/cli.md) only when choosing
  or comparing that route. Do not change the global browser default or install tools merely
  to optimize one task. If the current provider requires CUA, keep browser control in CUA.
- Read local files, task status and artifacts through their own tools. Do not automate
  Codex's interface to retrieve them or to submit feedback.

## Treat edits as small transactions

Identify each target by its stable business key, not a stale row number. For each item:

1. Read the live baseline and distinguish owned fields from surrounding content.
2. Apply the selected delta. For a rich-text field, use supported editing controls and
   text-format paste; verify the intended field/range was replaced and surrounding content
   survived. Do not paste an HTML string into a plain-text editor or mutate application
   state through an unsupported evaluation shortcut.
3. Read back the draft before saving. Unexpected text, duplicates or changed surrounding
   content are a reason to stop that item's save and determine ownership, not to overwrite
   the whole form. Continue independent items only when their state is unambiguous.
4. Save once, then obtain an authoritative confirmation and a fresh persisted readback
   where available (reopen/reload the item after a clear save result). A success toast or
   zero exit code alone does not prove the requested content persisted.

If submission times out or its outcome is unknown, inspect the saved state or transaction
receipt before retrying. Prefer a non-mutating receipt or separate read view so the existing
draft is not lost; preserve the intended owned delta before any necessary reload. Do not
replay the entire workflow or duplicate an external action.
An irreversible action still needs the authority required by the active provider/user.

## Reduce overhead without losing observation

- Reuse valid tab/session/job handles. After navigation, modal changes, asynchronous
  updates or a failed locator, obtain fresh state rather than reusing old element indexes.
- Group deterministic actions whose targets and intermediate behavior are already known.
  Keep observation points around branches, saves and uncertainty; do not use blind loops.
- Return only the fields needed to decide the next action, with stable IDs and relevant
  units/status. Keep the underlying error/receipt when diagnosing; compact output must not
  turn missing content, a loading page or an error into success. AX labels, DOM tags and
  CSS selectors are different representations—confirm the actual one before use.
- Inspect the actual rendered surface when layout or visible copy matters. A DOM read,
  HTTP response or hidden render does not prove visible correctness.

## Recover without masking the failure

- Distinguish wrong target, stale locator, incomplete loading, content extraction failure,
  unsupported response MIME/download handling, authentication, transport, and policy denial.
  Report the observed category; do not infer all client-block errors are permission bugs.
- A failed navigation may leave the previous page visible. Verify final URL and content
  identity before reading it as the requested destination.
- A security/permission denial is not a reason to switch to another browser, CLI or fetch
  channel. Preserve the exact failure and use allowed diagnostics; do not probe around it.
- On Windows, background browser input has been observed to disturb another Codex task's
  typing/IME focus. When concurrent typing is relevant, warn before a short input burst
  and coordinate it. If unrelated text appears, stop submitting that item and preserve
  the user's input. Re-clicking the chat composer can restore typing even while browser
  work continues; do not claim the workflow fixed native focus or requires stopping all
  work. Do not run a human-input experiment unless the user selected it.

Close with changed items, persisted verification, failures/unknowns, and remaining input.
For performance claims, separate tool runtime, model round-trips, returned bytes and total
task latency. A fixed-page benchmark is not proof of universal speed or account-usage savings.

When evaluating or adapting the workflow, use the [synthetic decision cases](references/synthetic-example.md).
They distinguish successful recovery from duplicate submission, wrong-page reads and
incorrect speed claims; they are not records of real user interactions.
