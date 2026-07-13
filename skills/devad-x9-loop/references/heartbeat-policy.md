# Heartbeat Policy

Use heartbeats only for bounded monitoring. A heartbeat is not memory, not a completion signal, not a continuation engine, and must never outrank the newest user request.

Normal worker completion should use durable handoffs and manager pickup:

```text
.devad/manager/workers/<lane>/STATUS.md
.devad/manager/workers/<lane>/HANDOFFS.md
.devad/manager/HANDOFF_INDEX.md
```

These files are passive. They do not wake a Codex thread by themselves. A Sub
Manager wakes only from a user message, a bounded heartbeat/automation, or a
manual manager pickup pass.

## Default

Heartbeat is `OFF`.

For a collaborative Linx replacement, heartbeat remains OFF until
`OLD_LINX_FINAL_REVIEW: PASS` and a valid `LINX_ACTIVATION_OK` token exist in
`.devad/manager/LINX_HANDOVER_STATE.md`. The automation must target the new
Linx thread, never the old one. When the owner requests a 19-minute wake, use
exactly **19 minutes**, delta-first reads, at most 76 wakes, and a 24-hour
expiry per version. Renew only from the new Linx after fresh scope and lock
checks while active Workers remain.

Every wake must acquire `.devad/manager/MANAGER_PASS_LOCK.md`. If the lock is
owned by a direct owner turn, another wake, or an unfinished pass, return
`SKIP_ACTIVE_MANAGER_PASS` and do nothing. A newer owner message cancels the
heartbeat pass immediately. Release the lock before the wake ends.

Do not create a recurring heartbeat merely to avoid asking "what is next." Use
durable worker handoffs, queue files, and one-shot manager pickup instead.

Turn it on only when:

- one manual manager pass already succeeded,
- truth lock is fresh,
- worker packets exist,
- active workers are bounded,
- the user explicitly asked for timed monitoring, handoff pickup, or an
  owner-wait deadline,
- expiry, max wakes, and cadence are written.

## Limits

| Setting | Limit |
| --- | --- |
| Active implementation workers | 2 until trust is rebuilt |
| Cadence | 10-15 minutes unless user says otherwise |
| Max wakes | 6-12 for handoff pickup; 3-6 for quick proof checks |
| Max duration | same day unless user renews |
| Manager app-code edits | never |
| Merge/deploy | never |
| File edits | pass logs or manager state only when explicitly allowed |
| Mutation | monitor/notify only unless current gate file explicitly allows one bounded action |

If a worker handoff exists, use handoff pickup instead of another timed wake.
Two no-change wakes may stop only when no active worker is still expected to
write a handoff. If a scoped worker is still active, keep the monitor until max
wakes, expiry, a changed handoff, or a hard owner decision.

Heartbeat must not turn old `PASS` text into action. It may monitor and notify
by default. It must not route new implementation work, push, deploy, merge, or
mark PASS unless `STATUS.md`, top `CURRENT_STATUS`, and any required gate file
authorize the exact action.

Heartbeat is never an implementation or product-judgment role. It cannot code,
generate previews, reconstruct history, answer owner contradictions, or take
over a Worker. Those become `JUDGMENT_REQUIRED` or `WORKER_REQUIRED` routing.

## Durable Continuation Gate

A heartbeat never invents approval. It must, however, act on a fresh durable
owner gate already recorded in `ANSWERED_DECISIONS.md`, `CENTRAL_FACTS.md`,
`MISSION_LOCK.md`, or the current pass note. A newer direct owner instruction
such as `continue`, `do next`, `run the goal again`, `do not stop`, `give the
worker next action`, or a complaint that the next Worker action was not sent
also authorizes exactly one smallest safe bounded action when the scope is
already durable and unambiguous; write that decision durably before dispatch.

Named gate tokens are durable labels, not a second approval ceremony. Do not
ask the owner to repeat a clear direct instruction as a synthetic token. Derive
the label, record it, and dispatch once. A review marker such as
`IMPLEMENTATION_NOT_STARTED_OR_APPROVED_BY_THIS_REVIEW` limits the review; it
does not override a newer direct owner request for the reviewed smallest safe
chunk. Do not chain an older instruction that was already consumed to obtain
the review into implementation; require one fresh post-review instruction.

This direct-instruction rule does not approve provider spend, deploy, push,
merge, destructive operations, branch changes, or live mutation. Those actions
still require exact operation-and-target approval.

Do not repeatedly return quiet output when an approved bounded action is queued
and no target Worker or reviewer is active. Dispatch one role/action, update
`HANDOFF_MONITOR.md`, and monitor it. Provider spend, deploy, push, merge,
destructive operations, branch changes, and live mutations still require exact
approval for that action.

If no valid gate exists, notify the owner once with the exact missing decision,
record the owner wait, and remain quiet until relevant state changes.

If `STATUS.md` is missing or stale, stop with:

```text
BLOCKED_STALE_STATUS:<lane>
```

## Handoff Pickup Monitor

Use this only when the owner expects Sub Manager to wake after worker handoffs.

Allowed actions:

- run `collect_worker_handoffs.py --write-index`,
- read changed worker `STATUS.md` and top `CURRENT_STATUS`,
- validate actionable lanes,
- classify blocker type: `SOFT_BLOCKER`, `HARD_BLOCKER`, or
  `OWNER_DECISION`,
- for `SOFT_BLOCKER`, use Top Manager, SIDE, or one safe read-only fallback
  before asking the owner,
- notify the owner or write a pass note,
- stop when no actionable lanes remain.

Blocked actions:

- new implementation orders unless current gates and owner-wait policy allow it,
- commit, push, deploy, merge, cleanup, delete, reset, stash, or force-push.

Required visible final state:

```text
MONITOR_ACTIVE | OWNER_WAIT_ACTIVE | WORKER_SENT_AND_MONITORED |
HARD_BLOCKED | OWNER_DECISION_REQUIRED | NO_ACTION_VERIFIED
```

## Owner-Wait Heartbeat

Use this when the owner wants Sub Manager to wait one hour before deciding.

At creation:

- write `.devad/manager/OWNER_WAIT.md`,
- record absolute deadline with timezone,
- record the default safe verdict,
- tell the owner `No answer by <time> => <default verdict>`.

At wake:

- read newest owner message first,
- if answered, mark `OWNER_WAIT.md` as `ANSWERED`,
- if not answered, mark `OWNER_WAIT.md` as `EXPIRED`,
- refresh truth and handoffs,
- do bounded safe research,
- choose the safest honest non-destructive verdict,
- never treat silence as approval for push, deploy, merge, destructive cleanup,
  or broad implementation.

## HEARTBEAT.md

```md
# Manager Heartbeat

**Status:** OFF | ACTIVE | EXPIRED | STOPPED
**Version:** hb-YYYYMMDD-N
**Created:** YYYY-MM-DD HH:mm Europe/Istanbul
**Expires:** YYYY-MM-DD HH:mm Europe/Istanbul
**Max wakes:** <n>
**Wakes used:** <n>
**Cadence:** <10m|15m|custom>
**Latest user override at creation:** <summary>

## Scope

| Lane | Worker chat | Worktree | Allowed manager action |
| --- | --- | --- | --- |

## Rules

- Read newest user message before acting.
- Stop if newest user message conflicts with this heartbeat.
- Refresh truth lock first.
- Read `STATUS.md` before `HANDOFFS.md`; old handoff sections are history.
- If a commit SHA appears, require `Security precommit: PASS` and
  `Post-commit docs: PASS` before push/deploy advice.
- Do not code, merge, deploy, reset, stash, clean, delete, or force-push.
- Intervene only for blocker, completion, drift, unsafe overlap, missing proof, or stale state.
```

## Stale Heartbeat Detection

Stop and report `BLOCKED_STALE_HEARTBEAT` when:

- status is not `ACTIVE`,
- expiry is in the past,
- wakes used is greater than or equal to max wakes,
- heartbeat version differs from `TRUTH_LOCK.md`,
- latest user message changes the mission, worker list, or stop/continue decision,
- another manager pass owns an unexpired `MANAGER_PASS_LOCK.md`,
- repo branch/HEAD no longer matches the heartbeat scope.

Always use absolute dates and times.
