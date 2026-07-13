# Owner Wait And Handoff Monitor

Use this when the Sub Manager should wait for the owner before routing workers,
or when workers are expected to finish by writing `STATUS.md` / `HANDOFFS.md`.

## Handoff Monitor Reality

Worker handoff files are passive. They do not wake Sub Manager alone.

If the owner expects unattended pickup, Sub Manager must create or ask for a
bounded monitor. In the Codex app, use a heartbeat automation attached to the
manager thread. `.devad/manager/HANDOFF_MONITOR.md` without an app heartbeat is
only a plan; it will not wake anything.

Whenever Sub Manager sends or continues a Worker and expects a later handoff,
it must do one of these before final chat:

1. create/update `.devad/manager/HANDOFF_MONITOR.md` and the real Codex app
   heartbeat automation,
2. write `NO_AUTO_WAKE:<reason>` in the pass note and tell the owner manual
   pickup is required.

The monitor prompt should only:

1. run `collect_worker_handoffs.py --write-index`,
2. read changed `STATUS.md` / top `CURRENT_STATUS`,
3. validate only actionable lanes,
4. classify blockers as `SOFT_BLOCKER`, `HARD_BLOCKER`, or `OWNER_DECISION`,
5. use Top Manager, SIDE, or read-only research before asking the owner about a
   `SOFT_BLOCKER`,
6. notify the owner or write a manager pass note,
7. stop when no active/actionable lanes remain, max wakes are reached, or the
   newest owner message changes the mission.

If no monitor is created, say plainly:

```text
No auto-wake. Sub Manager will need a user message or manual pickup.
```

## Required Final States

Every Sub Manager pass that has active Workers or just sent Worker orders must
end with one of these states in chat and in the pass note:

| State | Meaning |
| --- | --- |
| `MONITOR_ACTIVE` | A real app heartbeat exists and watches the listed handoffs. |
| `OWNER_WAIT_ACTIVE` | Owner has a deadline/default in `OWNER_WAIT.md`. |
| `WORKER_SENT_AND_MONITORED` | Worker got orders and a monitor is active. |
| `HARD_BLOCKED` | No safe fallback exists without owner/secret/destructive action. |
| `OWNER_DECISION_REQUIRED` | Owner must choose risk/scope/priority. |
| `NO_ACTION_VERIFIED` | No active actionable handoff remains. |

Do not finish with only "next suggestions" if a Worker was sent or an active
handoff may arrive later.

## One-Hour Owner Wait Window

Use this when the owner wants to hear the options first, then let Sub Manager
decide after one hour if the owner does not answer.

Sub Manager must:

1. write/update `.devad/manager/OWNER_WAIT.md`,
2. show the owner a tiny options table,
3. state the exact default action that will happen after the deadline,
4. create or request a one-shot/bounded heartbeat for the deadline,
5. avoid giving workers new implementation orders during the wait except
   safety stop, handoff cleanup, or read-only proof collection.

`OWNER_WAIT.md` format:

```md
# Owner Wait

**Status:** ACTIVE | EXPIRED | CANCELLED | ANSWERED
**Created:** YYYY-MM-DD HH:mm Europe/Istanbul
**Deadline:** YYYY-MM-DD HH:mm Europe/Istanbul
**Question:** <one short question>
**Default verdict if no answer:** <one safest action>
**Must not do before deadline:** <forbidden action>

## Options

| Option | Risk | Proof needed | Worker impact |
| --- | --- | --- | --- |

## After Deadline Rule

If no newer owner answer exists, refresh truth, do safe research, then choose
the safest honest verdict. Do not merge, push, deploy, delete, reset, stash,
clean, force-push, or start broad implementation because the owner was silent.
```

## After One Hour

When the deadline heartbeat fires:

1. check the newest owner message first,
2. if answered, mark `OWNER_WAIT.md` as `ANSWERED` and follow the answer,
3. if not answered, refresh repo truth and worker handoffs,
4. do bounded research from repo/source/docs/proof files only,
5. use SIDE challenge if the choice is high-risk and safe,
6. choose the safest honest verdict:
   - prefer read-only review, narrow proof, or one small reversible worker slice,
   - block if money, deploy, security, data loss, destructive cleanup, or broad
     merge risk remains unclear,
   - never claim owner approval from silence.

Record the result:

```text
OWNER_WAIT_EXPIRED:<decision>
```

Then update `QUEUE.md`, `DECISIONS.md`, `OWNER_WAIT.md`, and a pass note.

## Worker Orders During Wait

Allowed before deadline:

- request missing `STATUS.md`,
- request missing `HANDOFFS.md`,
- request proof path cleanup,
- stop unsafe work,
- read-only validation or trace collection.

Blocked before deadline:

- new implementation orders,
- commit/push/deploy,
- merge/port,
- cleanup/delete/reset/stash/force-push,
- starting new worker lanes unless needed to prevent damage.
