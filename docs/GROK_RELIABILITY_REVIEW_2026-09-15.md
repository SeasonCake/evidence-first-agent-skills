# Grok result return, role context and compact recovery

Recorded 2026-09-15. This update lets the parent wait for a delegated Grok turn and
read its original result without asking another model to quote it. It also separates
worker instructions from parent procedures and repairs a reproduced xAI history shape
that rejected manual compaction. Results below apply to the inspected local setup.

## Changes you can use

- `observe` now returns a compact notice. `receive` verifies the exact parent/task/turn,
  dispatch, receipt hash and original message hash, then returns unchanged result text.
  Complete JSON is retained up to 128 KiB separately from its clipped preview. Larger
  payloads and old clipped V1 receipts remain explicitly unavailable through this path.
- The active parent holds one bounded wait. A native wake may contain no message body;
  collection/readback completes the return. No extra model observer is required for this
  lifecycle. Separately selected observers and their existing responsibilities remain valid.
- `context --role` includes the selected role in the fingerprint without removing common
  rules or changing permissions. Workers do not load parent creation/observer procedures
  merely to return an ordinary assignment. Selected documents and receipt strings remain data.
- A third opencodex patch supplies missing xAI custom-call item IDs at final serialization.
  `call_id`, tool input/output and permissions remain intact. The patch is based on the
  published no-tools baseline and does not require the private native-media extension.

See [the Skill](../skills/grok-bridge/SKILL.md),
[completion workflow](../skills/grok-bridge/references/native-observer.md),
and [patch setup](../integrations/grok-codex-bridge/SETUP.md).

## What the live checks established

| Check | Observation | Scope |
| --- | --- | --- |
| Read-only write control | The actual default-path attempt returned `PermissionError`; the target file was absent | One exact read-only/on-request task turn |
| Explicit Full access | A user-selected task wrote and read back a synthetic JSON file; its byte hash matched | This task recorded `danger-full-access / never`; no automatic parent inheritance claim |
| Restart | The prior managed proxy exited normally; a new process launched the selected installed source | A normal owned lifecycle, without editing Codex binaries or history |
| Native compact | Before repair: HTTP 422, missing `custom_tool_call.id`. After reload: `contextCompaction` plus completed status, 128 seconds | One manual compact; one duration is not a performance target or universal fix |
| Post-compact continuity | The worker recalled its earlier marker/remaining plan, read changed rules, selected the new data and wrote 313 fen | It preserved the earlier artifact and the explicit Full access setting |
| Original result return | Parent waits woke for the dispatched turns; exact original JSON/message hashes and artifact hashes matched | Same active-parent lifecycle; no offline or after-final notification guarantee |
| Native image | One 1024×1024 JPEG was generated, visually inspected and returned with its actual path/hash | The native wrapper is a separate local component, outside this public package |

Earlier local role controls also exercised a new task, unchanged guidance, a changed rule
and a selected worker-to-parent planning role. Shared rules stayed present and the outputs
followed the tested current revisions. This does not prove the absence of every possible
cross-project/role error or stable permissions for every newly created task.

## A retained partial failure in the native image job

The image exists and matches the requested fictional scene. The nested native CLI also
attempted an unnecessary Bash/MCP directory listing, which its image-mode policy denied.
The wrapper correctly retained `tool_failed`; the outer Codex worker reported that status
alongside the valid artifact instead of hiding the denial or generating another image.

Inspection found that the restricted helper received the project rules but lacked the
full Imagine guide it was asked to read. The separate local wrapper now attaches the
current bounded guide, records its hash, and assigns disk/visual acceptance to the outer
worker. Its positive tool list and Bash/MCP denials are unchanged. Fourteen local context
tests passed, including retained partial-failure classification and byte-preserving
Windows guide attachment. A fresh native
planning control read the attached guide and chose image generation for fiction, code
for exact chart labels/data, and a real reference for a named person. It called no tools.
Its `no_required_tool_activity` status is the expected negative generation control.

The existing image was not regenerated. A new generation after that guide correction
was not run, so the planning control is not relabeled as clean image-generation proof.
Neither the native wrapper nor the bundled Imagine guide is redistributed here.

## Reproduce the relevant checks

From the integration directory, with Python 3.11+:

```text
python -B -m unittest discover -s tests
```

The updated public integration passed 149 tests with Python 3.13. The first attempt used
Python 3.10 and could not import the required `tomllib`; that was an environment/collection
error, not a failed runtime assertion. The supported-interpreter run completed normally.

Optional checks require an already inspected opencodex installation:

```text
bun test --no-install tests-js
```

The inspected installed variant passed 46 tests / 105 assertions: numeric-tool compatibility,
no-tools choice, custom-call history, wrong-destination controls and native OpenAI API/forward
controls. Set `GROK_BRIDGE_OCX_ROOT` and follow the exact-source hash instructions in setup.
No network/model calls occur in those tests. The new public patch is additionally checked
against its own published baseline, separate from the local media extension.

No account-level cost saving, automatic compact threshold, indefinite-session reliability,
native cross-provider Subagents repair, or all-host permission inheritance is established.
