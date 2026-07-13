# Handoff Pickup Policy

Use handoffs as the default Worker completion truth. Files do not wake Linx.
After writing durable state, Worker or Thinx sends `EVENT_READY` to the same
registered Linx task using `references/direct-event-callback.md`. Always target the
same registered Linx task.

Recurring 15/19-minute pickup is forbidden.

## Rule

Workers never stop with only a chat message. A Worker final state is valid only
when it writes:

```text
.devad/manager/workers/<lane>/STATUS.md
.devad/manager/workers/<lane>/HANDOFFS.md
```

and an identity-matching completion receipt. The final chat message is compact:

```text
HANDOFF_WRITTEN
Lane: <lane>
Status: CLAIMED_PASS | PARTIAL | BLOCKED | FAILED
Status path: .devad/manager/workers/<lane>/STATUS.md
Path: .devad/manager/workers/<lane>/HANDOFFS.md
Manager action requested: review | correct | merge-review | user-decision
```

Then send one callback:

```text
EVENT_READY
LINX_TASK_ID: <registered Linx task id>
SOURCE_TASK_ID: <registered Worker task id>
SOURCE_ROLE: WORKER
DISPATCH_ID: <dispatch id>
PACKET_SHA256: <packet hash>
EVENT_TYPE: HANDOFF_READY | BLOCKED | FAILED
RECEIPT_PATH: <Worker-owned receipt>
RECEIPT_SHA256: <receipt hash>
```

If direct callback delivery fails after at most three recorded attempts, write
`MANAGER_WAKE_FAILED` and report manual pickup. Do not create recurring polling.

For Thinx, use `SOURCE_ROLE: THINX` and `EVENT_TYPE: DECISION_READY`.

## Manager Pickup

On a valid callback, Linx acquires the manager pass lock and runs:

```powershell
$skill = Join-Path $HOME '.codex\skills\devad-x9-loop'
$repo = '<project-root>'
$py = Join-Path $HOME '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py "$skill\scripts\collect_worker_handoffs.py" --repo $repo --write-index
```

Linx reads only the signaled lane/event, validates identity and current state,
performs one bounded next action, acknowledges the callback, saves state, and
releases the lock. Old or wrong-task handoffs cannot complete current work.

A user message or manual pass may still trigger pickup. An owner-requested
one-shot fallback is allowed only for a delayed owner deadline or an external
condition that cannot callback.

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
