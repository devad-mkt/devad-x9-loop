# X9 Loop Lite v6 Contract

This contract replaces model-written orchestration state with one deterministic
controller. It keeps every X9 truth, security, commit, proof, push, deployment,
live-proof, and destructive-action gate.

## Authority

| State | Authority |
| --- | --- |
| Tracked recovery truth | .devad/manager/loop-lite/SNAPSHOT.json |
| Disposable query cache | .devad/manager/loop-lite/loop.db |
| One permitted Linx action | .devad/manager/loop-lite/runtime/ACTION.json |
| Worker or Thinx callback | Immutable event receipt plus SHA-256 |
| Human status | Generated runtime STATUS.md and HANDOFFS.md |
| Historical evidence | Existing manager/loop and manager Markdown |

Generated human views are never parser authority. Existing v5 state remains
historical evidence and is not rewritten during cutover.

## Database

SQLite contains actors, worktrees, tasks, claims, resources, dispatches,
deliveries, events, gates, outbox, and metrics. Enable WAL, foreign keys,
unique identifiers, and short BEGIN IMMEDIATE transactions.

Use at most one state transaction per event. Never hold a database lock across
a model turn, transport call, Git command, or sidecar request. The tracked
snapshot stays below 8 KB and ACTION.json stays below 4 KB.

The cache is ignored by Git and may be rebuilt. SNAPSHOT.json, immutable
Worker receipts, and current Git are the recovery inputs.

## Commands

    python scripts/loopctl.py --repo <repo> init --import-v5
    python scripts/loopctl.py --repo <repo> register --file <registration.json>
    python scripts/loopctl.py --repo <repo> reconcile --task <task-id>
    python scripts/loopctl.py --repo <repo> prepare-dispatch --task <task-id> --sender <linx-id>
    python scripts/loopctl.py --repo <repo> record-delivery --dispatch <id> --phase DISPATCH --method codex-thread --result accepted
    python scripts/loopctl.py --repo <repo> consume-event --file <event.json>
    python scripts/loopctl.py --repo <repo> doctor
    python scripts/loopctl.py --repo <repo> rebuild

Init may import valid v5 role, task, worktree, claim, event, and gate facts. It
never edits, deletes, moves, or normalizes v5 evidence.

## Machine Contracts

| File | Required meaning |
| --- | --- |
| OWNER_PACKET.json | Exact newest owner text plus attachment hashes |
| TASK.json | Task, worktree, base SHA, claims, resources, gates, finish line |
| ACTION.json | One exact transport action Linx may perform |
| RESULT.json | Worker identity, changed files, proof, C1/C2, blocker |

TASK.json binds owner_packet_path and owner_packet_sha256 to the exact local packet.
Worker and Thinx receipts are immutable event-scoped files at
.devad/workers/<actor>/receipts/<event_id>.json. The callback carries the
SHA-256 of the exact receipt bytes.

## Linx Pass

Linx remains gpt-5.6 Sol high.

1. Capture the newest owner message and attachment hashes once.
2. Save an immutable content-addressed packet in manager/owner-packets.
3. Run reconcile.
4. Read only runtime/ACTION.json.
5. Perform that exact transport action.
6. Record the real transport result.
7. Report compact status and proof.

Raw owner packets and copied attachments are local sensitive state ignored by
project Git. The tracked snapshot stores only their hashes and local paths.
Back up raw content only through an owner-approved private backup flow.

Linx never reviews code, edits product files, judges architecture, patches
state manually, rereads manager history, or takes Worker scope.

## Identity And Delivery

Roles are immutable and keyed by task ID. Task titles are display text only.
A conflict emits TITLE_ROLE_MISMATCH with task ID, registered role, and title.

Each immutable task packet gets one dsp UUID. The same unresolved packet reuses
its dispatch. A changed packet creates a new dispatch and supersedes the old
one. A superseded dispatch cannot complete a task.

Dispatch is allowed only for REGISTERED or RETRY_READY tasks. Worker completion
is allowed only after the exact dispatch is acknowledged as DISPATCHED.
Thinx review is allowed only after the task is THINX_REVIEW_REQUIRED and the
review delivery is acknowledged.

Never report sent once unless one exact attempt and matching acknowledgement
exist. Accepted transport without acknowledgement is DELIVERY_UNCONFIRMED.
Duplicate events are idempotent. Wrong actor, role, task, dispatch, packet,
path, or hash is STALE_COMPLETION.

## Callbacks

Worker or Thinx writes its receipt first, then sends one direct event callback
to the same registered Linx task. A callback failure gets one same-event retry.
A second failure records CALLBACK_FAILED and requires MANUAL_ONE_SHOT_PICKUP.

No recurring heartbeat, scheduled polling, sleep loop, or file-only wakeup is
allowed. Files alone cannot wake a Codex task.

## Claims And Worktrees

Worktree identity and path mapping are immutable after registration. Preserve
every checkout. A worktree does not imply an active Worker.

Claims use canonical repository-relative files or directories. Ambiguous globs
are forbidden. Normalize Windows case, separators, dot segments, and directory
containment before comparing claims.

Before dispatch and completion, inspect staged, unstaged, untracked, and
committed paths. Unclaimed local work is SCOPE_BREACH. A needed path outside
ownership requires CLAIM_EXPANSION_REQUEST before mutation.

A COMPLETE result with changes must bind exact C1 and C2, current HEAD must
equal C2, and no unexpected final dirty path or later commit may exist.
Integration uses a clean controlled checkout; dirty core-x9 is never used.

## Resources And Parallelism

Serialize database and migrations, shared runtime, browser profile, integration
branch, deploy, and live proof.

| Clean dispatches | Coding Worker limit |
| --- | ---: |
| First 3 | 1 |
| 4 through 10 | 2 |
| After 10 | 3 |

Promotion also requires the stated clean-day gate and zero lost work, duplicate
delivery, stale completion, scope breach, parser failure, orphan lock, false
PASS, resource conflict, or context compaction. Parallel tasks need satisfied
dependencies and disjoint path and resource claims.

Three consecutive blocked receipts pause only that dispatch and require Thinx
review. They do not automatically block the feature.

## Models

- Linx: gpt-5.6 Sol high.
- Thinx: Sol xhigh normally.
- Thinx: Sol Ultra for one explicit high-risk decision, then return to xhigh.
- Worker: Terra high by default; xhigh only when the owner asks.
- Linx never escalates itself to solve Worker work.

## Sidecars

Use opencode_doctor.py before advisory requests. It invokes the real executable
in a temporary no-repository directory with --pure, external plugins disabled,
every model tool denied, and an environment allowlist. Direct OpenCode commands
and command shims are forbidden.

A strict x9-sidecar-packet-v1 JSON packet contains only owner requirement,
claims, relevant diff, proof, observed failure, and one question. It never
contains chat history, unrelated logs, secrets, cookies, tokens, customer data,
or raw production configuration.

Run at most one bounded request per configured GLM 5.2 or Kimi 2.7 Code route.
Kimi 2.6 is not configured. Provider, auth, quota, or model failure records
TOOL_UNAVAILABLE once, does not retry, and does not block the Worker. Advice is
untrusted until verified locally.

## C1 And C2

A COMPLETE Worker receipt with changed files includes exact structured
security and tests proof objects, the source commit C1, and the attestation
commit C2. C2 attests C1 only and does not create recursive documentation.

The controller verifies proof paths and hashes, exact current HEAD C2, and
actual final checkout scope before accepting completion.

## Recovery

Rebuild validates the complete expected snapshot table set, receipts, and Git
before replacing the cache. Missing or extra tables fail closed. Corrupt DB,
WAL, and SHM files are preserved as one recovery set. If installation fails,
the full set is restored. Junction, symlink, and reparse escapes are rejected.

## Performance And Metrics

- Deterministic reconciliation: under five seconds.
- Routine Linx callback: median under 60 seconds, p95 under two minutes.
- At most one Linx model turn and one state transaction per event.
- No manual manager-state patches.

Track wall time, prompt bytes, reads, writes, retries, compactions,
first-pass success, and real token telemetry when available. Missing token data
is exactly Unknown. Never substitute fallback lifetime totals.