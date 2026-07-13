# Truth Lock Protocol

A truth lock re-anchors a long-running manager chat. It prevents stale callbacks, legacy heartbeats, stale handoffs, and worker claims from replacing current repo truth.

## Refresh When

Refresh `.devad/manager/TRUTH_LOCK.md`:

- at the start of a manager pass,
- after any new user direction,
- before sending worker corrections,
- before merge, port, drop, or deploy recommendations,
- before arming a direct callback or owner-requested one-shot fallback,
- after compaction, resume, branch switch, commit, push, or base SHA change.

## Template

```md
# X9 Truth Lock

**Updated:** YYYY-MM-DD HH:mm Europe/Istanbul
**Manager chat:** <chat id or unknown>
**Latest user override:** <short exact summary>
**Override source:** user | heartbeat | worker | manager
**Heartbeat version:** none | hb-YYYYMMDD-N
**Heartbeat expires:** none | YYYY-MM-DD HH:mm Europe/Istanbul

## Repo Truth

| Item | Value |
| --- | --- |
| Repo path | `<project-root>` |
| Manager-state branch | `<branch>` |
| Manager-state HEAD | `<full sha>` |
| Implementation branch | `<branch>` |
| Implementation HEAD | `<full sha>` |
| Deployment branch | `<branch>` |
| Deployment HEAD | `<full sha>` |
| Upstream | `<remote/branch or none>` |
| Remote X9 source | `<branch> @ <sha or unknown>` |
| Remote deploy/v105 | `<branch> @ <sha or unknown>` |
| Dirty tracked files | `<count>` |
| Untracked files | `<count>` |
| `.devad/ACTIVE.md` | fresh | stale | missing | skipped |
| Central facts | PASS | STALE | missing |
| Mission lock | PASS | MISMATCH | missing |
| Local work ledger | PASS | PARTIAL | BLOCKED | missing |
| Deploy gate | PASS | BLOCKED | missing | skipped |
| Owner wait | OFF | ACTIVE | EXPIRED | missing |
| Callback identity | PASS | MISSING | FAILED |

## Active Mission

- Goal: <one sentence>
- Non-goal: <one sentence>
- Current slice: <one sentence>
- Must reach: plan | commit | push | deploy | live-proof
- Target SHA: <sha or unknown>
- v105 role: deploy-only | hotfix-only | active | not-used
- Hard gates: <short bullets>

## Workers

| Lane | Chat ID | Worktree | Branch | Base SHA | Lane status | Security | Precommit | Docs | Source push | Deploy ready | Live deploy | Owns | Forbidden | Last proof | Next |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Shared Files

| File | Workers | Risk | Decision |
| --- | --- | --- | --- |

## Proof State

| Slice | Source | Backend | Browser | API | CLI | MCP | Security | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Stale Checks

- Newest user request conflicts with callback scope: yes/no
- CENTRAL_FACTS.md missing/stale/too long: yes/no
- MISSION_LOCK.md conflicts with repo/branch/HEAD/deploy/finish line: yes/no
- Worker packet older than worker branch HEAD: yes/no
- Worker STATUS.md missing or stale: yes/no
- Worker base differs from manager HEAD: yes/no
- Worker edited outside scope: yes/no
- Local-only active-lane work unclassified: yes/no
- Commit security precheck missing: yes/no
- Post-commit doc missing: yes/no
- Owner wait active before worker order: yes/no
- Callback pickup expected but exact identity/receipt is missing: yes/no
- Old handoff PASS conflicts with current STATUS.md: yes/no
- Deploy/push gate missing for claimed action: yes/no
- Secrets risk present: yes/no

## Next Approved Action

<one action, or NONE>
```

## Stale Detection

| Signal | Mark |
| --- | --- |
| A recorded branch/HEAD pair differs from its own current Git evidence | `STALE_ACTIVE` |
| `CENTRAL_FACTS.md` missing, stale, vague, or too long | `MISSING_CENTRAL_FACTS` or `STALE_CENTRAL_FACTS` |
| `MISSION_LOCK.md` conflicts with branch, HEAD, target SHA, deploy branch, or finish line | `MISSION_LOCK_MISMATCH` |
| Callback identity is stale, mismatched, or conflicts with newest owner message | `BLOCKED_STALE_CALLBACK` |
| Worker base SHA differs from current manager HEAD without approval | `BASE_DRIFT` |
| Worker changed forbidden or unclaimed files | `WORKER_DRIFTING` |
| `LOCAL_WORK_LEDGER.md` missing/stale while git is dirty | `MISSING_LOCAL_WORK_LEDGER` or `STALE_LOCAL_WORK_LEDGER` |
| Active lane has unclassified local work | `LOCAL_ONLY_WORK` |
| Worker says PASS without manager verification | `CLAIMED_PASS` |
| Worker lacks current status block | `MISSING_CURRENT_STATUS` |
| Deploy/push/live claim lacks gate | `BLOCKED_GATE_MISSING` |
| Worker handoff pickup expected but callback identity is missing | `MANAGER_WAKE_NOT_ARMED` |
| Owner wait active | `OWNER_WAIT_ACTIVE` |
| Manager cannot state original goal and current user override | `MANAGER_DRIFTING` |
