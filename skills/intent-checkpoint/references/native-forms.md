# Native question forms

Read this when selecting a question tool or adapting the workflow to another host.
The current session's actual tool list, schema, mode restrictions, and higher-priority
instructions control the call. Names below are observed examples, not universal APIs.

## Asynchronous form

A Codex desktop session may expose `request_user_input_async` (for example under
`functions`). In the observed schema it takes:

- `questions`: an array of objects;
- each object has a self-contained `title` and optional string-array `options`;
- free text is already available, so do not add an "Other" placeholder;
- the first option is preselected, not submitted;
- the call returns immediately; the user answer arrives as a later message.

For a design-stage choice, the argument shape can be:

```json
{
  "questions": [
    {
      "title": "The current release uses the existing protection baseline. Which scope should this proposal cover?",
      "options": [
        "Keep this release unchanged; record the proposal for later",
        "Assess one bounded protection option; do not implement yet"
      ]
    }
  ]
}
```

This example does not grant permission to implement either protection work or a release.
Use it only when there is a real design question, not when the user already chose.

## Synchronous form and fallback

Some sessions instead expose `request_user_input` with IDs, header labels and
label/description options. It can be restricted to Plan mode or to particular question
purposes. Check the current schema and instructions rather than translating the async
payload blindly. Do not use it for a permission request if the host forbids that use.

If no suitable native form is callable, use a concise plain-text question. Do not display
an imitation of a submitted choice or claim the UI was shown when it was not.

## Response lifecycle

Distinguish tool acceptance, user response, and host cleanup. Correlate a response with its
question before applying it; free-text clarification can supersede the offered choices.

The official [Codex App Server documentation](https://learn.chatgpt.com/docs/app-server)
describes app-server user-input requests separately from command/file/permission approvals.
It also documents that `serverRequest/resolved` may mean an unanswered request was cleared,
and that hosts can automatically resolve some prompts. That protocol is not proof that an
agent-facing async tool exists in another session, nor that the user explicitly consented.

Do not replace required host approvals, switch modes, open another task, or weaken execution
restrictions to force a question tool to work.
