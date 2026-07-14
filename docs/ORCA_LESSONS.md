# Orca Lessons For X9 Loop Lite v6

Orca proves that coordination becomes reliable when identity and completion
are explicit. X9 adopts those contracts without adding Orca as a runtime
dependency.

## Keep

| Concept | X9 Lite form |
| --- | --- |
| Task and dispatch identity | Immutable task ID, `dsp-<uuid>`, packet hash |
| Dependency-ready queue | SQLite task dependencies checked before dispatch |
| Worker-owned completion | Hashed `RESULT.json` plus identity and Git scope |
| Decision gates | Task-scoped PASS/PENDING/BLOCKED rows |
| Three-failure circuit breaker | Pause one Worker task for Thinx review |
| Stale Worker warning | Report; never auto-kill or delete its worktree |
| Full handoff vs supervised dispatch | Explicit ownership in the task contract |

## Reject

| Orca surface | Why X9 Lite rejects it |
| --- | --- |
| Orca runtime dependency | X9 must recover from tracked project state alone |
| Runtime database as truth | Disposable SQLite cannot replace Git-tracked truth |
| General message bus and groups | More routing state than three worktrees need |
| Terminal and pane management | Codex transport remains outside controller state |
| Heartbeat and status traffic | Burns turns without proving completion |
| Frequent polling/coordinator run | Direct callback plus one retry is cheaper |
| Four Workers by default | X9 promotes 1 to 2 to 3 only after clean evidence |
| Automatic Worker termination | Risks lost local work |
| Global reset | Can erase unrelated coordination evidence |

## Complexity Boundary

For three disjoint worktrees, the production loop is:

`register -> reconcile -> prepare one dispatch -> record transport -> consume one result`

Everything else is a gate or recovery command. X9 does not copy Orca terminal
groups, inbox history, coordinator polling, heartbeat lifecycle, or runtime
ownership. This preserves the useful semantics without rebuilding Orca inside
Markdown or model turns.
