# Changelog

This project follows Semantic Versioning. Dates use `YYYY-MM-DD`.

## [Unreleased]

- Add parent-owned bounded waits and verified original Grok result readback, retaining
  complete JSON separately from compact notices and keeping legacy clipped data unknown.
- Separate worker/parent context procedures and add an xAI custom-tool history patch
  for the missing-item-ID compact failure, with scoped live recovery and offline controls.
- Distinguish unavailable/filtered browser input values from actual empty fields;
  keep missing readbacks unknown in the transaction helper and add synthetic UI controls.
- Add bounded recording-process recovery with separate deadline/requested-stop results,
  real child-process regressions and a browser/recording investigation report.
  [Evidence and reproduction](docs/BROWSER_RECORDING_REVIEW_2026-09-15.md)
- Publish the optional native model/provider router and Windows bootstrap source,
  with idle-switch/policy controls, explicit setup and scoped compatibility evidence.
- Preserve the catalog helper's single-model contract while supporting selected
  multiple Grok rows; add Windows argument/stdio checks without model calls.
- Link the bilingual BidKing/Grok demo and distinguish its separately installed
  native image wrapper from the public desktop integration.

- Add `grok-bridge` as a seventh Skill, with the full desktop integration separately
  under `integrations/`: explicit configuration, native-preserving startup catalog,
  persistent tasks, context/trace/permission inspection and finite native result return.
- Add portable protocol/configuration tests and retained MIT compatibility patches;
  distinguish source setup from host acceptance and exclude private runtime/account data.
- Extend browser batch/read-only guidance with a pure transaction helper and executable
  positive/negative controls; reject non-JSON map objects without changing browser permissions.
- Refine existing verification/CLI/compatibility guidance for launcher/owner transitions,
  capture versus save time, yielded handles, stop versus reaped, and actual loaded settings.

- Make synthetic examples an explicit local package so an unrelated installed
  `examples` package cannot shadow fixture imports; cover the collision in a fresh process.
- Clarify forwarded scope ownership and local-versus-overall completion in
  `intent-checkpoint`; add three synthetic cases and preserve later explicit starts/pauses.
  [Read-only forward scenario review](docs/INTENT_SCENARIO_REVIEW_2026-09-08.md)
  covers both prompt and no-prompt decisions, not automatic matching or live host behavior.
- Add bilingual guidance for interim progress updates and recurring maintenance, with
  synthetic examples separating scoped passes, later failures, corrections and deferrals.
  This documentation update does not change installable skills or invocation policies.
- Add `browser-workflow` with six synthetic scenarios, conditional CLI guidance, and
  explicit/context-matched invocation. Document an optional standing `AGENTS.md` route
  without replacing provider rules or claiming universal performance gains.
- Tighten `intent-checkpoint` discovery and wording; add a ninth scenario for delayed
  answers after a newer start. Preserve its invocation policy and existing boundaries.
- Validate public boundaries across all directly attached Markdown references, including
  conditional references, with positive/negative regression coverage.
- Add `intent-checkpoint`: short native question forms for consequential choices,
  text fallback, and eight synthetic cases, including optional protection scope and
  when clear instructions should proceed without repeat approval.
- Preserve the four review skills' explicit-only policy while allowing context matching
  for the new skill; validate each declared policy with positive and negative controls.
- Improve bounded discovery, event-order evidence, reproducibility metadata, and
  execution continuity in the review skills. Refresh exact upstream references and
  make copy-only installation preserve existing local adaptations.
- Focus the home page on useful workflows and runnable examples, with project details
  linked from the relevant documentation.
- Add a bilingual hotfix1/follow-up-review case study, eight synthetic claim receipts,
  and executable regressions separating scoped absence, incomplete searches, unsupported
  queries, and gate maturity from real-world or release claims. That case-study update
  did not change the installable skills.
- Refresh GitHub Actions to the current Node 24-based action releases.

## [0.1.0] - 2026-08-29

- Add four explicit-only agent skills: architecture survey, claim verification, CLI
  contract review, and agent compatibility.
- Add per-skill attribution, upstream provenance, repository validation, and public
  project-origin boundaries.
- Add MIT licensing and DCO contribution terms.
- Add clean-install and fresh-clone verification for the first public release.
