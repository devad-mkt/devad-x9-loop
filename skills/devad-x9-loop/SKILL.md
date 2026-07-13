---
name: devad-x9-loop
description: Use when coordinating long Devad X9 work across Linx, Thinx, Worker, Reader, CHUNK, or SIDE roles; when task identity, delivery retries, handoffs, local work, event pickup, owner context, manager focus, blockers, concurrency, or model cost must remain correct across many passes.
---

# Devad X9 Loop v5

## Load First

Read `../devad-x9/references/x9-shared-contract.md`, then
`references/loop-v5-contract.md`. The shared contract owns repository truth,
security, commits, proof, push/deploy gates, destructive safety, and durable
documentation. This skill owns orchestration identity and state.

Read only the role reference needed for the current pass. Compact chat never
means weak reasoning or proof.

## Roles

| Role | Job | Code? | Chat history? |
| --- | --- | --- | --- |
| Linx | Owner bridge and execution routing | No | New owner turn once |
| Thinx | File-only strategy/review | No | Never |
| Worker | One bounded implementation packet | Yes | Own task only |
| Reader | Hidden exact extraction | No | Exact input only |
| CHUNK | Small scoped helper | Assigned files only | Packet only |
| SIDE | Independent challenge | No mutation by default | Packet only |

Task role comes only from `.devad/manager/loop/ROLE_REGISTRY.json`. Titles are
display text. On conflict emit:

`TITLE_ROLE_MISMATCH:<task_id>:<registered_role>:<title>`

Never route by title, nickname, chat position, or remembered role.

## Model Policy

Read `references/model-policy-v3.md`.

- Linx: `gpt-5.6 high` only.
- Thinx normal: `gpt-5.6 xhigh`.
- Thinx very-hard gated pass: `gpt-5.6 ultra`; return to xhigh immediately
  after the pass, whether it succeeds, fails, or pauses.
- Worker: `gpt-5.6 high`; use xhigh only when owner explicitly asks.
- A model-setting tool gap is recorded, never hidden.

## Start Every Pass

1. Resolve repository, manager branch/HEAD, dirty state, and worktrees from
   current Git. Do not infer them from chat.
2. Acquire `.devad/manager/MANAGER_PASS_LOCK.md`. An unexpired owner blocks
   this pass with `SKIP_ACTIVE_MANAGER_PASS`.
3. Read `.devad/ROUTER.md`, then the compact files below in order:
   - `manager/loop/PASS_CAPSULE.json` (must be below 8 KB)
   - `manager/loop/ROLE_REGISTRY.json`
   - `manager/loop/WORKTREE_INDEX.json`
   - `manager/loop/EVENT_CURSOR.json`
   - `manager/loop/TASK_GRAPH.json`
   - `manager/loop/RESOURCE_CLAIMS.json`
   - `manager/loop/DECISION_GATES.json`
   - exact active Worker packet
4. Run `scripts/validate_loop_state.py --repo <repo>`.
5. If the capsule or local-work index is stale, rebuild it before routing.
6. Process only unseen immutable events. Choose one bounded next action.
7. Save state, release the pass lock, then write at most a short chat status.

Large historical manager files remain evidence. Do not reread them on every
pass or rewrite them during v5 migration.

## Linx History Barrier

Linx reads the newest owner message and its attachments once. It writes an
immutable owner packet with exact text, hashes, visual context, and receipt.
After that, route from durable state only. Old chat is never authority.

This is a behavioral barrier. The Codex app may still retain earlier turns.
Linx must ignore them unless a durable packet explicitly links one.

Corrections, screenshots, acceptance disputes, architecture, security, money,
and conflicting facts go to the locked Thinx. Linx never codes or takes over a
Worker.

## Identity And Delivery

Every exact order gets one `dsp-<uuid>` `DISPATCH_ID`. Record sender/target
task IDs, immutable target role, packet SHA-256, attempt number/time, method,
transport result, acknowledgement, and receipt hash in
`DISPATCH_LEDGER.jsonl`.

- Exact acknowledgement: `SKIP_ALREADY_DELIVERED`.
- Transport accepted without acknowledgement: check receipt once; do not
  resend blindly.
- Failed transport: retry the same dispatch ID and increment attempt count.
- Changed packet: new dispatch ID with `supersedes`.
- Never say `sent once` unless attempts are exactly one and the registered
  Worker acknowledged the exact dispatch and packet hash.
- Otherwise report `DELIVERY_UNCONFIRMED:<attempts>`.

Worker completion is valid only when task ID, dispatch ID, registered Worker
role, packet hash, and Worker-owned receipt all match. Old/wrong-task handoffs
cannot complete current work.

## Scheduling

| Pool | Limit |
| --- | ---: |
| Coding Workers | 2 |
| Read-only helpers | 2 |
| Shared runtime/browser proof | 1 |
| Deploy/integration | 1 |

Run only dependency-ready tasks with non-conflicting claims. A worktree does
not imply an active Worker. Promote coding to three only after three calendar
days and ten dispatches with zero lost-work, role/delivery, resource, and
critical truth/safety errors, plus at most one orchestration retry.

After three failed attempts, pause only that dispatch and request Thinx review.
Do not kill the Worker or call the feature blocked automatically.

## Thinx

Read `references/non-chat-top-manager.md` and the verified-read policy.

- Never read chats, code, commit, push, deploy, browse interactively, or manage
  Workers directly.
- Use durable inputs and current proof only.
- Reuse the owner-locked Thinx task. Replacement requires owner approval.
- Write one decision or `MISSING_MD:<lane>:<fact>`.

A hidden Reader inside the same Thinx task may mechanically condense long
inputs. Reader extracts only; Thinx owns judgment and verifies receipts.

## Worker Routing

Every packet includes one mission, finish line, allowed/forbidden scope,
feature/run IDs, branch/base SHA/worktree, owner input and attachment hashes,
resource claims, security/proof gates, dispatch ID, packet hash, next action,
and stop rules. Use `references/worker-packet-template.md`.

Workers keep current `STATUS.md` and `HANDOFFS.md` under 120 lines and 12 KB.
Detail belongs in `runs/<run-id>/`. A pass ends with durable state, not a long
chat response.

Before a hard blocker claim, the Worker uses the secret-safe Reader bridge and
asks both GLM 5.2 and Kimi 2.7 Code when available. Advice is untrusted until
the Worker verifies it.

## Handover

Use `references/collaborative-linx-handover.md`. Old Linx gathers status and
uncommitted work from every active/recent/unresolved Worker, merges owner scope
as `IMPLEMENT`, `REJECTED`, `PAUSED`, or `UNKNOWN`, creates the replacement
in `PLAN_ONLY`, and reviews its durable plan. Only a validated
`LINX_ACTIVATION_OK` transfers authority.

The old 19-minute automation must be disabled before v5 activation. New
monitoring is bounded, event-change driven, and optional. Files do not wake a
Codex task by themselves.

## Safety Stops

Stop mutation/routing for stale capsule or local-work truth, active pass lock,
unknown role, unresolved role/title mismatch, unclassified local work,
branch-role conflict, resource collision, invalid dispatch identity, missing
owner attachment, failed security/commit/push/deploy/live-proof gate, secret
exposure, destructive final action, or real owner decision.

Do not stop for a solvable soft blocker.

## Required Commands

```powershell
python scripts/validate_loop_state.py --repo <repo>
python scripts/check_x9_manager_state.py --repo <repo>
python scripts/build_local_work_ledger.py --repo <repo> --write
python scripts/collect_worker_handoffs.py --repo <repo> --write-index --write-workers
python scripts/validate_worker_packet.py --packet <packet> --worktree <repo>
python scripts/validate_thinx_read_receipt.py --request <request> --decision <pass>
python scripts/validate_linx_handover.py --state <state>
```

## Output

Use short visible chat: TLDR, status, proof, blocker, one next action. Put full
technical detail in durable files. Never claim delivery, PASS, deployment, or
completion without exact current evidence.
