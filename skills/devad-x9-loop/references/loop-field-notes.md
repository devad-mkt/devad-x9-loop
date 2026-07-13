# Loop Field Notes For X9 Manager

Use this reference when the user says the loop is weak, a manager is losing
focus, a worker keeps patching without progress, `/goal` is looping, or the
team wants multi-day unattended work.

## Source Cleanup

The user's local extraction files agree on the main content, but one OCR result
has errors.

| Source | Use | Notes |
| --- | --- | --- |
| `ocr-result.md` legacy extraction | primary | Cleanest Markdown extraction. |
| `LOOPS.md` legacy attachment | primary backup | Same content with minor spacing issues. |
| `HL7Svy2XYAAdouZ.txt` legacy extraction | secondary | Mostly correct plain text. |
| `ParsedResult.txt` legacy extraction | avoid as source | OCR changed Roman numerals and spaced filenames. |

Treat the attribution from X/trending as unverified unless separately checked.
Use the ideas as loop design notes, not as proof of authorship.

## Corrected Rule List

1. Write the loop, not the prompt.
2. Separate the roles.
3. Negotiate the contract first.
4. Write to disk, not to context.
5. Let the loop restart.
6. Score the subjective.
7. Read the traces.
8. Delete the harness.
9. The bottleneck always moves.

Correct file names from the extraction:

```text
feature_list.json
progress.md
contract.md
log.md
```

## What This Means For X9

| Field note | X9 manager rule |
| --- | --- |
| Loop, not prompt | Use a repeatable cycle: truth -> contract -> work -> eval -> handoff -> pickup. |
| Separate roles | Manager plans/routes, worker generates, evaluator verifies. Do not let a worker grade itself as final PASS. |
| Contract first | For high-risk lanes, create `CONTRACT.md` before app-code work. |
| Disk state | Durable files beat chat: manager state plus worker packet files. |
| Restart | After repeated drift or same-method failure, restart lane from clean base and salvage only proven hunks. |
| Score subjective | For UI/taste, use a written rubric before judging. |
| Read traces | Debug loops by finding where judgment diverged, not by rerunning blindly. |
| Delete harness | Remove old heartbeat/polling/broad scan rules when they become overhead. |
| Bottleneck moves | Track current bottleneck: planning, proof, merge, taste, deploy, or user decision. |

## Weak Spots In Our Current Loop

| Weak spot | Symptom | Fix |
| --- | --- | --- |
| No formal contract | Workers ask "what next" or claim broad progress. | Add `CONTRACT.md` for high-risk lanes. |
| Worker self-grading | Worker says PASS from its own tests. | Treat as `CLAIMED_PASS` until manager/evaluator checks. |
| Chat as state | Long chat answers hide important state. | Store state in `.devad`; chat only reports path/result. |
| Retry loops | Browser/proof keeps retrying same method. | After two failures: switch method, narrow scope, or block. |
| No outside challenge | Long-running Codex claims blocker from its own tired context. | Use packet-only GLM/Kimi sidecar before high-risk blocker. |
| No restart policy | Worker patches around bad structure. | Use `RESTART_LANE` from clean base when drift is cheaper than repair. |
| No trace audit | Token burn grows without knowing why. | Write `TRACE_NOTES.md` for repeated failures or token burn. |
| Harness bloat | More rules, more overhead, less focus. | Run `HARNESS_PRUNE` after each major manager phase. |
| Top Manager reads chat | The highest-level planner inherits all old drift. | Use Top Manager: `.md` only, 0% thread reads. |
| No hard budgets | Managers keep going until quality drops. | Add `LIMITS.md` and handover when budget is spent. |
| Unknown process state | Dev servers/proof loops burn time invisibly. | Use `WATCHDOG_CHECK` then write result to `.md`. |

## Upgraded X9 Loop

Use this loop for long-running or high-risk work:

```text
1. Truth lock
2. Top-manager `.md` plan
3. Planner packet
4. Contract
5. Generator work
6. Evaluator review
7. Sidecar challenge before high-risk blocker
8. Manager pickup
9. Restart / continue / block / merge-review
10. Watchdog / cleanup candidate
11. Harness prune
```

### 1. Truth Lock

Refresh repo path, branch, HEAD, dirty files, worktrees, remote SHAs, active
workers, and stale `.devad/ACTIVE.md` state before routing.

### 2. Top Manager `.md` Plan

Use `non-chat-top-manager.md` when Top Manager exists. It reads only durable
`.md` files and writes `TOP_MANAGER.md`, `QUEUE.md`, `DECISIONS.md`, `RISKS.md`,
or a pass note. It does not read thread chat, worker chat, or old manager chat.

If it needs chat to decide, stop with `MISSING_MD:<lane>:<fact>` and assign the
Sub Manager to write that fact into `.devad`.

### 3. Planner Packet

Manager writes or updates worker packet files. Keep scope small.

Required worker files:

```text
.devad/manager/workers/<lane>/MANIFEST.md
.devad/manager/workers/<lane>/STATUS.md
.devad/manager/workers/<lane>/TASK.md
.devad/manager/workers/<lane>/CONTRACT.md
.devad/manager/workers/<lane>/LEDGER.md
.devad/manager/workers/<lane>/HANDOFFS.md
.devad/manager/workers/<lane>/proof/
```

`CONTRACT.md` may be skipped only for tiny docs-only or read-only lanes. If
skipped, `TASK.md` must say `Contract: skipped` and why.

### 4. Contract

Before app-code work, define testable assertions:

- scope and non-goals,
- allowed files and forbidden files,
- source evidence required,
- proof required,
- acceptance criteria,
- subjective rubric if UI/taste is involved,
- stop conditions,
- manager/evaluator review needed.

For normal lanes, 8-15 assertions is enough. For high-risk UI, billing, source
adoption, or merge work, 15-30 assertions is acceptable.

### 5. Generator Work

Worker implements only the contracted slice. Worker updates `LEDGER.md` while
working and `STATUS.md` plus `HANDOFFS.md` before final chat.

### 6. Evaluator Review

Use an independent evaluator when risk is high:

| Risk | Evaluator |
| --- | --- |
| Tiny docs-only | Manager quick check |
| Normal code | Manager validates packet/diff/tests |
| UI/browser | Separate evaluator or manager browser proof |
| Billing/security/deploy | Separate evaluator preferred |
| Merge-review | Fresh manager/evaluator preferred |

Evaluator starts from the assumption that the work is broken until proof says
otherwise.

### 7. Sidecar Challenge Before Blocker

For high-risk or long-running lanes, use SIDE before claiming a true blocker
when safe. Send GLM/Kimi a saved packet only, not the
full chat. Ask for:

- whether the blocker is real,
- smallest safe next step,
- proof that would change the decision,
- continue vs restart vs user decision.

SIDE output is advice only. Manager records the decision in `.devad`.

### 8. Manager Pickup

Manager reads `HANDOFF_INDEX.md`, current `STATUS.md`, and only
changed/actionable `HANDOFFS.md`.
Manager does not read full worker chats unless `STATUS.md` or the handoff is
missing or contradictory.

### 9. Restart / Continue / Block

Use these manager decisions:

```text
REQUEST_SUB_MANAGER_REFRESH:<lane|all>
REQUEST_MD_HANDOFF:<lane>:<missing fact>
APPROVE_CONTRACT:<lane>
APPROVE_GENERATOR_START:<lane>
APPROVE_EVALUATOR_REVIEW:<lane>
APPROVE_SIDECAR_CHALLENGE:<lane>:<topic>
APPROVE_WORKER_CONTINUE:<lane>:<slice>
RESTART_LANE:<lane>:<reason>
BLOCKED_NEED_USER:<decision>
BLOCKED_NEED_EVIDENCE:<evidence>
SIDECAR_UNAVAILABLE:<lane>:<reason>
SUB_MANAGER_HANDOVER:<reason>
WATCHDOG_CHECK:<scope>
CLEANUP_CANDIDATE:<lane>
HARNESS_PRUNE:<scope>
NO_ACTION
```

Restart when:

- same proof method failed twice,
- worker violated scope,
- branch/base is wrong,
- scaffold is broad/fake,
- shared-file overlap is messy,
- patching is more expensive than clean port.

Restart does not mean losing work. Salvage only proven hunks, source evidence,
tests, and docs.

### 10. Watchdog / Cleanup Candidate

Use `WATCHDOG_CHECK:<scope>` when dev servers, proof loops, queue monitors, or
long-running commands may be stale or burning tokens. Sub Manager performs
read-only checks and writes the result to `.md`.

Use `CLEANUP_CANDIDATE:<lane>` only after proof is verified or the lane is
abandoned. Do not delete, clean, stop, reset, or remove branches without a
separate user-approved cleanup action.

### 11. Harness Prune

After a major phase, delete or retire overhead:

- expired heartbeat instructions,
- broad observe/poll loops,
- stale worker packets,
- old source assumptions,
- duplicate state files,
- model ladders or fan-out that no longer help,
- rules that only repeat stronger current rules.

## Trace Reading

When token burn, focus drift, or repeated failure appears, do not guess. Write a
small trace note:

```text
.devad/manager/traces/YYYY-MM-DD-HHMM-<lane>-trace.md
```

Include:

```md
# Trace Note: <lane>

| Point | What happened | Expected | Divergence | Fix |
| --- | --- | --- | --- | --- |

Decision:
APPROVE_WORKER_CONTINUE | RESTART_LANE | BLOCKED_NEED_USER | HARNESS_PRUNE
```

Keep trace notes short. They should explain the exact moment the loop went
wrong.

## Caveman Chat Compatibility

This reference does not change the Caveman chat rule. Visible chat/status stays
short. Contracts, traces, proof notes, and handoffs stay complete and technical.
