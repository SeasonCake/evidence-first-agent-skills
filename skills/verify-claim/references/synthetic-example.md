# Synthetic example

Use this example to check evidence-tier separation.

## Claim

```text
After the change, the installed public CLI starts in under two seconds and returns the
same JSON as the source entry point for fixture sample.json.
```

## Matched check

- Baseline: source entry point, exact fixture SHA, clean environment, three runs.
- Treatment: installed wheel CLI, same fixture/checker/environment, three runs.
- Threshold: every treatment run is under two seconds and normalized JSON is identical.
- Negative control: change one fixture value and prove the checker detects the delta.

## Verdict boundary

A source unit test alone is `INCONCLUSIVE`; a timeout is not a pass; one mismatched output
is `NOT VERIFIED`; all matched runs and the negative control passing is `VERIFIED`.

## Event-order control

A user reports seeing a completion screen, then supplies a screenshot from the history
page. An export lacks the terminal event. The supported conclusion is that this export
does not establish the terminal boundary, not that the earlier screen never appeared.
Check the same session's version and callback path before proposing a cause. Preserve
ordinary artifact paths and hashes for reproduction; removing them is not a stronger check.
