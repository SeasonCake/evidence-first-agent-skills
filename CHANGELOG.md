# Changelog

This project follows Semantic Versioning. Dates use `YYYY-MM-DD`.

## [Unreleased]

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
