# Central Facts Policy

Use this when branch/deploy facts matter, details were forgotten, or a manager
must choose what is next.

`CENTRAL_FACTS.md` is tiny current truth. `MISSION_LOCK.md` is the hard outcome
contract. `LOCAL_WORK_LEDGER.md` classifies local-only work. They are not
history logs.

## Central Facts Template

Keep it under 50 lines.

```md
# Central Facts

CENTRAL_FACTS:
- Updated:
- Latest user override:
- Active lane:
- Feature ID:
- Role:
- Repo root:
- Manager-state worktree:
- Manager-state branch:
- Manager-state HEAD:
- Implementation worktree:
- Implementation branch:
- Implementation HEAD:
- Deployment branch:
- Deployment HEAD:
- Must reach: plan | commit | push | deploy | live-proof
- Finish only when:
- Must not:
- Required proof:
- Current blocker:
- Exact next action:
- Detail links:
```

Never use one generic `Source branch` or `Current HEAD` field for different
worktrees. Older fields remain readable during migration but must be replaced
when the file is next updated.

## Mission Lock Template

```md
# Mission Lock

MISSION_LOCK:
- Updated:
- Owner goal:
- Active lane:
- Feature ID:
- Repo root:
- Implementation branch:
- Deployment branch:
- Target SHA:
- Must reach:
- Finish only when:
- Forbidden actions:
- Required gates:
- Owner waivers:
- If mismatch:
```

## Dream And Distill

- `DREAM_PASS`: propose the next action only from current durable facts and
  current repo/runtime evidence.
- `DISTILL_PASS`: after a Worker pass, update only changed facts, answered
  decisions, tool lessons, local work, feature index, and exact next action.

Before routing, verify all branch/HEAD pairs independently. Rebuild a stale
local-work ledger or generated index. Read only the detail links needed for the
next action.

Use these blockers exactly:

```text
MISSING_CENTRAL_FACTS
MISSING_MISSION_LOCK
MISSING_CENTRAL_FACT:<field>
STALE_CENTRAL_FACTS
MISSING_LOCAL_WORK_LEDGER
STALE_LOCAL_WORK_LEDGER
BRANCH_LOCK_MISMATCH
MISSION_LOCK_MISMATCH
FINISH_LINE_NOT_REACHED
```
