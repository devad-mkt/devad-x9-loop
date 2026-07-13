# Handoff Pickup Policy

Use handoffs as the default worker completion mechanism. Do not rely on heartbeat to notice normal worker completion.

Handoff files are passive. They do not wake Sub Manager by themselves. Pickup
happens only when a user message, bounded heartbeat/automation, or manual
manager pass runs the pickup script.

## Rule

Workers never stop with only a chat message. A worker final message is valid only when it points to a durable handoff:

```text
.devad/manager/workers/<lane>/STATUS.md
.devad/manager/workers/<lane>/HANDOFFS.md
```

The final chat message should be short:

```text
HANDOFF_WRITTEN
Lane: <lane>
Status: CLAIMED_PASS | PARTIAL | BLOCKED | FAILED
Status path: .devad/manager/workers/<lane>/STATUS.md
Path: .devad/manager/workers/<lane>/HANDOFFS.md
Manager action requested: review | correct | merge-review | user-decision
```

If no `STATUS.md` or handoff exists, the manager treats the worker as
`UNVERIFIED`, even if the chat says done.

For Top Manager, missing `STATUS.md` or `HANDOFFS.md` is not a reason to read
the worker chat. It must output `MISSING_MD:<lane>:STATUS.md` or
`MISSING_MD:<lane>:HANDOFFS.md` and ask Sub Manager to collect or write the
durable files.

## Manager Pickup

The manager starts with:

```powershell
$skill = Join-Path $HOME '.codex\skills\devad-x9-loop'
$repo = '<project-root>'
$py = Join-Path $HOME '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py "$skill\scripts\collect_worker_handoffs.py" --repo $repo --write-index
```

This creates or refreshes a queue from `STATUS.md` plus the top
`CURRENT_STATUS` block in `HANDOFFS.md`:

```text
.devad/manager/HANDOFF_INDEX.md
```

Then the manager validates only the lanes that have new or actionable handoffs:

```powershell
& $py "$skill\scripts\validate_worker_packet.py" --packet "$repo\.devad\manager\workers\<lane>" --worktree "<worktree-root>\<lane>"
```

## Why This Replaces Most Heartbeats

Heartbeat is useful for checking whether active workers are blocked or drifting. It is not needed to catch normal completion when workers write handoffs. Handoff pickup is cheaper because the manager reads a small queue instead of repeatedly polling active workers.

If the user asks the manager to keep work moving, prefer:

```text
queue update -> worker packet -> durable STATUS.md + HANDOFFS.md -> one-shot pickup
```

Do not use:

```text
recurring heartbeat -> repeated thread reads -> advice-only next steps
```

Use heartbeat only when:

- the user needs unattended progress checks,
- the owner expects Sub Manager to wake after worker handoff files change,
- the owner asked for a delayed one-hour decision window,
- a worker is long-running and likely to block,
- external proof or deploy waits need timed checks,
- the heartbeat has an expiry and max wake count.

If the user says workers should hand off and Sub Manager should continue
without another user message, write or create a bounded handoff monitor. If no
monitor is created, say:

```text
No auto-wake. Manual pickup needed.
```

## Worker Handoff Requirements

`STATUS.md` and the top of `HANDOFFS.md` must include this exact current block.
It is the only authority for current state:

```md
CURRENT_STATUS:
- Lane:
- Updated:
- Scope:
- Lane status: PLANNED | ACTIVE | CLAIMED_PASS | VERIFIED_PASS | PARTIAL | BLOCKED | FAILED | REJECTED | ABANDONED
- Security review: PASS | PARTIAL | BLOCKED | NOT_REQUIRED
- Security precommit: PASS | BLOCKED | NOT_REQUIRED
- Post-commit docs: PASS | BLOCKED | NOT_REQUIRED | NOT_COMMITTED
- Source push: PASS | BLOCKED | NOT_REQUESTED
- Deploy readiness: PASS | BLOCKED | WAIVED_BY_OWNER | NOT_REQUESTED
- Live deploy: PASS | BLOCKED | NOT_REQUESTED
- Latest commit:
- Exact next action:
- Must not do:
```

Older `HANDOFFS.md` sections are historical only. Do not search lower old text
for current PASS, push, deploy readiness, or live deploy.

`HANDOFFS.md` latest section must also include:

- status,
- branch and HEAD,
- worktree,
- base SHA,
- files touched,
- tests/proof run,
- browser/API/CLI/MCP proof paths when claimed,
- blockers,
- risks,
- manager action requested.

Recommended latest section:

```md
CURRENT_STATUS:
- Lane: <lane>
- Updated: YYYY-MM-DD HH:mm Europe/Istanbul
- Scope: <one short scope>
- Lane status: CLAIMED_PASS | PARTIAL | BLOCKED | FAILED
- Security review: PASS | PARTIAL | BLOCKED | NOT_REQUIRED
- Security precommit: PASS | BLOCKED | NOT_REQUIRED
- Post-commit docs: PASS | BLOCKED | NOT_REQUIRED | NOT_COMMITTED
- Source push: PASS | BLOCKED | NOT_REQUESTED
- Deploy readiness: PASS | BLOCKED | WAIVED_BY_OWNER | NOT_REQUESTED
- Live deploy: PASS | BLOCKED | NOT_REQUESTED
- Latest commit: <sha or none>
- Exact next action: review | correct | merge-review | user-decision
- Must not do: <forbidden next action>

Older sections are historical only.

## Latest

**Status:** CLAIMED_PASS | PARTIAL | BLOCKED | FAILED
**Manager action requested:** review | correct | merge-review | user-decision
**Worktree:** `<worktree-root>\<lane>`
**Branch:** `<branch>`
**HEAD:** `<sha>`
**Base SHA:** `<sha>`
**Summary:** <short>

## Changed Files

| File | Reason | Scope OK |
| --- | --- | --- |

## Verification

| Command/proof | Result | Path |
| --- | --- | --- |

## Blockers

- none

## Risks

- none
```

## Manager Decisions

| Handoff status | Manager action |
| --- | --- |
| `CLAIMED_PASS` | Validate packet, worktree diff, tests, proof, secrets, and overlap before accepting. |
| `PARTIAL` | Review useful work and approve one next slice or correction. |
| `BLOCKED` | Decide, unblock, or stop lane. |
| `FAILED` | Inspect failure evidence before assigning a retry. |

Do not merge from a handoff alone. Handoff is the pickup signal; verification is still required.

Do not push or deploy from a handoff alone. Source push, deploy readiness, and
live deploy must be separate gates from `references/status-and-deploy-gates.md`.
