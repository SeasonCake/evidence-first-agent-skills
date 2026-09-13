# Synthetic example

## Native action and observation controls

A self-owned launcher reports no targetable window, then exits. Fresh enumeration shows
its identified child owns the intended ready window. Verify that bounded startup path;
do not call it failure from the launch result alone or generalize every no-window result
to success. If a permission prompt remains pending, the outcome is still unresolved.

A click returns a screenshot with no independent post-state change. That proves a capture,
not the button's effect. A later window disappearance should be checked against the actual
owner before repeating input. Reused screenshot IDs and save timestamps are not global
capture identities. These are synthetic decisions, not a live UI performance benchmark.

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
