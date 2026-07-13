# Collaborative Linx Handover

Use this protocol when Linx must be replaced and one summary is not enough.
The transition is collaborative, but there is always **one execution authority**.

## Phase 1: Freeze And Inventory

The old Linx acquires the manager pass lock and sets:

```text
Execution authority: OLD_LINX_STATUS_ONLY
```

It may not issue implementation, proof, push, deploy, or product-judgment
orders. It sends one status-only request to every managed Worker that is active,
recent, unresolved, locally dirty, or not durably accepted:

```text
HANDOVER_INVENTORY_REQUEST:<handover-id>:STATUS_ONLY
```

Each Worker must update its durable STATUS/HANDOFFS and return:

- current mission, feature, lane, thread, worktree, branch, and HEAD;
- exact completed, incomplete, blocked, rejected, and paused scope;
- `What next` and `Must not do`;
- tracked dirty, untracked, uncommitted, unpushed, and unproven work;
- latest commits plus source-push, deploy, and live-proof states;
- owner-input IDs and attachment receipts used;
- exact handoff path and timestamp.

Do not ask every historical terminal Worker. Include terminal Workers only when
local work, owner acceptance, proof, or next action remains unresolved. Ask
once, then use durable state. No polling or implementation restart is allowed.
Missing replies become `INVENTORY_MISSING:<lane>`, never guessed facts.

## Phase 2: Build Owner Scope

The old Linx merges Worker inventories with current Git, local-work truth, and
the newest durable owner inputs. It writes `OWNER_SCOPE_MATRIX` in the handover:

| Requirement | Owner state | Current state | Local-only work | Proof | Next | Must not |
| --- | --- | --- | --- | --- | --- | --- |

`Owner state` is exactly one of:

- `IMPLEMENT`
- `REJECTED`
- `PAUSED`
- `UNKNOWN`

The newest owner input overrides Worker plans and old PASS text. Rejected or
paused scope cannot appear in the new plan as implementation. `UNKNOWN` is a
handover review block when it changes product direction, risk, money, deploy,
or acceptance.

## Phase 3: New Linx Plans Only

After inventory coverage and handover hashes pass, the old Linx creates exactly
one replacement Linx at `gpt-5.6 high`. The replacement starts `PLAN_ONLY`, has
no execution authority, does not message Workers, and does not start a
heartbeat. It reads the handover and only its linked current files, then writes:

```text
NEW_LINX_PLAN:<absolute-path>:<sha256>
```

The plan must map every `IMPLEMENT` row to one bounded route, preserve every
`REJECTED`/`PAUSED` row, classify all local work, identify missing evidence,
reuse registered worktrees, and name one first action. It must not reconstruct
missing facts from old chat.

## Phase 4: Old Linx Final Review

The old Linx performs a coverage review, not new product judgment. Compare the
new plan against Worker receipts, `OWNER_SCOPE_MATRIX`, local-work ledger,
branch facts, and prohibited actions.

```text
OLD_LINX_FINAL_REVIEW: PASS | FAIL
```

Fail when any Worker is missing without explicit classification, any local work
is omitted, accepted scope is lost, rejected/paused scope is restarted, a
branch/worktree is wrong, or the plan invents acceptance. A contradiction that
requires judgment goes to the locked Thinx; the tired Linx does not decide it.

## Phase 5: Transfer And Direct Continuation

Only after final review PASS, the old Linx writes:

```text
LINX_ACTIVATION_OK:<new-thread-id>:<handover-sha256>:<plan-sha256>
```

Then it releases the lock, sets execution authority to the new Linx, sends one
start message containing the activation token, and retires. The old Linx must
not run another manager pass.

The new Linx refreshes current truth, acquires the lock, and starts one approved
action. Before dispatching Worker or Thinx, it records exact callback identity
and releases the lock. After durable work is written, the receiver sends:

```text
EVENT_READY
LINX_TASK_ID: <new Linx task id>
SOURCE_TASK_ID: <registered source task id>
SOURCE_ROLE: WORKER | THINX
DISPATCH_ID: <dispatch id>
PACKET_SHA256: <packet hash>
EVENT_TYPE: PLAN_READY | HANDOFF_READY | DECISION_READY | BLOCKED | FAILED
RECEIPT_PATH: <durable receipt path>
RECEIPT_SHA256: <receipt hash>
```

The callback targets the same registered Linx task. It starts one new manager
pass after identity and receipt validation.

Recurring 15/19-minute pickup is forbidden. Do not create or renew a recurring
heartbeat after activation. An owner-requested one-shot fallback is allowed
only for a delayed owner decision or an external condition that cannot callback.

## Required Transition State

Maintain `.devad/manager/LINX_HANDOVER_STATE.md`. Activation is invalid unless
it records every named phase, Worker coverage, hashes, one execution authority,
and the exact direct callback target. Validate before activation:

```powershell
python scripts/validate_linx_handover.py --state <repo>/.devad/manager/LINX_HANDOVER_STATE.md
```
