# Install and invoke

Each folder under `skills/` is a self-contained Codex skill. The four review skills are
explicit-only. `intent-checkpoint`, `browser-workflow` and `grok-bridge` permit explicit or context-matched
invocation, so they can help in their declared scenarios without being named every time.

`grok-bridge` additionally requires the [complete integration runtime](integrations/grok-codex-bridge/SETUP.md).
Copying its instruction folder alone does not configure a model/provider or completion
return. Other skills remain copy-only and do not acquire those runtime dependencies.

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

## Optional standing route

Discovery makes a skill available; it does not prove that every matching task uses it.
If you want an explicit standing browser-workflow rule, add a short route to your applicable
user or project `AGENTS.md` after installing the skill:

```text
For multi-step browser form/editor work, repeated browser operations, browser-task recovery,
or browser efficiency tuning, read and use browser-workflow from the available skill catalog
before browser actions. Exclude one-off navigation, ordinary web research, and website
implementation alone. Preserve the chosen browser/session and current provider permissions.
```

Keep detailed behavior in the skill instead of copying it into every project. Confirm the
host actually discovers the installed skill, then test a matching request and a non-matching
request. Do not claim the route overrides host rules or changes already-running tasks' context.

## Uninstall

Remove only the exact installed skill folder under the resolved Codex skills directory.
Do not remove the source clone or the whole skills directory. Restart Codex to refresh the
catalog.
