---
name: devad-x9-loop
description: Use when coordinating long Devad X9 work across Linx, Thinx, Worker, Reader, CHUNK, or SIDE roles; when deterministic task identity, dispatch, callbacks, local work, ownership, gates, concurrency, recovery, or model cost must remain correct without heartbeat polling or chat-history routing.
---

# Devad X9 Loop Lite v6

## Load First

Read `../devad-x9/references/x9-shared-contract.md`, then
`references/loop-lite-v6-contract.md`. The shared contract owns Git truth,
security, commits, proof, push/deploy gates, durable documentation, and
destructive safety. This skill owns deterministic orchestration.

Compact chat does not reduce reasoning, tests, or proof. Read only the exact
role packet and smallest linked rule needed.

## Roles

| Role | Job | Code? | Authority |
| --- | --- | --- | --- |
| Linx | Owner bridge and exact transport | No | `ACTION.json` only |
| Thinx | File-only strategy/review | No | One verified decision |
| Worker | One bounded implementation | Yes | Exact `TASK.json` |
| Reader | Mechanical extraction | No | Manifested inputs |
| CHUNK | Small assigned files | Scoped | Exact subtask |
| SIDE | Independent challenge | No by default | Secret-safe packet |

Role comes from immutable task ID in loop-lite state. Titles are display text.
Emit `TITLE_ROLE_MISMATCH:<task_id>:<role>:<title>` on conflict. Never route by
nickname, title, chat position, or remembered identity.

## Models

- Linx: `gpt-5.6-sol high`.
- Thinx: `gpt-5.6-sol xhigh` normally.
- Thinx: `gpt-5.6-sol Ultra` for one explicit high-risk decision, then return to
  xhigh whether the pass succeeds, fails, or pauses.
- Worker: `gpt-5.6-terra high`; use xhigh only when the owner asks.
- Reader/CHUNK/SIDE: cheapest proven model for the bounded extraction or
  challenge. They do not own judgment.

Record a model-setting tool gap honestly. Never create a second Thinx merely
to change effort.

## Linx Fast Pass

Linx reads the newest owner message and attachments once and saves an immutable
OWNER_PACKET.json. Raw owner text and copied attachments are local sensitive
state ignored by project Git; tracked recovery state keeps only hashes and
paths. Old chat is never routing authority.

For each owner turn or verified callback:

1. Run scripts/loopctl.py reconcile for the exact repository and event.
2. Read only .devad/manager/loop-lite/runtime/ACTION.json.
3. Perform that one exact Codex transport action.
4. Run scripts/loopctl.py record-delivery with the real result.
5. Report short status, proof, blocker, and one next action.

Linx never reviews code, edits product files, judges architecture, manually
patches orchestration state, or rereads manager history. It does not stop with
only `Next` when ACTION.json authorizes a safe transport.

No recurring heartbeat, 15/19-minute poll, sleep loop, or model-written pass
lock is allowed. Files alone do not wake a Codex task. Worker or Thinx writes
its receipt, then sends one direct event callback to the same registered Linx.
Callback failure gets one same-event retry, then CALLBACK_FAILED and a manual
one-shot pickup.

## Controller

Use scripts/loopctl.py:

    python scripts/loopctl.py --repo <repo> init --import-v5
    python scripts/loopctl.py --repo <repo> register --file <registration.json>
    python scripts/loopctl.py --repo <repo> reconcile --task <task-id>
    python scripts/loopctl.py --repo <repo> prepare-dispatch --task <task-id> --sender <linx-id>
    python scripts/loopctl.py --repo <repo> record-delivery --dispatch <id> --phase DISPATCH --method codex-thread --result accepted
    python scripts/loopctl.py --repo <repo> consume-event --file <event.json>
    python scripts/loopctl.py --repo <repo> doctor
    python scripts/loopctl.py --repo <repo> rebuild

Tracked SNAPSHOT.json is recovery truth and stays below 8 KB. Ignored loop.db
is disposable SQLite. Generated ACTION.json stays below 4 KB. STATUS.md and
HANDOFFS.md are generated human views, never parser authority. Existing v5
files remain historical evidence.

If snapshot export fails or database generation is newer, stop routing with
SNAPSHOT_STALE and reconcile. Never guess or manually patch the state.

## Dispatch And Completion

Each immutable packet gets one dsp-<uuid>. Same task and packet reuse the
unresolved dispatch. A changed packet creates a new dispatch with supersedes.

- Accepted transport without exact acknowledgement: DELIVERY_UNCONFIRMED.
- Never claim sent once without one attempt plus exact acknowledgement.
- Duplicate callback: idempotent DUPLICATE_EVENT.
- Wrong task, actor, role, dispatch, packet, path, or hash: STALE_COMPLETION.
- Two failed callback attempts: CALLBACK_FAILED, manual one-shot pickup.

Worker completion requires a Worker-owned RESULT.json and matching current Git
scope. Historical or wrong-lane handoffs cannot complete current work.

## Worktrees And Claims

Preserve every checkout. A worktree does not imply an active Worker. Use
canonical repository-relative file/directory claims; no ambiguous globs.
Normalize Windows case and separators before overlap checks.

Completion checks staged, unstaged, untracked, and committed paths. An
unclaimed path is SCOPE_BREACH and cannot integrate. Ask
CLAIM_EXPANSION_REQUEST before editing a needed new path.

Serialize database/migrations, shared runtime, browser profile, integration
branch, deployment, and live proof. Dirty core-x9 is never integration.

Rollout:

| Clean dispatches | Coding Workers |
| --- | ---: |
| 0-2 | 1 |
| 3-9 | 2 |
| 10+ | 3 |

Any lost work, duplicate delivery, stale completion, scope breach, parser
failure, orphan lock, false PASS, or context compaction returns the limit to
one until reviewed. Parallel tasks need satisfied dependencies and disjoint
path/resource claims.

## Thinx

Reuse the owner-locked Thinx task. Thinx reads durable manifested files only,
never chat. It does not code, commit, push, deploy, browse interactively, or
manage Workers. It writes one decision or MISSING_MD:<lane>:<fact>, then one
identity-checked direct callback.

A hidden Reader in the same Thinx task may condense long inputs mechanically.
Thinx verifies the receipt and owns the judgment. Replacement requires owner
approval; effort changes do not require a new task.

## Worker

Use devad-x9 for code, tests, security, commits, docs, proof, push, and deploy
gates. Every Worker receives TASK.json, owner packet hash, exact worktree/base
SHA, dependencies, claims, resources, finish line, and forbidden scope.

Before completion:

1. Run focused tests and full security gate.
2. Create source C1 from exact staged files.
3. Write .devad/docs/commits/<C1>.md and create attestation C2.
4. Write RESULT.json with changed files and proof.
5. Send one direct callback after the result is durable.

Do not use git add ., cleanup, reset, stash, worktree removal, destructive
database/app operations, or deployment without exact current gates.

## Sidecars

Run scripts/opencode_doctor.py doctor first. Use one secret-safe request each
for configured GLM 5.2 and Kimi 2.7 Code only when plan challenge or blocker
review adds value. The doctor copies strict JSON into a temporary no-repository
directory, disables external plugins and every model tool, and passes only an
environment allowlist. Never invoke a direct sidecar command.

The packet contains the requirement, exact claims, relevant diff/proof,
failure, and one question, never full chats or unrelated logs.

`TOOL_UNAVAILABLE` is recorded once and does not block the Worker. Sidecar
advice remains untrusted until locally verified. Kimi 2.6 is not configured.

## Safety

All existing X9 safety remains mandatory: current Git/runtime truth, owner and
attachment identity, local-work preservation, full security before C1, C1/C2
attestation, separate source/push/deploy/live-proof gates, exact release state,
and owner-run destructive final actions.

Do not stop for a solvable soft blocker. After three failed Worker attempts,
pause only that task and request Thinx review; do not declare the feature
blocked automatically.

## Output

Use compact visible chat. Put detailed proof in durable files. Unknown token
telemetry stays `Unknown`; never use fallback lifetime totals. Never claim
delivery, PASS, deployment, or completion without exact current evidence.
