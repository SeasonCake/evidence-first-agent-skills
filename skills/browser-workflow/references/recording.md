# Recording a browser demonstration

Use only when recording or recovering an authorized demonstration. This reference does
not select a capture tool, install binaries or authorize new account/model/UI actions.

## Bind capture to the requested result

- Retain the selected window versus full-monitor framing and real-pointer requirements.
  Observe current target identity and dimensions; old window IDs/crop coordinates are
  not portable. A colored capture border is not a requirement unless selected.
- Use a short preflight for a new capture path. Inspect the actual resulting frames for
  black output, wrong target, unintended content and pointer visibility. Metadata or an
  encoder's zero exit code cannot prove those properties. Hardware-rendered windows may
  need a different supported capture backend; preserve protection/permission settings.
- Keep dependent browser controls in separate proven batches: changing a source/mode
  can replace the options available in the next selector. Read fresh options at that
  boundary, then group independent known edits. Preserve failed takes and receipts as
  failed evidence; do not count one batch as one total tool call or erase recovery cost.

## Bound and reconcile the encoder

An output-duration option such as FFmpeg `-t` limits media time. It is not a wall-clock
deadline: startup or a capture source that stops producing frames can delay completion.
Record the exact command, output path, requested duration, start time and child PID before
waiting. Use a fresh owned output path and no shell wrapper; keep stderr in its own file.

The optional [process helper](../scripts/recording_process.py) waits on the exact
caller-created process, sends `q` at most once, then uses bounded kill and wait. It does
not record the screen or operate the browser. Pass only a direct child whose stdin is
owned exclusively and whose output streams are redirected to files/DEVNULL, not undrained
PIPEs. Use Windows `CREATE_NO_WINDOW` when spawning a background encoder.

```python
# proc already refers to the caller's directly spawned FFmpeg child.
# Its PID/command/output receipt has been written before entering this wait.
result = finish_recording(proc, timeout=maximum_seconds + startup_grace,
                          stop_requested=lambda: stop_signal.exists())
receipt.update(result)
receipt['status'] = recording_status(result, output_bytes)
# Persist the receipt even for deadline, controller error or failed shutdown.
```

The caller owns startup failures and durable receipt writes; the helper handles the
started child's wait/shutdown. A controller error is returned as a failed result after
bounded cleanup. `kill-unconfirmed` means the process is not proven reaped: keep its
identity for recovery and do not start another recording over that output. The helper
does not promise cleanup of descendants or recovery after the controller itself is killed.

Keep `duration`, `requested`, `deadline`, `controller-error`, shutdown method, actual exit
code and process-exit confirmation distinct. A deadline followed by graceful `q` and
exit 0 remains **failed**, with a potentially salvageable artifact. A deliberate early
stop may be `recorded-awaiting-qa`; a nonempty file is never media verification.
Do not call `communicate(input=...)` again after a prior communicate attempt. A broken
stdin pipe must not prevent the process from being reaped or the receipt from being saved.

After interruption, inspect the original receipt, matching live process and existing
file before retrying. Preserve an unknown historical encoder exit code as unknown;
independent successful decode does not retroactively make that exit code zero.

## Verify the selected media

Probe duration, dimensions, frame count, codec and audio, decode the full file, and inspect
representative beginning/action/end frames. Relate visible content to the intended take.
Keep source capture, trim, final composition and published upload checks separate.
Synthetic process/FFmpeg tests validate shutdown and file handling, not desktop capture,
readability, native focus, every GPU/driver combination or existing final videos.
