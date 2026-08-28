# Upstream inspirations

No upstream skill was copied verbatim. The public-candidate text is a project-neutral
rewrite that preserves the following useful ideas and documents the differences.

## Architecture survey

- Inspiration: Matt Pocock, `improve-codebase-architecture`.
- Reference: <https://www.aihero.dev/skills-improve-codebase-architecture>
- Recorded license: MIT.
- Adaptation: read-only, bounded scope, no automatic interview/grill, no CONTEXT/ADR
  mutation, no external report service, and no automatic browser action.

## Verify, CLI, and agent compatibility

- Inspiration: Cursor official plugins repository.
- Reference: <https://github.com/cursor/plugins>
- Recorded upstream commit reviewed: `bdf7aa355337897f167153e05069aca505dae17c`.
- Recorded license: MIT.
- Adaptation: three-state evidence verdicts, explicit evidence tiers, runtime conditions
  separated from authorization, durable receipt recovery, and fresh-clone/Git-index truth.

Before publication, the final license file should reproduce the selected license text and
the repository owner should recheck upstream notices at the pinned identities.
