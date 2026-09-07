# Share progress before the release is ready

[简体中文](INTERIM_MAINTENANCE.zh-CN.md) · [Maintainer guide](../MAINTAINING.md)

A useful interim update tells readers what they can use today, what has changed within a
verified scope, and what remains unfinished. It does not need a new package version or a
promise that the next release will ship on schedule. This guide is documentation, not a new
installable skill or a change to the six skills' invocation policies.

## A small maintenance round

1. Check the selected repository's current ref, relevant CI and a bounded set of new
   issues or pull requests. Compare with the last verified baseline before repeating work.
2. Follow the current project pointer and named result records when development has moved
   ahead of the public page. An unchanged commit or quiet task feed alone does not show inactivity.
3. Write a dated update with four parts: the version usable now, scoped completed work,
   remaining evidence or decisions, and the next useful action. Keep observed facts and
   proposed improvements separate.
4. Publish only the selected content. A completed review, a scheduled run or an estimated
   release window does not by itself select a push, release, deployment or schedule change.

For a recurring workflow, choose its cadence, permitted writes, evidence budget, notification
conditions and stop condition explicitly. Try the workflow once before scheduling it.
Routine in-progress states stay quiet unless periodic updates were requested; notify for a
meaningful failure, completion or decision the maintainer needs to handle. Keep the latest
baseline and unfinished-work links available to the next run.

## Preserve the scope when evidence changes

This is a synthetic example, not a claim about a particular product:

| New observation | Accurate maintenance record | What does not follow |
| --- | --- | --- |
| A constructed input passes the source test | That revision passes the tested constructed case | Every real caller or the packaged application passes |
| A real caller exposes a mismatch | Record the new failure, affected input and owner; retain the earlier scoped result | The earlier test never ran, or its pass cancels the new failure |
| A focused correction passes independent review | Close that defect for the reviewed revision and inputs | Installation, live operation or the whole release is complete |
| The maintainer defers a narrow compatibility change | Record the selected deferral and its resume condition | The behavior passed, or unrelated issues were also deferred |

Reconcile later results with the same subject and stage before sending an alert. Preserve
the original failure and corrected result; do not restart completed tests just because a
message arrived late. One incident can motivate a candidate, not a universal rule or a new
release gate. Use [verify-claim](../skills/verify-claim/SKILL.md) for a selected verification
and [intent-checkpoint](../skills/intent-checkpoint/SKILL.md) for a genuine unresolved scope choice.

## Publish a useful summary, keep recovery evidence available

Public notes can explain the user benefit, validation scope, limitations and supported
version. Keep private requests, credentials, customer records and operational details out
of that summary. Retain the internal evidence needed to resume the work; removing details
from the public page should not destroy the recovery trail.

For the companion project's actual, explicitly unfinished snapshot, see
[development progress](https://github.com/SeasonCake/bidking-inference/blob/main/docs/DEVELOPMENT_STATUS.md).
