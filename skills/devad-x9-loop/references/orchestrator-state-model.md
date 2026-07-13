# Orchestrator State Model

Use durable files for manager state. Chat memory is not authority after long runs, context compaction, or heartbeat resumes.

## State Locations

| State | Location | Notes |
| --- | --- | --- |
| Original mission | `.devad/manager/MISSION.md` | The stable goal and non-goals. |
| Central facts | `.devad/manager/CENTRAL_FACTS.md` | First file read before "what next"; current facts only, under 40 lines. |
| Mission lock | `.devad/manager/MISSION_LOCK.md` | Hard repo, branch, target SHA, deploy, finish-line, and proof contract. |
| Local work ledger | `.devad/manager/LOCAL_WORK_LEDGER.md` | Active local dirty/untracked work and release-state classification. |
| Current override | `.devad/manager/CURRENT.md` | Latest user direction and active scope. |
| Top Manager plan | `.devad/manager/TOP_MANAGER.md` | File-only Top Manager view, priorities, missing MD facts, and one next action. |
| Model policy | `.devad/manager/MODEL_POLICY.md` | Required X9 model/thinking for Top Manager, Sub Manager, Worker, CHUNK, and SIDE. |
| Truth lock | `.devad/manager/TRUTH_LOCK.md` | Current repo, branch, HEAD, remote SHAs, dirty state, workers, proof. |
| Worker registry | `.devad/manager/WORKERS.md` | Human-readable list of lanes, chat IDs, worktrees, ownership, status. |
| Queue | `.devad/manager/QUEUE.md` | Ordered lane queue with owner, status, next action, and blocker. |
| Limits | `.devad/manager/LIMITS.md` | Focus, runtime, proof-failure, chat-read, and watchdog budgets. |
| Owner wait | `.devad/manager/OWNER_WAIT.md` | One-hour owner decision window and default safe verdict. |
| Handoff monitor | `.devad/manager/HANDOFF_MONITOR.md` | Bounded pickup monitor scope, cadence, expiry, and stop rule. |
| Heartbeat state | `.devad/manager/HEARTBEAT.md` | Optional, versioned, expiring monitoring state. |
| Handoff index | `.devad/manager/HANDOFF_INDEX.md` | Compact manager pickup queue from worker handoffs. |
| Deploy gate | `.devad/manager/DEPLOY_GATE.md` or worker `DEPLOY_GATE.md` | Exact-SHA deploy approval and blockers. |
| Decisions | `.devad/manager/DECISIONS.md` | User decisions, waivers, merge approvals, branch choices. |
| Answered decisions | `.devad/manager/ANSWERED_DECISIONS.md` | Reusable owner answers that managers/workers must not ask again. |
| Tool lessons | `.devad/manager/TOOL_LESSONS.md` | Known-good and known-bad Chrome, OpenCode, thread-tool, MCP, browser, and connector routes. |
| Risks | `.devad/manager/RISKS.md` | Open proof, merge, security, deploy, or ownership risks. |
| Pass logs | `.devad/manager/passes/YYYY-MM-DD-HHMM-<slug>.md` | Compact manager pass summaries only. |
| Manager handovers | `.devad/manager/handoffs/YYYY-MM-DD-HHMM-manager-handoff.md` | Fresh-manager launch artifact when focus risk is high. |
| Commit docs | `.devad/docs/YYYY-MM-DD-<lane>-commit-<shortsha>.md` | Required after each commit before push/deploy. |
| Worker packets | `.devad/manager/workers/<lane>/` | One folder per worker lane. |

## Recommended Tree

```text
.devad/
  X9.md
  ACTIVE.md
  manager/
    MISSION.md
    CENTRAL_FACTS.md
    MISSION_LOCK.md
    LOCAL_WORK_LEDGER.md
    CURRENT.md
    TOP_MANAGER.md
    MODEL_POLICY.md
    TRUTH_LOCK.md
    WORKERS.md
    QUEUE.md
    LIMITS.md
    OWNER_WAIT.md
    HANDOFF_MONITOR.md
    HANDOFF_INDEX.md
    HEARTBEAT.md
    DEPLOY_GATE.md
    DECISIONS.md
    ANSWERED_DECISIONS.md
    TOOL_LESSONS.md
    RISKS.md
    handoffs/
    passes/
    workers/
      <lane>/
        MANIFEST.md
        STATUS.md
        TASK.md
        LEDGER.md
        HANDOFFS.md
        DEPLOY_GATE.md
        proof/
  docs/
    YYYY-MM-DD-<lane>-commit-<shortsha>.md
```

## Chat-Only State

Keep only temporary reasoning, short user-facing status, and one next approved action in chat. Do not keep worker ownership, branch/base SHA, proof status, merge order, heartbeat instructions, or acceptance criteria only in chat.

Do not keep model choice only in chat. X9 model policy belongs in
`.devad/manager/MODEL_POLICY.md` and requires the role matrix from
`references/model-policy.md` with `xhigh` / extra high thinking for Top
Manager, Sub Manager, Worker, CHUNK, and SIDE Codex threads.

Do not keep active lane, source branch, deploy branch, v105 role, target SHA,
finish line, blocker, or exact next action only in chat. These belong in
`CENTRAL_FACTS.md` and `MISSION_LOCK.md` so every pass can reread a small truth
block before touching long handoffs.

Do not keep local dirty/untracked/source-only/not-live work only in chat or old
handoffs. This belongs in `LOCAL_WORK_LEDGER.md`, especially before source
push, v105 bridge, deploy, or done claims.

Do not keep reusable owner answers only in chat. If the owner answers a question
that can come up again, write it to `ANSWERED_DECISIONS.md`.

Do not keep repeated tool lessons only in chat. If Chrome profile, browser
proof, OpenCode SIDE, thread tools, MCP, or a connector fails or needs a special
route, write it to `TOOL_LESSONS.md`.

## Top Non-Chat State

When using Top Manager, chat state is never authority and thread history is
never an input. Top Manager reads only `.md` files listed in
`non-chat-top-manager.md` and writes only manager-control `.md` files.

If a needed fact exists only in chat, write:

```text
MISSING_MD:<lane>:<fact>
```

Sub Manager must then update `CENTRAL_FACTS.md`, `MISSION_LOCK.md`,
`ANSWERED_DECISIONS.md`, `TOOL_LESSONS.md`, `CURRENT.md`, `QUEUE.md`,
`LOCAL_WORK_LEDGER.md`, `HANDOFF_INDEX.md`, worker `STATUS.md`, worker
`HANDOFFS.md`, or a manager handover before the Top
Manager decides.

## Handover State

When a manager thread becomes long-running or high-risk, write a compact
handover under `.devad/manager/handoffs/`. Treat the handover as a launch
artifact for a fresh manager, not as a replacement for `WORKERS.md`,
`HANDOFF_INDEX.md`, worker `STATUS.md`, or worker `HANDOFFS.md`.

If `$devad-memory` is used, store only a compact memory digest path in the
handover. The memory digest is helpful context; repo truth, worker `STATUS.md`,
and worker handoffs remain primary.

## Refresh Rule

Every manager pass refreshes state from git and disk before interpreting worker reports:

```powershell
$repo = '<project-root>'
git -C $repo status --short --branch
git -C $repo rev-parse HEAD
git -C $repo branch --show-current
git -C $repo rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git -C $repo worktree list
git -C $repo remote -v
git -C $repo diff --name-only
git -C $repo ls-files -o --exclude-standard
```

Trust git, source, tests, browser proof, and explicit user direction over old manager state.

Before choosing a next action, read:

```text
.devad/manager/CENTRAL_FACTS.md
.devad/manager/MISSION_LOCK.md
.devad/manager/ANSWERED_DECISIONS.md
.devad/manager/TOOL_LESSONS.md
.devad/manager/LOCAL_WORK_LEDGER.md
```

If either file is missing, stale, vague, or conflicts with git/runtime truth,
repair the files or stop with the exact mismatch label before reading long
handoffs.
