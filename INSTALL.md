# Install and invoke

Each folder under `skills/` is a self-contained Codex skill. All four are explicit-only:
installing them does not add their full instructions to unrelated tasks.

## Windows PowerShell

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$skillHome = Join-Path $codexHome 'skills'
New-Item -ItemType Directory -Force -Path $skillHome | Out-Null
Copy-Item -Recurse -Force '.\skills\verify-claim' (Join-Path $skillHome 'verify-claim')
```

Repeat the final command for another skill. Restart Codex after installation if the skill
catalog is already open.

## Verify before copying

```powershell
python scripts/verify.py
```

When the current Codex skill validator is available, also run it against each selected
skill folder.

## Invoke

Use the skill name explicitly, for example:

```text
Use $verify-claim to verify that this CLI returns the same result after a clean install.
```

## Uninstall

Remove only the exact installed skill folder under the resolved Codex skills directory.
Do not remove the source clone or the whole skills directory. Restart Codex to refresh the
catalog.
