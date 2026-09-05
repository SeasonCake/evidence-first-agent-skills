# Upstream inspirations

No upstream skill was copied verbatim. The public-candidate text is a project-neutral
rewrite that preserves the following useful ideas and documents the differences.

`PROJECT_ORIGIN.md` separately documents the local engineering lessons that motivated
these rewrites. Project origin is not upstream source-code provenance.

## Architecture survey

- Inspiration: Matt Pocock, `improve-codebase-architecture`.
- Reference: <https://www.aihero.dev/skills-improve-codebase-architecture>
- Exact source reviewed on 2026-09-05:
  [improve-codebase-architecture](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/improve-codebase-architecture/SKILL.md),
  commit `3cca18b368ae95cdbdebbff572ccafa662551015`,
  blob `a578dd0a34ad0a8886abe7e7642b100106ba86d6`.
- Recorded license: MIT.
- License evidence: [LICENSE at the same commit](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/LICENSE),
  copyright Matt Pocock 2026. The earlier article was an inspiration reference, not a
  previously pinned source baseline.
- Adaptation: read-only, bounded scope, no automatic interview/grill, no CONTEXT/ADR
  mutation, no external report service, and no automatic browser action.

## Verify, CLI, and agent compatibility

- Inspiration: Cursor official plugins repository.
- Reference: <https://github.com/cursor/plugins>
- Recorded upstream commit reviewed on 2026-09-05: `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`.
- Previous pin: `bdf7aa355337897f167153e05069aca505dae17c`. The three selected skill
  blobs are unchanged between these commits:
  - [verify-this](https://github.com/cursor/plugins/blob/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/cursor-team-kit/skills/verify-this/SKILL.md):
    `54bcf49ad0cc6256a90750fdbec7e27f79eb3d39`;
  - [cli-for-agents](https://github.com/cursor/plugins/blob/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/cli-for-agent/skills/cli-for-agents/SKILL.md):
    `3c560387748ffb1d9960787ff2cfe93b8b086f20`;
  - [check-agent-compatibility](https://github.com/cursor/plugins/blob/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/agent-compatibility/skills/check-agent-compatibility/SKILL.md):
    `6d88d4a5f9e5a053f45c0321916e08460b3ce089`.
- Recorded license: MIT.
- License evidence: the selected `cursor-team-kit/LICENSE`, `cli-for-agent/LICENSE`,
  and `agent-compatibility/LICENSE` files at that commit all have blob
  `ca2bba771cd39dbef6acf96b52481133983451f3`, copyright Cursor 2026.
- Adaptation: three-state evidence verdicts, explicit evidence tiers, runtime conditions
  separated from authorization, durable receipt recovery, and fresh-clone/Git-index truth.

The 2026-09-05 local refinements add actual read budgets, event-order reconciliation,
useful internal evidence metadata, and short intent decisions. These are project-derived
adaptations, not newly adopted upstream behavior. Mandatory parallel scoring, automatic
report services, and blanket restrictions on local evidence storage are not imported.

## Intent checkpoint

Original SeasonCake workflow, not a rewrite of an upstream skill. Its tool-specific
reference separates an observed Codex `request_user_input_async` schema from the
[official app-server protocol](https://learn.chatgpt.com/docs/app-server).
The current host's exposed tools and instructions determine actual availability and use.

The repository owner should recheck upstream notices at the pinned identities before
publishing a release that changes the attributed material.
