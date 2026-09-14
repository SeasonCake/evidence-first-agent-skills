# When input readback is missing or contradictory

Use this reference when a field looks filled but text extraction is blank, when an
extracted value conflicts with the visible page, or when adapting a provider readback.

## Decide from the available evidence

An AX tree, a provider's DOM representation and the live rendered page are distinct
evidence surfaces. Some providers deliberately omit contact/credential-like values;
DOM-style evaluation can still return an empty string for those fields. Reading through
another method backed by the same representation is not independent confirmation.

1. Reconfirm the current tab, field identity and settled page state. Treat absence as
   **unavailable** until the evidence supports an actually empty field.
2. For ordinary non-secret form content, inspect the rendered field using a permitted
   screenshot or provider read view. Follow authentication/credential restrictions first;
   this is never permission to inspect secrets, change input types, mirror hidden values,
   patch a provider's filter or switch channels around a denial.
3. Use visible validation and the site's normal controls where useful. Validity proves
   neither the exact intended value nor persistence. If exact required content remains
   unknown, keep that uncertainty; do not mark it ready or repeatedly retype it.
4. After a submission, use the original receipt or a permitted persisted view. A later
   reopened form with default/partially restored fields does not cancel an earlier
   success receipt or justify another submission.

Do not label this a website reset or provider defect without discriminating evidence.
For a reproducible issue, use an isolated fixture with synthetic inputs: a plain-text
control, a populated contact field, an actually empty required field, and invalid/valid
UI edits. Compare text readback with the rendered result. No real sign-in data is needed.

## Transaction adapter contract

The pure helper cannot detect provider filtering. A caller must preserve unavailable
fields explicitly, for example:

```js
const readback = {
  key: 'test-a',
  fields: { description: 'updated' },
  unavailableFields: ['contact']
};
```

Do not encode an unavailable value as `null`, `false`, `0` or `""`: all are legitimate
values in the existing scalar contract. When a legacy adapter already returns a
placeholder, `unavailableFields` takes precedence over it. Missing required keys also
yield `unknown`; an observed empty string without that marker remains a real value.
This distinction applies to protected fields and baselines as well as owned edits.

`checkDraft` returns `ok: false, outcome: 'unknown'` for an unreadable required draft
or protected baseline. `judgeReadback` returns `unknown` before classifying unavailable
required values as verified, not-saved or conflict, even when the outer view is settled.
Neither result authorizes a save/retry. Acquire permitted evidence and update the record,
or report the precise unknown. Do not mark a draft screenshot as persisted evidence.
