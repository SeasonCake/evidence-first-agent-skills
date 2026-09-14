# Trace and recovery

These operations inspect current identity and evidence without starting a model turn:

```text
python ADAPTER_ROOT/desktop.py reconcile --request-key EXISTING_REQUEST_KEY
python ADAPTER_ROOT/desktop.py list --parent-id ACTUAL_CALLING_TASK_ID
python ADAPTER_ROOT/desktop.py trace --thread-id EXISTING_TASK_ID --turn-limit 3 --item-limit 20 --include-content
python ADAPTER_ROOT/desktop.py permissions --thread-id EXISTING_TASK_ID --turn-id EXACT_TURN_ID
```

Reconcile an uncertain creation before repeating it. Trace uses bounded pages, exact
cursors and explicit clipping; a page is not the entire history. `notLoaded` describes
the reader process and does not prove that a GUI task is idle. `--raw-tools` can inspect
bounded canonical tool records when the API omits a call; reasoning is not exported.
Keep real traces private and inspect actual command/file output when checking a claim.

Permission inspection reads the exact turn's recorded context, not the live UI state.
An old read-only task may correctly deny a later write. Preserve that denial or pending
approval; do not auto-approve, change settings or use another writer to bypass it.
After an authorized user setting change, check the next turn's evidence and actual
operation. A ready bridge parent binding does not establish permission inheritance.

For context diagnosis, compare catalog settings against real creation/continuation/reopen
behavior. A per-thread catalog field did not refresh the tested startup model manager.
Do not force global windows or add unrelated model rows to make one check pass.

Native compact acceptance needs the actual `contextCompaction` event, successful terminal
turn status and a follow-up continuity check. A no-op summary or a quiet UI is insufficient.
Retain the same active operation and a bounded wait; a slow request without an error is
still pending. Source installation and a live managed reload are separate evidence.
