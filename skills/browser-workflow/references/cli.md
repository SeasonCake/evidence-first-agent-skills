# Conditional CLI use

Read only when a browser CLI is allowed by the current host and is being selected or
compared. This reference grants no exception to a CUA-only rule or a policy denial.

## Select from actual capabilities

- Keep an explicitly selected browser/profile. Separate CLI profiles may lack the user's
  login, cookies or working external-site access; do not copy private profiles or cookies.
- Playwright CLI is a candidate for a user's own web-development/testing flow. A lightweight
  agent-browser CLI is a candidate for an already understood repeated flow. These are
  conditional choices, not required defaults or universally faster tools.
- Inspect the selected installed package's version, runtime requirement, command help and
  bundled instructions before control. Reuse a known installation; do not silently use
  `npx latest`, change PATH/defaults or install another copy. If unavailable, continue with
  the permitted working provider unless installation is actually needed and selected.

## Windows execution and evidence

- Use a task-owned named session and an explicit executable. Verify a package's Windows
  native binary option and supported Node version instead of assuming a JS wrapper works.
- Give owned commands/processes real deadlines. A tool's output-yield interval is not a
  process timeout. If browser descendants keep inherited output handles open, use the
  tool's supported background/session mechanism and bounded output files rather than
  treating a silent parent as still doing useful work. Reuse the job and inspect its receipt.
- Inspect exit status together with expected page identity, actual visible body and saved
  state. Exit 0 with a framework script, empty body or error page is an extraction failure.
- Preserve the raw result locally when a compact extraction is inconclusive. Print only
  decisive content/errors; do not feed repeated full DOMs or script bundles into context.
- Close only task-owned sessions/processes, using verified handles/identity; never broadly
  kill browsers or enumerate unrelated profiles to recover one failed run.

## Compare only when the comparison will change the decision

Use equivalent authorized inputs, correctness criteria, and representative repeat counts.
Retain failed cases instead of timing only successful paths. Include startup and recovery
costs relevant to the intended workflow. Do not extrapolate a fixed synthetic page to
authenticated sites, unfamiliar UI, IME behavior or total model/billing savings.
