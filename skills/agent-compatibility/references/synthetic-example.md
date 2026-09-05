# Synthetic example

Use this example to check fresh-clone truth and recoverable execution.

## Candidate repository

- README documents `python scripts/verify.py`.
- The script reads `fixtures/example.json`.
- The fixture exists locally but is ignored and absent from the Git index.
- A handoff says to resume process ID 4242 after restart.

## Expected result

Return `NOT READY` because a fresh clone lacks a required input and the saved process ID is
not durable execution state. The smallest fixes are to track a synthetic fixture and write
a receipt from which an equivalent bounded job can be reconstructed.

## Positive control

After the fixture is tracked and the recovery receipt is documented, verify in a fresh
clone that the command passes and stale PID absence triggers reconstruction rather than an
author authorization request. Then `READY` is possible within the tested scope.

## Question-routing control

A specified heading edit should proceed with a small diff check, without a questionnaire.
A consequential unresolved design choice should use the host's suitable native question
tool or a concise text fallback. Failure to expose that tool is not a reason to install
a form service or claim the repository cannot be used.
