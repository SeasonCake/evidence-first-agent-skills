---
name: intent-checkpoint
description: Resolve a material ambiguity or disagreement about scope, outcome, owner, or next stage with a short user decision, preferably a native question form. Use before an unselected expansion, including optional protection work; do not interrupt clear, reversible in-scope work or replace host approvals.
license: MIT
---

# Intent Checkpoint

Turn a consequential fork into a small, explicit user choice, then continue the selected work.
This is a decision workflow, not a new approval system or a reason to ask before every action.

## Decide whether a question is needed

First compare the latest user instruction with the proposed next action: object, outcome,
responsible actor, stage, and explicit exclusions. Use current evidence to resolve factual
uncertainty when a cheap in-scope check can do so; do not ask the user to diagnose for you.

- **Clear selection:** continue the normal reversible steps needed for that selected endpoint.
- **Material fork:** ask if different plausible interpretations change product behavior,
  ownership, deliverables, substantial cost, or a destructive/external/later-stage action.
- **Explicit reservation:** preserve it. A prerequisite finishing does not authorize the next
  stage. If the user reserved the start to a named actor or a later instruction, wait for that
  signal instead of asking repeatedly or dispatching a coordinator message to manufacture it.
- **Speculative adjacent idea:** usually record or omit it. Do not make the user decide every
  opportunity an audit, model, tool, or historical handoff happens to suggest.

A phrase such as "for safety" does not select extra encryption, signing, anti-debugging, or
a new release gate. Distinguish an observed violation of the existing baseline from an
optional protection proposal; do not hide the former or promote the latter into a requirement.
Likewise, simplifying diagnostic wording does not select removal of the underlying controls.

## Ask the smallest decision-changing question

Use the user's language and normal level of detail. Prefer one question; group up to three
closely related decisions when they can be answered independently.

State the verified context, the fork, and the practical consequence. Offer two or three
genuine alternatives where useful, with a brief tradeoff and a supported recommendation.
Include a no-change or defer choice when it is a real option. Avoid loaded "safe/unsafe"
labels, false urgency, bundled permissions, and a long questionnaire for a small decision.
Respect free-text answers rather than forcing them into the nearest option.

Prefer an available native question tool when the current host and instructions permit
that tool for this purpose. Read [native forms](references/native-forms.md) when choosing or
adapting the tool call. Do not install a plugin, build a form service, or invent a callable
tool merely to show choices. If native forms are unavailable or not permitted, ask one
concise plain-text question. Required host permission prompts remain separate.

While awaiting a material answer, pause only the affected action and continue independent,
already-selected work. Do not repeatedly send the same form or poll for an unchanged answer.
If no independent work remains, state the unresolved choice and yield.

## Interpret the answer without enlarging it

Only an actual submitted answer or direct user instruction resolves the user's choice.
A preselected option, successful form submission request, timeout, closed card, or host
"resolved" notification is not by itself an affirmative user answer.

Bind the answer to the question it answers. If a newer instruction changes the decision,
use the newer instruction and supersede the pending interpretation. Ask a narrow follow-up
only if the submitted answer still leaves a material fork.

Record the chosen action/object/stage and any explicit exclusions in the existing plan or
nearest decision record when the choice affects later work. Keep it brief; a separate receipt
system is not required. A historical record is a retrieval cue, not perpetual authority.

Proceed through the selected endpoint without asking again for the same reversible steps.
Do not append unselected proposals, remove existing protections, or infer publication,
deployment, deletion, or another actor's start from a milestone. Target checks, resource
limits, recovery procedures, and host permissions still apply to the actual execution.

## Review the behavior

Use [synthetic examples](references/synthetic-example.md) when adapting or evaluating this
skill. Include both a material fork that should elicit a question and a clear instruction
that should not. Check the resulting action, not whether an answer contains particular words.
Do not claim that a form guarantees incident prevention or that schema validation proves
the skill will make correct decisions.
