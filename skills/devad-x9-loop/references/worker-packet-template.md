# Worker Packet Template

Use one packet per Worker lane. Workers should read only their packet, explicit source evidence, and necessary repo code.

Official role names:

| Role | Meaning |
| --- | --- |
| `Worker` | One implementation chat for one contracted lane. |
| `CHUNK` | Tiny helper/swarm spawn owned by the Worker for one subtask. |
| `SIDE` | Packet-only GLM/Kimi plan and blocker reviewer. |

Worker/CHUNK profiles come from model-policy-v3.md and the exact task-class
benchmark. SIDE models are OpenCode GLM/Kimi, not Codex Worker threads.

For every nontrivial Worker, use worker-sidecar-context-bridge.md:

- PLAN_CHALLENGE once before first mutation;
- hidden gpt-5.6-luna medium builds the full durable task-context packet;
- both opencode-go/glm-5.2 and opencode-go/kimi-k2.7-code review it;
- BLOCKER_CHALLENGE reuses that packet before final BLOCKED;
- Worker verifies advice and remains the decision owner.

## Folder Shape

```text
.devad/manager/workers/<lane>/
  MANIFEST.md
  STATUS.md
  TASK.md
  CONTRACT.md
  LEDGER.md
  HANDOFFS.md
  DEPLOY_GATE.md   # only for deploy/live lanes
  proof/
```

## Required Central Facts

Every Worker packet must include or link to the current central facts:

```text
.devad/manager/CENTRAL_FACTS.md
.devad/manager/MISSION_LOCK.md
.devad/manager/LOCAL_WORK_LEDGER.md
```

The Worker must read both files before every "what next" move, before any
commit, and before any deploy/live-proof claim. If repo, worktree, branch, HEAD,
target SHA, deploy branch, v105 role, or required finish line conflicts with
the worker packet, stop with `MISSION_LOCK_MISMATCH`.

Before asking the owner or manager a question, the Worker must also read:

```text
.devad/manager/ANSWERED_DECISIONS.md
.devad/manager/DECISIONS.md
.devad/manager/TOOL_LESSONS.md
```

If the answer is already there, use it. If a tool route already failed there,
switch route or stop with a precise label instead of retrying.

The Worker must read `LOCAL_WORK_LEDGER.md` before push, deploy, done, or
"what next" claims. If it shows active-lane local work, classify it before
claiming remote/GitHub is complete truth.

## Required Owner Context

Every packet links the active owner-input bundle:

    OWNER_INPUT_ID: <id>
    OWNER_REQUEST: <path + sha256>
    ATTACHMENT_MANIFEST: <path + sha256>
    VISUAL_CONTEXT: <path + sha256>
    REQUIRED_ATTACHMENTS: <ids or NONE>

Worker validates OWNER_CONTEXT_RECEIPT before planning or mutation. Required
images/screenshots must be viewed as binaries or through an approved visual
Reader with spot-check. Summary-only transfer is BLOCKED.

## PERMISSION_MODE

Every implementation prompt must fill this block:

```md
PERMISSION_MODE:
- Owner-approved local actions: reads; isolated worktree setup; exact owned-file
  edits; focused tests; formatting; security checks; exact staging; scoped local
  commit; commit record; lane handoff.
- Manager-verified external facts: <fact + evidence + timestamp, or NONE>
- External actions this turn: NONE | <exact operation and target>
- Escalated tool requests: FORBIDDEN unless the exact external action above
  explicitly requires that route.
```

For `External actions this turn: NONE`, the Worker must not repeat network
preflight already supplied by the manager, set an escalated/unsandboxed tool
mode, or create an owner approval popup. If a default tool path fails, record
`TOOL_FAILED`, use the documented fallback, and continue local work that does
not depend on it. `waitingOnApproval` is not `OWNER_DECISION`. A stale local
tracking ref does not override a fresher timestamped manager live-remote fact.

## MANIFEST.md

```md
# Worker Manifest: <lane>

**Packet schema:** `X9-V2`
**Status:** PLANNED | ACTIVE | PARTIAL | BLOCKED | CLAIMED_PASS | VERIFIED_PASS | REJECTED | ABANDONED
**Worker chat:** <chat id or pending>
**Registered Linx task ID:** <task id>
**Registered Worker task ID:** <task id>
**Registered role:** WORKER
**Dispatch ID:** dsp-<uuid>
**Packet SHA-256:** <64 hex>
**Completion receipt:** <repository-relative path>
**Required model profile:** `<task-class profile from model-policy-v3.md>`
**Base tool model id:** `<host-supported identifier>`
**Required thinking:** `<selected effort>`
**Worktree:** `<worktree-root>\<lane>`
**Branch:** `<worker-branch>`
**Base SHA:** `<sha>`
**Target:** `<target branch>@<sha>`
**Manager packet version:** YYYY-MM-DD-HHMM
**Feature ID:** `<stable-slug>`
**Subfeature ID:** `<stable-slug>` | `NONE`
**Feature root:** `.devad/features/<feature-id>`
**Run ID:** `r-YYYYMMDD-NN`
**Artifact index:** `.devad/features/<feature-id>/refs/ARTIFACTS.md`
**Max runtime:** `<minutes or contract>`
**Max same-method proof failures:** 2

## Purpose

<one paragraph>

## Source Evidence

| Evidence | Path or URL | Required |
| --- | --- | --- |
| Source screenshot | `<path>` | yes/no |
| Source DOM/JSON | `<path>` | yes/no |
| Source route/code | `<path>` | yes/no |
| User decision | `<path>` | yes/no |

## Allowed Files

- `path/or/folder/**`

## Forbidden Files

- `.env`
- `storage/logs/**`
- `.devad/manager/**` except this packet
- shared files not explicitly listed

## Stop Conditions

- needs a forbidden/shared file,
- source evidence is missing,
- secrets or raw customer/provider/payment data would be exposed,
- live provider write, deploy, merge, reset, stash, clean, or destructive action is needed,
- tests or proof fail outside scope,
- the same proof method failed twice without new evidence,
- max runtime or focus budget is exceeded,
- branch/base SHA mismatch is detected.
```

## STATUS.md

`STATUS.md` is the current worker truth. Managers must not infer current status
from old `HANDOFFS.md` body text.

```md
# Worker Status: <lane>

CURRENT_STATUS:
- Lane: <lane>
- Updated: YYYY-MM-DD HH:mm Europe/Istanbul
- Scope: <one short scope>
- Lane status: PLANNED | ACTIVE | CLAIMED_PASS | VERIFIED_PASS | PARTIAL | BLOCKED | FAILED | REJECTED | ABANDONED
- Mission lock: PASS | BLOCKED
- Central facts: PASS | BLOCKED
- Local work: PASS | PARTIAL | BLOCKED
- Destructive guard: PASS | NOT_REQUIRED | OWNER_RUN_REQUIRED | BLOCKED
- Security review: PASS | PARTIAL | BLOCKED | NOT_REQUIRED
- Security precommit: PASS | BLOCKED | NOT_REQUIRED
- Post-commit docs: PASS | BLOCKED | NOT_REQUIRED | NOT_COMMITTED
- Source push: PASS | BLOCKED | NOT_REQUESTED
- Deploy readiness: PASS | BLOCKED | WAIVED_BY_OWNER | NOT_REQUESTED
- Live deploy: PASS | BLOCKED | NOT_REQUESTED
- Live proof: PASS | BLOCKED | NOT_REQUESTED
- Latest commit: <sha or none>
- Attestation commit: <sha or none>
- Exact next action: <one action>
- Must not do: <forbidden next action>

ISSUE_CARD:
| Item | Answer |
| --- | --- |
| Problem | <one simple line> |
| Cause | <one simple line> |
| Fix | <one simple line> |
| Proof | <one simple line> |
| Next | <one action> |
```

## DEPLOY_GATE.md

Required only when a lane wants deploy readiness or live deploy PASS.

```md
# Deploy Gate: <lane>

**Target SHA:** <sha>
**DEPLOY_APPROVED:** DEPLOY_APPROVED:<sha> | none
**Approved by:** owner | manager | none
**Updated:** YYYY-MM-DD HH:mm Europe/Istanbul

| Check | Status | Proof |
| --- | --- | --- |
| Security review for exact commit range | PASS | <path/command> |
| Local intended HEAD equals source remote HEAD | PASS | <path/command> |
| Sidecar/live dependencies ready or owner-waived | PASS | <path/decision> |
| Dokploy branch policy verified | PASS | <path/command> |
| Live proof plan exists | PASS | <path> |
| No stale PASS in handoff used as authority | PASS | STATUS.md |
```

If `DEPLOY_APPROVED:<sha>` is missing, deploy is blocked.

## TASK.md

```md
# Worker Task: <lane>

## Objective

<one vertical slice only>

## Execution Order

1. Confirm worktree, branch, HEAD, and dirty state.
2. Read `.devad/manager/CENTRAL_FACTS.md`,
   `.devad/manager/MISSION_LOCK.md`, and
   `.devad/manager/LOCAL_WORK_LEDGER.md`; stop on mismatch or unclassified
   active-lane local work before reading long handoffs.
3. Read `.devad/manager/ANSWERED_DECISIONS.md`,
   `.devad/manager/DECISIONS.md`, and `.devad/manager/TOOL_LESSONS.md` before
   asking owner questions or repeating tool routes.
4. Read this packet and listed evidence only.
5. Read `CONTRACT.md`, or stop if high-risk work has no contract.
6. List expected files before editing.
7. Draft the smallest native CORE plan.
8. For a nontrivial task, run PLAN_CHALLENGE through the hidden
   Luna context bridge and both GLM/Kimi before first mutation.
9. Implement the smallest native CORE change.
10. Use CHUNK helpers only for bounded subtasks inside this packet scope.
11. Before declaring a blocker, run BLOCKER_CHALLENGE by reusing SIDE_INPUT and
   adding only the new failure delta.
12. Run required tests and proof.
13. Before commit, apply the X9 shared contract's security gate to exact
   staged files.
14. After a source commit, apply the shared contract's finite C1/C2
   attestation protocol.
15. Update `STATUS.md`, `LEDGER.md`, and `HANDOFFS.md`.
16. Report `CLAIMED_PASS`, `PARTIAL`, or `BLOCKED`.
17. Write the Worker-owned completion receipt and immutable event.
18. Send one identity-checked `EVENT_READY` callback to the same registered
    Linx task. Retry direct delivery at most three times; on failure write
    `MANAGER_WAKE_FAILED`. Never create recurring pickup.
19. Final chat message must include `HANDOFF_WRITTEN`, status, `STATUS.md`,
    handoff path, callback status, and callback attempt count.

## Proof Required

| Claim | Proof |
| --- | --- |
| UI/browser | screenshot, DOM/ARIA facts, console/log status |
| Backend | test, route/service/persistence evidence |
| API | request/response or dry-run contract |
| CLI | command output |
| MCP | callable tool proof or documented mock |
| Security | no secrets and no cross-workspace leak |
| Commit security | shared-contract security gate result for exact staged files |
| Post-commit docs | tracked C1 record plus attestation-only C2 |

## Report Format

Return:

- Worktree:
- Branch/HEAD/Base:
- Central facts / mission lock:
- Local work:
- Status: CLAIMED_PASS | PARTIAL | BLOCKED | FAILED
- Current status file:
- Files touched:
- Tests run:
- Browser proof:
- API/CLI/MCP proof:
- Secrets/security scan:
- Known risks:
- CHUNK/SIDE used: yes/no, paths:
- Owner question checked against ANSWERED_DECISIONS: yes/no
- Tool lessons checked/updated: yes/no
- Ready for manager verification: yes/no
- Linx callback: ACKNOWLEDGED | DELIVERY_UNCONFIRMED | MANAGER_WAKE_FAILED
- Callback attempts: <n>
```

## CONTRACT.md

Required for long-running, high-risk, merge-review, UI/browser, billing,
source-adoption, or repeated-failure lanes. Optional for tiny docs-only or
read-only lanes only when `TASK.md` says `Contract: skipped` and why.

```md
# Worker Contract: <lane>

**Contract status:** PROPOSED | APPROVED | NEEDS_MANAGER_DECISION | SKIPPED
**Evaluator:** manager | separate evaluator | not required

## Scope

- <one contracted slice>

## Non-Goals

- <explicit exclusions>

## Acceptance Criteria

| # | Assertion | Proof required | Status |
| ---: | --- | --- | --- |
| 1 | <testable assertion> | <test/browser/API/CLI/MCP/source proof> | pending |

## Budget

| Limit | Value |
| --- | --- |
| Max runtime | <minutes> |
| Max same-method proof failures | 2 |
| Max scope expansions | 0 unless manager approves |
| Handover needed after | <time or trigger> |

## Subjective Rubric

Use only when UI/taste/content quality matters.

| Axis | Weight | Good means | Bad means |
| --- | ---: | --- | --- |

## Stop Conditions

- missing source evidence,
- forbidden/shared file needed,
- same proof method fails twice,
- max runtime or max attempts reached,
- contract proves wrong,
- worker cannot verify without unsafe access.

## Restart Rule

If the implementation drifts or patching becomes more expensive than a clean
port, request `RESTART_LANE:<lane>:<reason>` and salvage only proven hunks.
```

## CHUNK Rules

CHUNK helpers/swarm spawn agents are allowed only when the Worker owns the
scope and the task is small enough to verify cheaply.

CHUNK rules:

- one tiny subtask only,
- no manager role,
- no merge/deploy/destructive commands,
- no secrets/raw customer/provider/payment data,
- no edits outside Worker allowed files,
- output must be summarized into Worker `LEDGER.md` or `HANDOFFS.md`.

The Worker remains accountable for CHUNK output.

## SIDE Rules

SIDE means packet-only GLM/Kimi review. Use PLAN_CHALLENGE before first
mutation on nontrivial tasks and BLOCKER_CHALLENGE before final BLOCKED.

SIDE rules:

- hidden Luna medium builds one saved sanitized packet from full durable task
  context; reuse it with a compact failure delta,
- ask both GLM 5.2 and Kimi 2.7 Code once per challenge,
- never send full chat,
- ask for blocker reality, smallest safe next step, proof that would change the
  decision, risks, and stop conditions,
- record SIDE output path in `HANDOFFS.md`,
- treat SIDE advice as evidence, not truth.

## LEDGER.md

```md
# Worker Ledger: <lane>

| Time | Action | Files | Proof | Status |
| --- | --- | --- | --- | --- |
```

## HANDOFFS.md

```md
# Worker Handoffs: <lane>

CURRENT_STATUS:
- Lane: <lane>
- Updated: YYYY-MM-DD HH:mm Europe/Istanbul
- Scope: <one short scope>
- Lane status: CLAIMED_PASS | PARTIAL | BLOCKED | FAILED
- Mission lock: PASS | BLOCKED
- Central facts: PASS | BLOCKED
- Local work: PASS | PARTIAL | BLOCKED
- Destructive guard: PASS | NOT_REQUIRED | OWNER_RUN_REQUIRED | BLOCKED
- Security review: PASS | PARTIAL | BLOCKED | NOT_REQUIRED
- Security precommit: PASS | BLOCKED | NOT_REQUIRED
- Post-commit docs: PASS | BLOCKED | NOT_REQUIRED | NOT_COMMITTED
- Source push: PASS | BLOCKED | NOT_REQUESTED
- Deploy readiness: PASS | BLOCKED | WAIVED_BY_OWNER | NOT_REQUESTED
- Live deploy: PASS | BLOCKED | NOT_REQUESTED
- Latest commit: <sha or none>
- Exact next action: review | correct | merge-review | user-decision
- Must not do: <forbidden next action>

ISSUE_CARD:
| Item | Answer |
| --- | --- |
| Problem | <one simple line> |
| Cause | <one simple line> |
| Fix | <one simple line> |
| Proof | <one simple line> |
| Next | <one action> |

Older sections are historical only. Do not use old PASS text as current truth.

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
```

## Worker Start Prompt

```md
Use $devad-x9-loop worker packet rules and $devad-x9 repo router.
Role: Worker.

THREAD_NAME: Worker
MODEL_PROFILE: <task-class profile from model-policy-v3.md>
MODEL_POLICY: use the selected task-class profile and record it in MANIFEST.

You are a Devad X9 worker for lane `<lane>`.

Read only:
1. `.devad/manager/workers/<lane>/MANIFEST.md`
2. `.devad/manager/workers/<lane>/TASK.md`
3. `.devad/manager/workers/<lane>/CONTRACT.md`
4. `.devad/manager/workers/<lane>/LEDGER.md`
5. `.devad/manager/workers/<lane>/STATUS.md`
6. `.devad/manager/workers/<lane>/HANDOFFS.md`
7. explicitly listed source evidence
8. necessary repo code

Rules:
- You are not the manager.
- You may use CHUNK helpers only for tiny packet-scoped subtasks.
- For nontrivial work, use hidden Luna medium to build SIDE_INPUT, then ask
  both GLM/Kimi to challenge the plan before first mutation.
- Before final BLOCKED, reuse SIDE_INPUT with a compact failure delta and ask
  both GLM/Kimi once more.
- Do not edit outside allowed files.
- Do not touch shared files without manager approval.
- Do not merge, deploy, reset, stash, clean, delete, or force-push.
- Do not commit until `.devad/rules/security` has been applied and
  `composer security:precommit` has passed or the lane is marked `BLOCKED`.
- After a commit, create the required `.devad/docs` commit record before
  claiming push/deploy readiness.
- Do not claim push, deploy readiness, or live deploy without the matching
  gate in `STATUS.md`; deploy also needs `DEPLOY_GATE.md`.
- Do not claim push, deploy readiness, live deploy, or done unless
  `Local work: PASS` is backed by `.devad/manager/LOCAL_WORK_LEDGER.md`.
- Do not write secrets or raw provider/customer/payment data anywhere.
- Do not start high-risk implementation until `CONTRACT.md` is approved or
  manager explicitly says `Contract: skipped`.
- If proof is missing, report PARTIAL or BLOCKED, not PASS.
- Before final BLOCKED on a high-risk/long-running lane, use SIDE or record why
  SIDE was unsafe/unavailable.
- Before final response, update `STATUS.md`, `HANDOFFS.md`, and the
  Worker-owned receipt; then send `EVENT_READY` to the same registered Linx
  task.
- Recurring 15/19-minute pickup is forbidden. Never create a heartbeat/monitor
  as callback fallback.
- Follow `PERMISSION_MODE`. Do not ask the owner to approve safe local work or
  repeat a manager-verified network preflight. Abandon redundant approval
  popups, record `TOOL_FAILED`, and continue through the safe fallback.

First response: 5-line plan, missing evidence, and exact files expected to change.
Final response: `HANDOFF_WRITTEN`, status, status path, handoff path, manager action requested, callback status, and attempt count.
```


## X9-V5 Identity And Callback Addendum

Every active packet must use packet schema X9-V5 and include:

- immutable registered Linx task ID;
- immutable Worker task ID and registered role `WORKER`;
- one dispatch ID for the exact packet;
- packet SHA-256;
- claimed resources;
- Worker-owned completion receipt path and SHA-256;
- callback event type and expected Linx acknowledgement.

Linx checks `ROLE_REGISTRY.json` before delivery and
`DISPATCH_LEDGER.jsonl` before retry. A changed packet gets a new dispatch ID.
Completion is stale unless task ID, dispatch ID, role, packet hash, and receipt
owner all match.

After durable completion state is written, Worker sends:

```text
EVENT_READY
LINX_TASK_ID: <registered Linx task id>
SOURCE_TASK_ID: <registered Worker task id>
SOURCE_ROLE: WORKER
DISPATCH_ID: <dispatch id>
PACKET_SHA256: <packet hash>
EVENT_TYPE: HANDOFF_READY | BLOCKED | FAILED
RECEIPT_PATH: <Worker-owned receipt path>
RECEIPT_SHA256: <receipt hash>
```

Retry unchanged direct delivery at most three times. Exact acknowledgement
stops. After failure write `MANAGER_WAKE_FAILED` and report manual pickup.
Recurring 15/19-minute pickup is forbidden.
