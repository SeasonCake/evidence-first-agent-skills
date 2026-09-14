# Grok ↔ Codex desktop integration

Keep Grok work in a persistent, directly editable Codex task, with bounded history reads,
parent-owned waiting and exact original-result readback for delegated work.
Native GPT requests keep their own provider. This is an **integration project with a
companion Skill**, not an instruction-only Skill or native cross-provider Subagents parity.

## Included

| Component | What it does |
| --- | --- |
| `grok_codex_bridge/` | Create/reconcile tasks, inspect history/permissions, refresh instructions for the selected role, collect and verify an exact delegated result |
| `configure.py` | Dry-run or apply local provider/profile and an additive startup catalog; preserve native model rows and unrelated config |
| `desktop.py` | Resolve the installed source and selected adapter root |
| `grok_codex_bridge/model_router.py`, `scripts/` | Optional native model/provider pairing over stdio, with Windows bootstrap source |
| `compat/` | Three narrowly scoped opencodex 2.51.0 source patches and upstream notice |
| `tests/`, `tests-js/` | Offline protocol, identity, recovery, configuration and request-shape controls |
| [Grok bridge Skill](../../skills/grok-bridge/SKILL.md) | Separate worker procedures from parent waiting, original receipt and conditional observer responsibilities |

The native Grok CLI/media wrappers, proprietary binaries, account credentials, model
catalog snapshots and personal runtime records are not bundled. Use the official native
Grok CLI separately when its own tools are the selected task. A proxy login, compatible
Codex host and native parent/subagent tools remain external prerequisites.

## Quick path

1. Read [setup and recovery](SETUP.md), including the exact compatibility baseline.
2. Run `python configure.py ...` to inspect the concrete plan; repeat with `--apply`
   only when installing the selected local integration.
3. Normally reopen Codex so its model manager loads the startup catalog. Keep the
   selected proxy running through the documented upstream/local entry.
4. Ask Codex to use `$grok-bridge` for an independent Grok task or explicit delegation.

For direct selection using Codex's existing model button, follow the optional
[model-picker setup](MODEL_PICKER.md). Adding a catalog row alone does not bind the
right provider. Cross-provider changes require an idle task; active work is preserved.

[English demo](https://x.com/zheng_qili666/status/2099349396895019095) ·
[中文实录](https://www.bilibili.com/video/BV1rRYk63ER5/). The video includes a separately
installed native Imagine wrapper; neither that wrapper nor a default media route is
provided by this desktop package.

No command here installs a model, logs in, copies authentication, enables global GPT
proxying, changes permissions, edits Codex history, or starts a permanent watcher.
The CLI factory performs one real initialization turn; subsequent input belongs to the
native app. A ready binding alone starts neither a wait nor an observer. The current
`observe` command prints a compact notice; use `receive` with its receipt hash to read
the unchanged result. Old complete V1 receipts remain readable; old clipped payloads
remain unknown. See [completion return](../../skills/grok-bridge/references/native-observer.md).

## Verification

Python 3.11+ from this directory:

```text
python -B -m unittest discover -s tests
python desktop.py --adapter-root YOUR_ADAPTER_ROOT context --cwd PROJECT --workspace-root WORKSPACE --role worker --doc README.md
```

The tests use synthetic local fixtures and no model calls. Set `GROK_BRIDGE_OCX_ROOT` to
an already inspected patched package before optional Bun checks:

```text
bun test tests-js
```

Current host acceptance and its limits are summarized in [compatibility evidence](COMPATIBILITY.md).
Those scoped live results do not certify every host version, automatic threshold or
long-running session. A fresh installation must verify its actual provider, task and
runtime context rather than infer them from a menu label or configuration file.

Original SeasonCake integration code is under the repository MIT license. The patches
derive from opencodex's MIT source; its separate notice is retained in
[compat/LICENSE.opencodex](compat/LICENSE.opencodex). See [source scope](SOURCE_SCOPE.md).
