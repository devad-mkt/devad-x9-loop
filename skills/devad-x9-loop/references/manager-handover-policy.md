# Manager Handover Policy

Use handover when a manager thread is still useful but no longer the best place
to make high-risk routing, merge-review, or next-worker decisions.

This applies most often to Sub Manager. Top Manager should stay stable because it reads
only `.md` state; Sub Manager can be
replaced after a long run, many worker chat reads, or repeated proof routing.

## Triggers

Start a handover before continuing when any trigger is true:

- more than six worker lanes exist,
- two or more active user direction changes changed the mission,
- `.devad/ACTIVE.md` or `TRUTH_LOCK.md` is stale,
- the manager accepted a worker claim without durable proof,
- the manager is about to do merge review after a long run,
- repeated context compaction happened in Linx/Sub Manager,
- the manager produced advice without routing safe next work,
- a proof loop retried the same method twice without new evidence,
- Sub Manager read worker chats more than its focus budget,
- Sub Manager has routed for more than 90 continuous minutes,
- Top Manager reports `MISSING_MD` and the current Sub Manager cannot
  write a clean missing-fact handoff quickly.
- Linx gave one incorrect owner-facing truth, acceptance, implemented, or
  deployed answer that required correction.
- Linx performed Worker implementation or generated product/preview artifacts.
- two manager/heartbeat turns overlapped or the pass lock was bypassed.
- a judgment was made while the required model/effort was not tool-enforced.

Any trigger above sets `HANDOVER_REQUIRED`. Use
`collaborative-linx-handover.md`. The old Linx may collect `STATUS_ONLY`
Worker inventories, repair durable truth, create one plan-only replacement,
and review handover coverage. It cannot issue implementation orders or make
new product judgment during transition.

Thinx is thread-locked. Context compaction, a missed file, or a failed receipt
causes a durable context reset inside the same Thinx. Do not replace, fork, or
create another Thinx unless the owner writes `REPLACE_THINX_OK:<reason>`.

## Required Artifact

Write one compact handover:

```text
.devad/manager/handoffs/YYYY-MM-DD-HHMM-manager-handoff.md
```

It must include:

- repo, branch, HEAD, upstream, dirty tracked/untracked counts,
- latest user override,
- active, queued, blocked, rejected, and verified lanes,
- worker thread IDs, worktrees, handoff paths, and latest statuses,
- worker `STATUS.md` paths and current `CURRENT_STATUS` gate values,
- Top Manager status: `ACTIVE`, `MISSING_MD`, or `NOT_USED`,
- Sub Manager status and focus-budget state,
- owner wait / handoff monitor state,
- changed/shared files and owners,
- proof status by lane,
- exact blockers and user decisions needed,
- next safe manager action,
- what not to do,
- whether `.devad/ACTIVE.md` is fresh or stale,
- whether a `$devad-memory` digest exists and its path.
- complete managed-Worker inventory coverage and missing replies,
- `OWNER_SCOPE_MATRIX` with `IMPLEMENT`, `REJECTED`, `PAUSED`, or `UNKNOWN`,
- every known local/uncommitted/unpushed item and its owner,
- new Linx plan path/hash, old Linx final review, and activation state.

## Durable Memory Layer

Use `$devad-memory` only as a compact digest layer, not as authority.

When the handover is caused by focus drift, long context, or a new manager
thread, run the Devad memory workflow against the manager thread/session if the
repo has `.devad/memory` or the user provided a memory root. Extract only:

- mission and newest user override,
- worker lane table,
- decisions and rejected routes,
- proof gaps and blockers,
- next safe steps,
- do-not-repeat lessons.

Do not store raw chats, full transcripts, secrets, cookies, `.env`, provider
logs, private data, or screenshot dumps. Add the resulting memory topic/session
path to the manager handover. If memory setup is missing or too expensive, write
`Memory digest: skipped` with the reason.

## Fresh Manager Start Prompt

End the handover with a paste-ready prompt:

```md
Use $devad-x9-loop.

Start as the fresh Sub Manager bridge from:
<absolute handover path>

Read only:
1. the handover file,
2. `.devad/manager/HANDOFF_INDEX.md`,
3. `.devad/manager/WORKERS.md`,
4. `.devad/manager/QUEUE.md`,
5. `.devad/manager/TOP_MANAGER.md`,
6. `.devad/manager/OWNER_WAIT.md`,
7. `.devad/manager/HANDOFF_MONITOR.md`,
8. the listed active worker `STATUS.md` files,
9. the listed active worker `HANDOFFS.md` files,
10. the listed worker or manager `DEPLOY_GATE.md` files when deploy is in scope,
11. the listed memory digest path if present.

Start in `PLAN_ONLY`. Refresh repo truth with the bundled Python runtime, do
not trust old chat memory, do not start a heartbeat, and write one hashed plan
covering every owner-scope row and Worker inventory.
Read worker chats only if `STATUS.md` or a handoff is missing, stale, or
contradictory. If you read chat, write the fact into `.devad` so Top Manager
does not need chat.
```

## Completion Rule

After writing a handover, the old manager may only complete the collaborative
coverage review. It transfers execution only with
`LINX_ACTIVATION_OK:<new-thread-id>:<handover-sha256>:<plan-sha256>`, then
retires. The new Linx must refresh truth from disk before acting.

After a critical truth error, Linx implementation takeover, or overlapping
pass, the old manager may send status-only inventory requests and write/repair
handover facts. It must not continue judgment, implementation routing, or
artifact creation.

For a Top Manager handoff, do not pass a chat transcript. Pass only the
handover path and `.devad` state files listed in `non-chat-top-manager.md`.
