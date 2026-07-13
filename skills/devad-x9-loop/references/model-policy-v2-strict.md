# X9 Model Policy

Use this before creating, continuing, waking, or correcting any X9 Codex
manager/worker thread.

## Required Setting

| Thread title | Compatibility role | Required profile | Thinking |
| --- | --- | --- | --- |
| Thinx | Top Manager | `GPT-5.6 Sol Ultra` | `Ultra` |
| Linx | Sub Manager | `GPT-5.6 Sol` | `xhigh` / extra high |
| Worker | Worker | `GPT-5.6 Terra` | `xhigh` / extra high |
| Worker Reader | Hidden non-decision subagent | `gpt-5.6-luna` | `medium` |
| Worker CHUNK | CHUNK Codex helper | `GPT-5.6 Terra` | `xhigh` / extra high |
| Worker SIDE | SIDE Codex helper | `GPT-5.6 Terra` | `xhigh` / extra high |

`medium`, `high`, `low`, mini, spark, a different model family, or a different
named profile is not allowed unless the owner explicitly writes:

```text
LOWER_MODEL_OK:<role>:<reason>
```

Standing owner exception: `Worker Reader` may use `gpt-5.6-luna` with medium
thinking only under `references/reader-helper-and-read-receipt.md`. This does
not downgrade Thinx, Linx, Worker, CHUNK, or SIDE.

## Thread Tool Rule

For Worker, CHUNK, and SIDE thread tools, select the host-supported Terra
identifier and pass extra-high thinking. Put this at the top of the prompt:

```md
THREAD_NAME: Worker
MODEL_PROFILE: GPT-5.6 Terra
MODEL_POLICY: GPT-5.6 Terra + xhigh / extra high required for this Worker role.
```

For Worker Reader, Thinx uses the internal subagent tool with
`model: "gpt-5.6-luna"`, `reasoning_effort: "medium"`, and
`fork_context: false`. Never use `create_thread`, `fork_thread`, or another
visible task. Put this at the top of its exact-file prompt:

```md
THREAD_NAME: Worker Reader
ROLE: mechanical extraction only
MODEL_PROFILE: gpt-5.6-luna
MODEL_POLICY: medium thinking; no decisions, approvals, coding, or mutation.
```

For Linx thread tools, select the host-supported model identifier for
`GPT-5.6 Sol`, set extra-high thinking, title the task `Linx`, and put this at
the top of the prompt:

```md
THREAD_NAME: Linx
ROLE: Sub Manager
MODEL_PROFILE: GPT-5.6 Sol
MODEL_POLICY: GPT-5.6 Sol + xhigh / extra high required for Linx.
```

For Thinx thread tools, select the host-supported `GPT-5.6 Sol Ultra` profile,
title the task `Thinx`, and put this at the top of the prompt:

```md
THREAD_NAME: Thinx
ROLE: Top Manager
MODEL_PROFILE: GPT-5.6 Sol Ultra
MODEL_POLICY: GPT-5.6 Sol Ultra required for Thinx.
```

This applies to create, fork, continue, handoff, wake, automation, heartbeat,
handoff monitor, Thinx, Linx, Worker, CHUNK, and SIDE messages.
Reader is covered only by its explicit narrow exception above.

If the available tool cannot select the named profile or thinking level, do
both:

1. Put this at the top of the prompt:

```md
MODEL_PROFILE: <required profile from the role table>
MODEL_POLICY: <required profile and thinking from the role table> required for this X9 role.
Do not continue on a different profile or lower thinking unless owner writes
LOWER_MODEL_OK:<role>:<reason>.
```

2. Record `MODEL_PROFILE_NOT_TOOL_ENFORCED:<role>:<thread>` in
   `.devad/manager/MODEL_POLICY.md` or the relevant pass note.

## Stop Rule

Stop routing if the next X9 action would run outside the role matrix or below
its required thinking without an owner waiver. Never claim Terra, Sol, or
Ultra was tool-enforced when the tool exposed only a base model id.
