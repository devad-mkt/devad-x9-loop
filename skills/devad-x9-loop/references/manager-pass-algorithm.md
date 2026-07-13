# Manager Pass Algorithm

Run a manager pass as active verification, not summarization.

## Steps

1. Select role for this pass:
   - `Thinx` / `Top Manager` / `TOP_NON_CHAT_MANAGER`: read only durable `.md` manager state; do not read
     thread chats, worker chats, old manager chat, or conversation memory. Use
     `references/non-chat-top-manager.md`.
   - `Linx` / `Sub Manager` / `SUB_MANAGER_BRIDGE`: read newest user message, verify Workers, update
     `.md` state, and read worker chat only if a handoff is missing, stale, or
     contradictory.
   - `Worker`: implementation role; do not use this manager pass except to
     validate the Worker packet.
   - `Worker Reader`: hidden Thinx subagent for mechanical exact-file
     extraction only; no visible task, decisions, approvals, code, routing,
     or mutation.
   - `NORMAL_MANAGER`: use the default manager rules below.
Before step 2, enforce `references/model-policy-v3.md` and MODEL_STATE.md.
Linx requires `gpt-5.6 high`; normal Workers use `gpt-5.6 high` and xhigh when
the owner explicitly asks extra high; Thinx uses `gpt-5.6 xhigh` for normal
planning/review and ultra for one very-hard pass, then returns to xhigh.
1a. Acquire `.devad/manager/MANAGER_PASS_LOCK.md`. If another unexpired pass
    exists, return `SKIP_ACTIVE_MANAGER_PASS`. A callback pass stops when a
    newer owner turn changes scope. Release the lock before receiver execution
    and before final chat.
2. Read the newest user message and attachments. Before summarizing, follow
   `references/owner-context-and-attachments.md`: preserve the exact message,
   stabilize/hash attachments, inspect required images/screenshots, and update
   owner-input/INDEX.md. A summary alone is not context transfer.
   Skip this step only for `Top Manager`; its current override must
   already be in `.devad/manager/CURRENT.md` and the active owner-input
   bundle.
2a. Classify the owner turn before answering:
    - `ROUTINE_BRIDGE`: Linx may report exact durable status.
    - `JUDGMENT_REQUIRED`: route exact input/current evidence to locked Thinx;
      Linx does not answer the judgment.
    - `WORKER_REQUIRED`: route a Worker; Linx never takes over implementation.
3. Read `.devad/manager/CENTRAL_FACTS.md` and
   `.devad/manager/MISSION_LOCK.md`, then read
   `.devad/manager/ANSWERED_DECISIONS.md`,
   `.devad/manager/TOOL_LESSONS.md`, and
   `.devad/manager/LOCAL_WORK_LEDGER.md`, then the active
   `.devad/manager/owner-input/INDEX.md` row before reading long handoffs or choosing
   "what next". If the files are missing, stale, vague, too long, or conflict
   with current repo/branch/HEAD/target SHA/deploy branch/finish line, stop with
   `MISSING_CENTRAL_FACTS`, `MISSING_MISSION_LOCK`,
   `MISSING_LOCAL_WORK_LEDGER`, `STALE_CENTRAL_FACTS`,
   `STALE_LOCAL_WORK_LEDGER`, `BRANCH_LOCK_MISMATCH`, or
   `MISSION_LOCK_MISMATCH`. For Top Manager, missing fields become
   `MISSING_MD:<lane>:<fact>` or `MISSING_CENTRAL_FACT:<field>`; do not read
   chat to recover them.
3a. Before sending to Thinx, Worker, Reader, CHUNK, or SIDE, require the exact
    owner request identity, attachment manifest identity, visual context
    identity, and required attachment IDs. Require OWNER_CONTEXT_RECEIPT: PASS
    from the receiver before accepting its result.
4. Refresh repo truth with the bundled Python runtime unless acting as
   `Top Manager`:

```powershell
$py = Join-Path $HOME '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py <skill>\scripts\check_x9_manager_state.py --repo <repo>
```

5. Refresh local work ledger unless acting as `Top Manager`:

```powershell
& $py <skill>\scripts\build_local_work_ledger.py --repo <repo> --write
```

6. Collect worker handoffs unless acting as `Top Manager`:

```powershell
& $py <skill>\scripts\collect_worker_handoffs.py --repo <repo> --write-index
```

7. Compare git truth with `CENTRAL_FACTS.md`, `MISSION_LOCK.md`,
   `LOCAL_WORK_LEDGER.md`, `.devad/ACTIVE.md`,
   `.devad/manager/TRUTH_LOCK.md`, `HANDOFF_INDEX.md`, callback/event state,
   worker `STATUS.md`, and worker packets. For `Top Manager`,
   compare only the `.md` files already on disk and stop with `MISSING_MD` if a
   fact is absent.
7a. Before asking the owner any question, search `ANSWERED_DECISIONS.md`,
    `DECISIONS.md`, `CENTRAL_FACTS.md`, `MISSION_LOCK.md`, active Worker
    `STATUS.md`, and top `CURRENT_STATUS`. If the answer exists, use it. If it
    exists only in chat, write it into `.devad` first.
7b. Run `DREAM_PASS` before choosing the next step: propose only from durable
    `.md` files plus current git/runtime truth, not from long chat history.
7c. Run `DISTILL_PASS` after every Worker pass: save new current facts to
    `CENTRAL_FACTS.md`, owner answers to `ANSWERED_DECISIONS.md`, tool routes
    to `TOOL_LESSONS.md`, and local-only work state to `LOCAL_WORK_LEDGER.md`.
8. Read only the `Detail links` from `CENTRAL_FACTS.md` that are needed for the
   exact next action. Do not scan broad old reports to rediscover active task
   facts.
9. Classify each worker:

```text
NOT_STARTED
WORKING
IDLE
BLOCKED
FAILED
DRIFTING
CLAIMED_PASS
VERIFIED_PASS
REJECTED
SOFT_BLOCKER
HARD_BLOCKER
OWNER_DECISION
```

10. Inspect worker worktrees read-only unless acting as `Top Manager`:

```powershell
git -C <worktree> status --short --branch
git -C <worktree> rev-parse HEAD
git -C <worktree> diff --name-only
git -C <worktree> diff --check
```

11. Validate each actionable worker packet unless acting as `Top Manager`:

```powershell
& $py <skill>\scripts\validate_worker_packet.py --packet <packet> --worktree <worktree>
```

12. Check overlap across workers. If two workers changed the same file, stop and assign one owner.
13. Check contract state for high-risk lanes. If implementation started without
   `CONTRACT.md` or an explicit `Contract: skipped` reason, mark the lane
   `BLOCKED_NEED_CONTRACT`.
14. Enforce local work authority. If `LOCAL_WORK_LEDGER.md` shows active-lane
    local work as present, no source push, deploy readiness, live deploy, or
    done claim may rely on GitHub/remote alone. The next action must classify
    local work, review exact diffs, or write why it is intentionally skipped.
15. Enforce current-status authority. Use worker `STATUS.md` and the top
   `CURRENT_STATUS` block in `HANDOFFS.md`. Older handoff sections are history
   only. If current status is missing or contradictory, mark the lane
   `MISSING_CURRENT_STATUS` or `PARTIAL`, not `PASS`.
16. Enforce role separation. A worker can report `CLAIMED_PASS`; only a manager
   or separate evaluator can mark `VERIFIED_PASS`.
16a. Enforce Linx non-implementation. If Linx created product/preview/test/proof
     artifacts or took over Worker work, mark `HANDOVER_REQUIRED`, preserve the
     files as untrusted local work, and route independent review.
17. Enforce owner wait windows from
   `references/owner-wait-and-handoff-monitor.md`. If `OWNER_WAIT.md` is
   active and the deadline has not passed, do not route new implementation
   orders. If the deadline passed, check the newest owner message, refresh
   truth, do bounded safe research, and choose the safest honest verdict.
18. Enforce push/deploy gates from `references/status-and-deploy-gates.md`.
   `CLAIMED_PASS`, `Source push: PASS`, and `Deploy readiness: PASS` are
   separate. No deploy starts without `DEPLOY_GATE.md` and
   `DEPLOY_APPROVED:<sha>` for the exact commit. No multi-commit or multi-lane
   branch push without owner approval or manager review.
19. Enforce the shared contract's finite C1/C2 security and attestation gate
   through `references/commit-security-docs-gate.md`. Do not restate or weaken
   that contract in a packet.
19a. Enforce `devad-x9/references/destructive-action-guard.md` before routing
    mutation. A destructive final step becomes `OWNER_DECISION_REQUIRED` plus
    a verified `DESTRUCTIVE_REQUEST.md`; it is never executed by Codex. Reject
    chat approval tokens, manager waivers, automation, or helper claims as an
    execution boundary.
20. Enforce outbound-fetch security review. For scraping, URL import, webhooks,
   RSS, browser automation, n8n callbacks, provider fetch, or server-side URL
   work, require security review before and after code; otherwise deploy
   readiness is `BLOCKED`.
21. Enforce `LIMITS.md` and lane contract budgets. If max runtime, same-method
    failures, active-lane count, or chat-read budget is exceeded, choose
    `SUB_MANAGER_HANDOVER`, `RESTART_LANE`, `WATCHDOG_CHECK`, or
    `BLOCKED_NEED_USER`; do not keep routing from the same tired context.
22. Enforce proof-loop budget. If a lane failed the same browser, API, CLI, MCP, or source-proof method twice without new evidence, require a different method, a smaller proof target, a `RESTART_LANE`, or a `PARTIAL`/`BLOCKED` handoff.
22a. Enforce tool lessons. Before repeating a failed Chrome profile, browser
     proof, OpenCode SIDE, thread-tool, MCP, connector, or Dokploy route, read
     `TOOL_LESSONS.md`. After a repeated failure or fallback success, update the
    lesson before routing another attempt.
22b. Before accepting any Thinx decision, run the verified-read gate in
     `references/reader-helper-and-read-receipt.md`. Validate the request and
     decision with `validate_thinx_read_receipt.py`. A prompt that merely lists
     files is not evidence that Thinx read them.
22c. If Thinx compacts context after receiving the request but before a valid
     read receipt, reject the decision and restart the same locked Thinx with
     the durable request. Context compaction is not permission to create or
     replace Thinx. Replacement requires `REPLACE_THINX_OK:<reason>` from the
     owner.
23. Before claiming a high-risk or long-running lane is truly `BLOCKED`, run a
    packet-only SIDE challenge if safe and available. Use
    `references/sidecar-challenge-worker.md`. Record the packet, output, and
    decision. If SIDE is unsafe/unavailable, record why.
24. Treat a blocker as `SOFT_BLOCKER` while any safe fallback remains:
    Top Manager file-only review, SIDE packet-only review, local docs/source
    search, read-only process/proof check, or smaller worker proof. Do not ask
    the owner until the blocker is `HARD_BLOCKER` or `OWNER_DECISION`.
25. Preparation and validation do not consume the bounded action. If current
    truth proves one exact safe continuation and it needs no owner decision,
    perform or dispatch it before final chat. A report containing only
    `Next: <safe action>` is `NEXT_ONLY_FORBIDDEN`. Stop only for an exact
    safety/identity/resource/lock/transport blocker or real owner decision.
26. If a Worker or Thinx was dispatched, record exact callback identity and
    require the receiver to write its durable receipt, then send `EVENT_READY`
    to the same registered Linx task. Recurring 15/19-minute pickup is
    forbidden. On bounded delivery failure record `MANAGER_WAKE_FAILED`.
27. Verify claims from primary evidence:

| Claim | Authority |
| --- | --- |
| Files changed | `git status`, `git diff --name-only`, `git diff -U0` |
| Tests pass | exact command result |
| Browser/UI works | screenshot, DOM/ARIA, console/log status |
| Backend works | route/controller/service/test/database proof |
| API/CLI/MCP works | callable proof or explicit dry-run contract |
| Adoption parity | source/local matrix and missing disclosure |
| Security clean | secret scan and no raw sensitive data |

27. Run a watchdog check request when process/proof state is unknown. Top
    manager writes `WATCHDOG_CHECK:<scope>` only; Sub Manager may perform
    read-only process checks and write results back to `.md`.
28. Read traces when repeated failure or token burn appears. Write a compact
    `.devad/manager/traces/<timestamp>-<lane>-trace.md` only when it explains a
    real divergence.
29. Send a correction only for blocker, completion, drift, unsafe overlap, missing proof, stale state, or a direct user decision.
30. If safe work exists, save or update central facts, mission lock, local work
    ledger, the queue,
    worker packet, handoff index, top-manager plan, owner wait file, callback
    receipt, or blocker. Do not end with advice only.
31. If handover triggers are present, run
    `references/collaborative-linx-handover.md`: freeze implementation,
    collect status-only Worker inventories, build the owner scope matrix,
    obtain a plan-only replacement plan, review coverage, and transfer with
    `LINX_ACTIVATION_OK`. Only the activated new Linx may restart bounded
    routing. Receiver callbacks continue work; recurring pickup remains
    forbidden.
32. Approve only one next action:

```text
REQUEST_SUB_MANAGER_REFRESH:<lane|all>
REQUEST_MD_HANDOFF:<lane>:<missing fact>
REQUEST_LOCAL_WORK_LEDGER:<lane>
CLASSIFY_LOCAL_WORK:<lane>
REQUEST_ANSWERED_DECISION:<field>
REQUEST_TOOL_LESSON:<tool>
ARM_DIRECT_CALLBACK:<target_task_id>:<dispatch_id>:<packet_sha256>
OWNER_WAIT_START:<deadline>:<default_verdict>
OWNER_WAIT_EXPIRED:<decision>
APPROVE_WORKER_CONTINUE:<lane>:<slice>
APPROVE_CONTRACT:<lane>
APPROVE_GENERATOR_START:<lane>
APPROVE_EVALUATOR_REVIEW:<lane>
APPROVE_SIDECAR_CHALLENGE:<lane>:<topic>
SOFT_BLOCKER_ROUTE:<lane>:<top|side|read_only|smaller_proof>
APPROVE_REVIEW_DIFF:<lane>
APPROVE_PORT:<lane> -> <target>
RESTART_LANE:<lane>:<reason>
HARD_BLOCKER:<lane>:<reason>
OWNER_DECISION_REQUIRED:<lane>:<decision>
OWNER_RUN_DESTRUCTIVE_REQUEST:<lane>:<request-path>
BLOCKED_NEED_USER:<decision>
BLOCKED_NEED_EVIDENCE:<evidence>
BLOCKED_NEED_CONTRACT:<lane>
SIDECAR_UNAVAILABLE:<lane>:<reason>
REPEATED_OWNER_QUESTION:<field>
REPEATED_TOOL_FAILURE:<tool>
SUB_MANAGER_HANDOVER:<reason>
WATCHDOG_CHECK:<scope>
CLEANUP_CANDIDATE:<lane>
HARNESS_PRUNE:<scope>
NO_ACTION
```

Every pass with active or just-routed Workers must also record one final state:

```text
CALLBACK_ARMED
OWNER_WAIT_ACTIVE
WORKER_SENT_CALLBACK_ARMED
HARD_BLOCKED
OWNER_DECISION_REQUIRED
NO_ACTION_VERIFIED
```

## Status Rules

| Status | Meaning |
| --- | --- |
| `PASS` | Manager verified packet, scope, proof, and no stale or unsafe overlap. |
| `PARTIAL` | Useful work exists, but proof, scope, or parity is incomplete. |
| `BLOCKED` | Missing evidence, user decision, credentials, branch repair, or stale-state repair blocks safe progress. |
| `SOFT_BLOCKER` | Progress paused, but safe fallback checks still exist. Do not ask owner yet. |
| `HARD_BLOCKER` | No safe fallback remains without owner, secret, permission, destructive action, or data/deploy risk. |
| `OWNER_DECISION` | More than one safe path exists and owner must choose risk, scope, money, deploy, or priority. |
| `CALLBACK_ARMED` | Receiver has exact identity for one direct callback to Linx. |
| `WORKER_SENT_CALLBACK_ARMED` | Worker got orders and verified direct pickup is armed. |
| `MANAGER_DRIFTING` | Manager skipped truth lock, accepted unverified PASS, or only summarized without next action. |
| `WORKER_DRIFTING` | Worker deviated from allowed files, source evidence, branch/base, or task. |
| `HANDOVER_REQUIRED` | Manager state is too broad, stale, long-running, or high-risk for further routing in the same chat. |
| `MISSING_CURRENT_STATUS` | Worker lacks `STATUS.md` or top `CURRENT_STATUS`; old PASS text cannot be trusted. |
| `MISSING_CENTRAL_FACTS` | Central facts file is absent, stale, or too vague for a what-next decision. |
| `MISSING_LOCAL_WORK_LEDGER` | Local work ledger is absent/stale while git has local dirty or untracked work. |
| `LOCAL_ONLY_WORK` | Active lane has local-only work that must be classified before push/deploy/done. |
| `MISSION_LOCK_MISMATCH` | Repo, branch, target SHA, deploy target, or finish line conflicts with the lock. |
| `FINISH_LINE_NOT_REACHED` | The task required push, deploy, or live proof but current evidence stops earlier. |

## Merge Discipline

- Merge or port one lane at a time.
- If shared files changed, freeze all lanes touching those files until reviewed.
- Reject broad copy/paste merges.
- Reject workers that edited outside scope until the worker explains or corrects it.
- Worker `CLAIMED_PASS` is never deploy, merge, or production PASS.
- Worker `VERIFIED_PASS`, source push, deploy readiness, and live deploy are
  different gates.
- Do not push a branch that is ahead by more than one commit or contains
  multi-lane work without `PUSH_APPROVED_BY_OWNER` or manager review.
- Do not deploy without `DEPLOY_GATE.md` and `DEPLOY_APPROVED:<sha>`.
- Do not push/deploy a commit until the shared contract's security and
  attestation gates pass for the exact source SHA.
