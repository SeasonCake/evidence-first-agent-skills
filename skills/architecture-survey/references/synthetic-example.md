# Synthetic example

Use this example to check that the survey distinguishes a structural seam from a size
signal.

## Request

```text
Survey the parser-to-report subsystem. The parser is 1,800 lines and changed 12 times.
Do not modify files.
```

## Known-fail response

“Split the parser because it is large and changes often.” This has not traced callers,
state, tests, or whether a smaller boundary would remove duplicated complexity.

## Known-good evidence shape

- Freeze the parser-to-report scope and recent 12-commit window.
- Trace three report consumers and their tests.
- Show whether they duplicate the same normalization/state transition.
- Apply the deletion test to the proposed boundary.
- Return `no action recommended` if size and churn are the only evidence.

The example is synthetic and does not authorize a refactor.
