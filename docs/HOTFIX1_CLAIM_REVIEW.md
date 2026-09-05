# From logs to reliable conclusions: eight executable review cases

[简体中文](HOTFIX1_CLAIM_REVIEW.zh-CN.md) · [Synthetic receipt example](../examples/claim_receipts.py)

Distilled from BidKing `0.3.4-hotfix1` maintenance and its follow-up engineering review,
eight synthetic receipts demonstrate scoped conclusions, instrument failures, and
actionable next checks. Use the examples alongside the four existing skills.

## A tempting but unsupported inference

A user saw step five, but an exported file contains no corresponding event. A complete
search establishes only what was not found in that export. It cannot establish that
the user never reached step five, or that the user is still at step five now.

Separate three coverage questions:

1. Did the search complete, with a supported query?
2. Does the export represent the target session, revision, and time, and retain transient events?
3. Are the firsthand observation and searched object answering the same question?

Completing the first does not establish the second. Preserve firsthand timing as
independent evidence. A missing event needs a separate falsifiable investigation;
zero matches cannot manufacture its unique root cause.

## Reproduce the scoped-claim contract

```powershell
python examples/claim_receipts.py
python -m unittest discover -s tests -p test_claim_receipts.py -v
```

The standard-library script reads its synthetic JSON fixture and verifies each expected
result, showing exactly which conclusion each receipt supports.

| Synthetic receipt | Supported report | Unsupported report |
| --- | --- | --- |
| Complete search, positive match | Observed in the selected scope | Universal behavior across users or versions |
| Complete search, no match | Not observed in the selected scope | The real event never happened |
| Partial, timeout, refusal, or read error | Inconclusive | Proven absence |
| Multiline query to a line-oriented engine | Unsupported query | The string does not exist |
| A measured gate | That gate's measurement maturity | Product or release approval |
| An implemented, unmeasured gate | Measurement still pending for that gate | Every current release must be blocked |

`absence_supported` is limited to the supported search within its declared scope;
it does not prove export coverage. `proves_event_never_happened` remains false. Boolean
counts and inconsistent status/completeness are errors, not negative results. This
classifier cannot authenticate receipts: real instruments still need positive and
negative controls and concrete scope evidence.

## Correct with facts, not expanded instructions

Report **fact → impact → unknown → smallest next check**. For example:

> The supplied export was fully searched without a match. Independent evidence shows
> step five occurred. This export cannot prove the event identifier, but cannot disprove
> the step. Event retention remains unknown; inspect the matching-version export path
> before requesting an entire new run.

Explicitly supersede a mistaken claim when new evidence arrives. Do not project a tool
interruption or reconnect onto the user's actions or sample provenance. A new tool's
maturity gap is not automatically a gate for an already completed product release.

## Resource limits are part of the experiment

Start from named files and a selected repository index; set file, byte, deadline, and
output budgets. Truncating output does not bound upstream traversal. After cancellation,
confirm your owned process exited rather than killing every process with the same name.
This example provides no system-wide interceptor or background monitor.

See the companion [completeness and revision example](https://github.com/SeasonCake/bidking-inference/blob/main/docs/EVIDENCE_LIFECYCLE.md)
and the existing [skill installation instructions](../INSTALL.md).
