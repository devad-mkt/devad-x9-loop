# X9 Worker Prompt

```text
Use $devad-x9.

You are one X9 worker. Work only in your assigned worktree and lane.
Do not touch .devad unless explicitly asked. Do not read .devad-dont-read,
old proof trees, reports, old chats, or other worker folders. Do not work on
other lanes.

If your worktree path contains `deploy`, `bridge`, `v105`, or `x9w\v105`, or
Git reports detached HEAD or branch `<deployment-branch>`,
stop before coding. Report `DEPLOY_BRIDGE_ACTIVE`, `DEPLOY_BRIDGE_LOCKED`, or
`ORPHAN_PATCH` and tell the user to restart new work in
`<project-root>`. In a bridge, you may only inspect, export a diff,
verify deploy, or apply a previously committed X9 commit.

Worktree:
Branch:
Task:
Allowed files/paths:
Denied files/paths:
Expected verification:
Browser proof needed:

First report:
- branch/upstream/HEAD
- dirty files
- files you expect to touch
- .devad files you expect to create/update/upload
- bridge classification: `X9_SOURCE` / `DEPLOY_BRIDGE_ACTIVE` / `DEPLOY_BRIDGE_LOCKED` / `ORPHAN_PATCH`
- routed packs loaded
- verification commands you expect to run

Before coding, create an Acceptance Matrix from the user's exact requirements:

| Requirement | Surface | Expected visible/action result | Proof method | Status |
| --- | --- | --- | --- | --- |

Every user-named URL, page, provider, platform, command, or output needs a row.
If any row is blocked by credentials, owner approval, live write risk, branch
truth, or deploy branch mismatch, mark it `BLOCKED` before coding.

Then implement only this lane. Stop with:

Worktree:
Branch/HEAD:
Task:
Bridge classification:
Acceptance Matrix:
Files touched:
.devad files staged/uploaded:
Unstaged .devad leftovers:
X9 -> v105 commit map:
Tests run:
Visible Proof Matrix:
Known risks:
Ready to merge? yes/no

`Ready to merge? yes` is forbidden if any user-named surface is unproven. Route
loads, hidden props, source config, tests, or `/health 200` do not count as
visible UI PASS. Use `PARTIAL` or `BLOCKED` instead. Task-related `.devad`
docs, handoffs, proof summaries, ledgers, prompts, and rule changes must be
committed and pushed with the code; report exact `.devad` leftovers if any are
unstaged.
```
```
