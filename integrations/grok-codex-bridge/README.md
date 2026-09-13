# Grok ↔ Codex desktop integration

Keep Grok work in a persistent, directly editable Codex task, with bounded history reads
and a finite native completion observer that returns delegated work to its parent.
Native GPT requests keep their own provider. This is an **integration project with a
companion Skill**, not an instruction-only Skill or native cross-provider Subagents parity.

## Included

| Component | What it does |
| --- | --- |
| `grok_codex_bridge/` | Create/reconcile persistent tasks, inspect history/permissions, refresh canonical instructions, observe one exact delegated turn |
| `configure.py` | Dry-run or apply local provider/profile and an additive startup catalog; preserve native model rows and unrelated config |
| `desktop.py` | Resolve the installed source and selected adapter root |
| `compat/` | Two narrowly scoped opencodex 2.51.0 source patches and upstream notice |
| `tests/`, `tests-js/` | Offline protocol, identity, recovery, configuration and request-shape controls |
| [Grok bridge Skill](../../skills/grok-bridge/SKILL.md) | Teach the installed workflow and conditional observer procedure |

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

No command here installs a model, logs in, copies authentication, enables global GPT
proxying, changes permissions, edits Codex history, or starts a permanent watcher.
The CLI factory performs one real initialization turn; subsequent input belongs to the
native app. A ready binding alone does not arm the completion observer.

## Verification

Python 3.11+ from this directory:

```text
python -B -m unittest discover -s tests
python desktop.py --adapter-root YOUR_ADAPTER_ROOT context --cwd PROJECT --workspace-root WORKSPACE --doc README.md
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
