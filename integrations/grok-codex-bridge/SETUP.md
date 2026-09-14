# Setup, update and recovery

This experimental desktop path was exercised with Codex CLI 0.153.4, the inspected
desktop host, opencodex 2.51.0 and Grok 4.6. Start from your own installed, authenticated
proxy and Codex account; follow their supported login routes. Do not copy tokens into
this repository, run a broad configuration sync or migrate existing histories.

## 1. Inspect the compatibility inputs

The numeric and no-tools patches target these opencodex 2.51.0 source files:

| File | Before SHA-256 | Patched SHA-256 |
| --- | --- | --- |
| `src/lib/tool-argument-integers.ts` | `0ed323ea85d13016cb88e048d20238b7d87fe2beae39406229d9f970f1402b2c` | `71d71f2b1a010e10e864b8b1b83abc51bb30784e2a856a3db709c3b801fbc890` |
| `src/responses/function-call-compat.ts` | `642c72c2d9aeaad9c6840059eaab33e3729733447ac746197ad122e3c18b779b` | `78406205db2acf82f0776d4cb08c31685e9ca698dbf015947e410c9ba3b3b4dd` |
| `src/adapters/openai-responses.ts` | `5eef85b5c6a109bc14bc324dca15bc1f9292445614673d331850ffeac80187e7` | `603a67c1a68133e4259df5a74c611c3aef19c119bc28327b35cee64863f28ac4` |

The no-tools patch also adds `src/adapters/xai-no-tools-choice.ts`. Compare actual bytes
and preserve originals before applying a selected patch. A different source version or
later modification needs review; do not force these hunks over it. From the package root,
`git apply --check` followed by `git apply` can apply the two inspected patch files.
These source patches require a source-based proxy launch, such as the installed Bun
running `src/cli/index.ts start --port 10100`; they do not patch a precompiled bundle.
Reload the owned proxy through its existing lifecycle after installation. This package
does not adopt or terminate another process or install a boot service.

The numeric patch repairs only known tool/field representations; it preserves invalid
fractions, unrelated tools and permissions. The request patch removes redundant auto/none
selectors only when no tools exist at the exact xAI destination. Required/explicit tool
selection is not relaxed into successful prose.

The third patch, `compat/opencodex-2.51.0-custom-tool-history.patch`, applies **after**
the no-tools patch. It changes the adapter from SHA-256
`603a67c1a68133e4259df5a74c611c3aef19c119bc28327b35cee64863f28ac4` to
`712deb7ee15a4912d7fbca73506ffada1ff7dcde67fff404bd59ea9fefddb320` and adds
`src/adapters/xai-custom-tool-history.ts`. It supplies missing xAI custom-call item IDs
after generic `store:false` sanitization, preserving call/output pairing and all tool
input. A real manual compact had rejected that missing field with 422.

Apply/check it against the reviewed source just like the earlier patches, preserve the
original, and reload the owned source process. This public patch is based on the public
no-tools baseline; it does not require the separately excluded local media-navigation
extension. If your source includes other changes, inspect them and construct an equivalent
delta instead of forcing this patch. Optional installed-source tests default to the
final public adapter hash; `GROK_BRIDGE_EXPECT_ADAPTER_SHA256` may identify another exact,
independently reviewed extension build, not a hash derived merely to make the test pass.

## 2. Prepare the local configuration

Use Python 3.11+. A native `models_cache.json` must already exist under your Codex home;
normal Codex startup or `codex debug models` can populate it. The routed catalog must
already contain the selected Grok row with its authoritative context/compaction metadata.
It is an input, not a file to publish or a reason to enable upstream global GPT routing.

From this integration directory, substitute actual installed paths:

```powershell
python configure.py --codex-binary "C:/tools/codex.exe" --routed-catalog "C:/tools/opencodex-catalog.json" --model xai/grok-4.6
```

The default is a dry-run listing exact files and hashes. Repeat the reviewed command
with `--apply` to install. `--codex-home`, `--adapter-root`, `--base-url` and `--effort`
are explicit options. The supported URL here is a loopback HTTP `/v1` endpoint without
credentials. Existing conflicting providers, another startup catalog or a different
bridge installation are preserved and reported rather than overwritten.

Setup writes the launcher/settings, a dedicated profile and a generated catalog, then
updates the main configuration last. It adds the `ocx-grok` provider and startup catalog
pointer; native provider/default/window/permission settings remain unchanged. All native
model rows are copied intact, with only the selected Grok row appended. Existing files
that change are backed up under the adapter's `backups/` directory. Concurrent edits
detected since planning stop the update before those edits can be overwritten.

The source remains in this checkout. Keep it available or explicitly reconcile the
installation before moving it. Copying just the Skill cannot install this runtime.

## 3. Reopen and verify actual behavior

The provider/profile setup above supports bridge-created tasks. To select Grok directly
with the native desktop model button, also prepare the [optional model router](MODEL_PICKER.md)
before reopening. A catalog entry without provider pairing can still send Grok to the
native OpenAI provider and fail.

The host loads its model catalog when app-server starts. Passing a catalog only in
`thread/start.config` was observed to leave unknown-model fallback metadata in use.
Normally close/reopen the desktop after configuring; an already open model manager
does not refresh merely because the file changed.

Create one selected synthetic task, retain its request key, check actual provider/model/
cwd, then send a warm no-tools and a read-only tool control through the native app.
Verify the runtime context after both creation and native continuation. For the tested
Grok row, 500000 with a 95% effective window yielded 475000; it previously fell back to
258400. These numbers are model metadata, not a universal preset to impose on other models.

When refreshing native metadata after a host/model update, compare the generated
host-loaded native rows with the current native source again. The setup script can
regenerate from a newly available native cache; it does not promise automatic remote
discovery of every future model while a custom startup catalog is selected.

## 4. Recover or roll back

- Creation uncertainty: use the same request key with `reconcile`, never create a second
  task to hide a partial first operation.
- Ordinary follow-up: retain the task ID and use native app input. Do not open a competing
  CLI resume writer or change permissions to bypass a pending request.
- Wait/observer uncertainty: retain exact task/turn/parent and collector handle/receipt;
  a yielded command is still running, and a helper receipt is not proof of parent delivery.
- Configuration rollback: inspect the current config and selected backup, then restore
  only the owned catalog pointer/provider changes without removing later unrelated edits.
  Reopen the desktop and verify its native model metadata. Original backup bytes remain
  available; generated catalog files can remain inert without destructive cleanup.
- Proxy rollback: restore the exact backed-up source files, reload through the existing
  owned lifecycle, and check the selected route. An unreferenced helper can remain inert.

No public task histories or diagnostics are needed to follow these steps. Keep private
receipts locally and derive a small outward report containing only relevant evidence.
