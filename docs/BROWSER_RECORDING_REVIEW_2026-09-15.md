# Browser input and recording recovery review

Recorded and last verified: 2026-09-15, Asia/Shanghai. Source maintenance; no new release tag.
[简体中文](BROWSER_RECORDING_REVIEW_2026-09-15.zh-CN.md)

## Findings and changes

| Finding | Evidence | Maintained change |
| --- | --- | --- |
| A filled contact input can return an empty text value | In-app browser UI fixture: normal text is readable; populated, empty and invalid email controls all return `""` through DOM-style value reads. Screenshots and the fixture's visible presence/validity result distinguish them. | Input-readback guidance and explicit `unavailableFields`; missing or unavailable required values return `unknown` before a helper can suggest a retry or verify an empty target. |
| The observed omission is consistent with provider filtering | Read-only inspection of the configured browser runtime shows contact/credential classification and deliberate AX value omission. | Preserve the filter. Do not claim the page cleared the field, patch vendor code or recover secrets. |
| A deadline can leave a usable file despite incomplete recording | A real FFmpeg synthetic run hits its wall-clock deadline, accepts q, exits 0 and fully decodes; its recording result must still be failed. | Separate stop reason, shutdown method, process exit, actual return code and media QA. |
| A prior controller recovery could lose the process/result | The original incident retained a repeated `communicate(input=...)` failure and an unknown encoder exit code. Its first wait/q/kill patch lacked a timeout-branch exercise. | Reusable wait/one-q/bounded-kill helper; real child-process tests for graceful stop, ignored q, closed stdin and controller error. Preserve historical unknown exit codes. |

The input finding was reproduced with a standalone static HTML form and synthetic data;
it does not require a specific website or framework. No real application was resubmitted.
The source inspection establishes deliberate AX filtering; the DOM-style empty values
are directly observed, without claiming a complete trace of every provider internals path.
The browser runtime was inspected, not modified or redistributed.

Additional operational guidance keeps a fresh observation between a parent selector
change and its newly available dependent options. It also preserves selected capture
framing/pointer requirements and accounts for failed takes and preparation in performance
claims. There is no measured universal speed, token, quota or focus-fix claim.

## Reproduce with synthetic inputs

```sh
python -m http.server 8766 --bind 127.0.0.1 --directory examples
```

Open `http://127.0.0.1:8766/browser-input-readback.html` through the selected, permitted
browser provider. Compare its current AX/DOM-style readback with the rendered fields.
Use **Check form locally**; edit Plain text, then Blank email to an invalid and a valid
synthetic value. This page has no external submission or storage and never mirrors values
into its status output. Stop the owned local server when finished.

Observed on Windows with Codex In-app Browser, configured bundled runtime build
`26.903.61454`, package `@oai/browser-desktop` `0.1.1`. The inspected service file SHA-256 was
`c96dbf28f0854b00b0cf79e936adfb3754ecb6b0714f94c50a594d3b68940e3e`.
This identifies the inspected installation; it does not pin future host behavior.

| Synthetic state | Text control value | Email value readback | Visible/local validation |
| --- | --- | --- | --- |
| Initial defaults | `sample-alpha` | Populated and blank controls both `""` | Contact present/valid; blank absent/invalid |
| UI edits | `sample-beta` | Invalid input still `""` | Invalid input present/invalid |
| Valid UI edit | `sample-beta` | Valid input still `""` | `second@example.test` visible; present/valid |

For the optional real-encoder check, provide already selected FFmpeg/ffprobe binaries and
a new output directory. It generates only a 160×90 test pattern, never desktop input:

```sh
python examples/recording_ffmpeg_smoke.py --ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe --output-dir /path/to/new-smoke-output
```

FFmpeg 9.0.1 on Windows produced these results; exact timings/frame counts can vary:

| Case | Process result | Media | Recording classification |
| --- | --- | --- | --- |
| Natural duration | Reaped, exit 0 | 1.000 s, 12 frames, H.264 | recorded-awaiting-qa |
| Requested stop | One q, reaped, exit 0 | 1.583 s, 19 frames, H.264 | recorded-awaiting-qa |
| Deadline | One q, reaped, exit 0 | 1.583 s, 19 frames, H.264 | failed |

All three passed ffprobe and complete decode. Matching media in the last two cases is
expected: they use the same source and similar stop timing. The independently selected
stop reason is what changes the lifecycle verdict; file bytes do not establish intent.

## Validation and limits

- `python -B scripts/verify.py`: PASS, 7 skills.
- `python -B -m unittest discover -s tests -v`: 26 passed, 0 failed/skipped; includes
  7 new recording-process tests using real synthetic child processes.
- `node --test tests/browser-transaction.test.js`: 11 passed, 0 failed/skipped.
- Optional FFmpeg smoke: 3/3 expected lifecycle outcomes, 3/3 probe/decode passes.
- Local window/full-monitor wrapper adapters: 4 synthetic subcases across 1 test,
  covering saved PID before wait, deadline/exit-0 failure, startup error receipt and
  preservation of existing output/sidecars. The producer was substituted; no desktop was captured.
- Read-only forward review of scenarios 6–9: the one-off request does not select this
  workflow; contradictory extraction preserves unknown; an observed empty value remains
  meaningful; recording deadline does not become success. These are decision controls,
  not proof of automatic invocation.

Native static-window capture, GPU/driver coverage, visual acceptance of new recordings,
and revalidation of earlier final videos were not run. Process and synthetic media tests
close the recovery/classification gap within that scope; they do not certify a universal
recorder. Existing capture assets and historical receipts remain independent evidence.
