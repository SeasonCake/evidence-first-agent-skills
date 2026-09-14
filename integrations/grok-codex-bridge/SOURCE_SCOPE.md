# Source and distribution scope

Original SeasonCake code, extracted from the local Grok/Codex integration research on
2026-09-13. The maintained Python package, launcher and synthetic tests are included;
the public configurator is independently added for explicit portable setup.
File-level identities are recorded in `SOURCE_MANIFEST.json` after validation.

September 14 adds the existing native model/provider router, its Python entry, Windows
C# stdio bootstrap and synthetic routing tests. The catalog helper now accepts an
explicit list of Grok rows while retaining its original single-model API. The public
Windows bootstrap tests use a temporary argument-echo fixture, not installed account
data or live model requests. No precompiled bootstrap is distributed.

The local test that imports already installed native-CLI/interactive wrappers is not
included: those wrappers and their machine-specific installation are outside this
desktop package. No test has been relabeled as passing on an absent runtime.
The later local media-navigation adapter embeds machine-specific Skill/wrapper assumptions
and is also excluded. The public package does not claim to install native Imagine or
reproduce that local media route merely by adding Grok to a menu.

Excluded: account/authentication files, real prompts, model-catalog snapshots, session
history/databases, personal binding ledgers, runtime logs, native observer receipts,
proprietary Codex/Grok binaries, old private baseline copies and unrelated product code.

September 15 adds parent-owned waiting, compact notices plus verified original-result
readback, and explicit context roles without dropping common rules. Synthetic controls
cover long Unicode results, legacy/clipped receipts, wrong identities/hashes, and changed
role/rule context. The xAI custom-tool history patch targets the published no-tools
baseline; its deterministic helper is shared with the locally tested repair.

The three opencodex modifications retain their separate MIT notice. They preserve the
upstream baseline identities documented in [SETUP.md](SETUP.md); they are source patches,
not a vendored proxy distribution or a change to native GPT request routing.
