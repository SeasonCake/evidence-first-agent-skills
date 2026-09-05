# Install and invoke

Each folder under `skills/` is a self-contained Codex skill. The four review skills are
explicit-only. `intent-checkpoint` permits explicit or context-matched invocation, so it
can help with a material scope choice without being named every time.

## Windows PowerShell

```powershell
$taskSkillName = 'intent-checkpoint'
$taskCodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$taskSkillDirectory = Join-Path $taskCodexHome 'skills'
$taskSource = (Resolve-Path -LiteralPath (Join-Path '.\skills' $taskSkillName)).Path
$taskDestination = Join-Path $taskSkillDirectory $taskSkillName
if (Test-Path -LiteralPath $taskDestination) { throw 'Review the existing local skill before updating it.' }
New-Item -ItemType Directory -Force -Path $taskSkillDirectory | Out-Null
Copy-Item -LiteralPath $taskSource -Destination $taskDestination -Recurse
```

Run this from the clone root and choose another skill name to install a different folder.
The example uses the configured `CODEX_HOME/skills` layout verified in our desktop setup.
Use the user-skill directory exposed by your host; current Codex documentation also lists
`$HOME/.agents/skills`. See [official skill discovery](https://learn.chatgpt.com/docs/build-skills).
If the skill does not appear, refresh/restart the host. Do not overwrite an existing local
adaptation blindly or nest a second same-name folder inside it.

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

For `intent-checkpoint`, native question cards depend on the host's actual tools and
current mode. If no suitable form is available, the skill uses a concise text question;
installing the skill does not install a new question API.

## Uninstall

Remove only the exact installed skill folder under the resolved Codex skills directory.
Do not remove the source clone or the whole skills directory. Restart Codex to refresh the
catalog.
