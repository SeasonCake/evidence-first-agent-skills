# Source and distribution scope

Original SeasonCake code, extracted from the local Grok/Codex integration research on
2026-09-13. The maintained Python package, launcher and synthetic tests are included;
the public configurator is independently added for explicit portable setup.
File-level identities are recorded in `SOURCE_MANIFEST.json` after validation.

The local test that imports already installed native-CLI/interactive wrappers is not
included: those wrappers and their machine-specific installation are outside this
desktop package. No test has been relabeled as passing on an absent runtime.

Excluded: account/authentication files, real prompts, model-catalog snapshots, session
history/databases, personal binding ledgers, runtime logs, native observer receipts,
proprietary Codex/Grok binaries, old private baseline copies and unrelated product code.

The two opencodex modifications retain their separate MIT notice. They preserve the
upstream baseline identities documented in [SETUP.md](SETUP.md); they are source patches,
not a vendored proxy distribution or a change to native GPT request routing.
