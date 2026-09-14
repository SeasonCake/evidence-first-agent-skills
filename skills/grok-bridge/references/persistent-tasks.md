# Persistent Grok tasks and current context

Create only an independent task or delegation selected by the user. For a new logical
creation choose one stable request key and retain it after interruptions:

```text
python ADAPTER_ROOT/desktop.py create --request-key UNIQUE_REQUEST_KEY --title "Grok task" --cwd ABSOLUTE_PROJECT
```

For delegation add `--parent-id ACTUAL_CALLING_TASK_ID`. Do not guess or rebind the
parent. An ID alone is not ready: `state=ready` establishes initialization and persisted
readback, not business completion, permission inheritance or an armed return route.
Give the user the returned task link. For selected delegated work, read the parent's
[completion procedure](native-observer.md) before dispatch.

Use native app send/wait tools for follow-ups, omitting model/effort overrides to retain
the existing binding. The user may also type directly in that task. Do not create another
task for an ordinary follow-up or use a second CLI/app-server writer for an app-owned task.

Before the first substantive handoff, a changed role/rule, or uncertain loaded context:

```text
python ADAPTER_ROOT/desktop.py context --cwd ABSOLUTE_PROJECT --workspace-root ABSOLUTE_WORKSPACE --thread-id EXISTING_TASK_ID --role worker --doc README.md
```

Select `parent`, `worker`, `observer` or `standalone` for the actual assignment. The role
participates in the context fingerprint and never changes permissions. Select the actual
project/workspace ancestor boundary, not the integration installation directory.
Repeat `--doc` for applicable current contracts; selected references remain data.

Metadata is the default. `--prompt` returns current full bounded file content for a
native handoff; alternatively have the task read those exact files. A changed hash requires
refresh before work, not another task. Missing files and cwd mismatches are errors.
Attachment/hash evidence does not establish model compliance or an automatic host watcher.
Check actual reads and behavior for material rule changes. Keep original project AGENTS
files canonical, and read linked procedures only when their triggers apply.

On uncertain creation, use the same key with `reconcile`. A lost or timed-out result must
be reconciled against the original turn and receipt before retrying any business work.
