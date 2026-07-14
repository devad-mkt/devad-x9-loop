# X9 Shared Contract

This is the normative safety contract shared by `devad-x9` and
`devad-x9-loop`. The temporary `devad-x9-manager` name redirects here. Read it
before code, routing, commit, push, deploy, or completion claims.

## Authority

Use this order:

1. Current Git, filesystem, test, browser, provider, and runtime evidence.
2. `.devad/manager/loop-lite/SNAPSHOT.json`, exact `TASK.json`, and validated
   `RESULT.json` for current orchestration identity and scope.
3. `CENTRAL_FACTS.md`, `MISSION_LOCK.md`, and `LOCAL_WORK_LEDGER.md` after
   checking them against current evidence.
4. Current feature contract, task, and run proof.
5. Historical handoffs and chat only when a durable fact points to them.

Existing `.devad/manager/loop/`, manager locks, and large handoffs are
historical evidence in v6. They never override current Git or loop-lite state.

## Manager Role Boundary

- The controller owns roles, worktree/task state, claims, dependencies,
  dispatch identity, callbacks, recovery snapshot, and the one action Linx may
  perform.
- Linx captures the newest owner input once, runs reconciliation, transports
  `ACTION.json`, records the real result, and reports compact status. Linx
  never codes or reviews Worker code.
- Thinx makes one file-only strategy or contradiction decision. It never codes
  or manages Workers.
- Worker performs implementation and proof inside exact claims.
- A stalled Worker is corrected, resumed, or replaced after durable receipt;
  Linx never takes over its work.

Owner corrections, contradictions, acceptance mismatch, screenshot judgment,
security, money, architecture, or implemented/deployed claims are
`JUDGMENT_REQUIRED`. Preserve exact owner text and attachment hashes, then
route current evidence to the locked Thinx. Incomplete evidence is `Unknown`
plus the exact check.

## Deterministic Manager State

SQLite uses short `BEGIN IMMEDIATE` transactions, WAL, and foreign keys. It is
an ignored cache, never durable authority. Tracked `SNAPSHOT.json` is compact
recovery truth. `ACTION.json` is generated only after the state transaction and
snapshot succeed.

No model-written mutex, recurring heartbeat, periodic poll, or lock survives a
model turn. Existing `MANAGER_PASS_LOCK.md` remains historical evidence only.
Callback failure gets one same-event retry, then `CALLBACK_FAILED` and manual
one-shot pickup.

## Truth Lock

Before choosing or proving the next action, the current task/snapshot must
resolve:

```md
- Repository root:
- Manager-state branch and HEAD:
- Implementation branch and HEAD:
- Integration branch and HEAD:
- Deployment branch and HEAD:
- Active feature/task/dispatch:
- Worker and worktree identity:
- Base SHA and exact claims:
- Finish line:
- Local work: PASS | PARTIAL | BLOCKED
- Destructive guard: PASS | NOT_REQUIRED | OWNER_RUN_REQUIRED | BLOCKED
- Security precommit: PASS | BLOCKED | NOT_REQUIRED
- Post-commit docs: PASS | BLOCKED | NOT_COMMITTED | NOT_REQUIRED
- Source push: PASS | BLOCKED | NOT_REQUESTED
- Deploy readiness: PASS | BLOCKED | WAIVED_BY_OWNER
- Live deploy: PASS | BLOCKED | NOT_REQUESTED
- Live proof: PASS | BLOCKED | NOT_REQUESTED
- Exact next action:
- Must not do:
```

Never compare manager, implementation, integration, and deployment checkouts
as if they were one branch.

## Local Work

Current Git is required for every registered checkout. Classify each lane as:

- `PLANNED_ONLY`
- `UNCOMMITTED`
- `SOURCE_ONLY`
- `V105_READY`
- `DEPLOYED`
- `LIVE_PROOF_PASS`

GitHub is not complete truth while active local work exists. Do not push,
integrate, deploy, or claim done until staged, unstaged, untracked, and
committed local work is attributed to an exact task or preserved as unrelated.
`LOCAL_WORK_LEDGER.md` is a generated/human aid; current Git and snapshot
identity remain authority.

## Worktree Discipline

The controller registers every checkout from `git worktree list --porcelain`
plus explicitly independent repositories. Each entry records repository,
worktree, branch, HEAD, local state, purpose, and `PRESERVE` status.

- Reuse an existing worktree for the same active feature when its state fits.
- Up to three coding worktrees may be active only after rollout promotion.
- Parallel tasks require satisfied dependencies and non-overlapping canonical
  file/directory claims and exclusive resources.
- Use stable short paths; do not make timestamped copies for ordinary retries,
  reviews, or model changes.
- A worktree is never active merely because it exists.
- Dirty `core-x9` is never the integration checkout.
- Before retirement, classify all local work and prepare an owner-run report.
- Codex never removes, cleans, resets, stashes, or relocates a worktree.

Age alone never marks a checkout safe to move or remove.

## Exact Scope

- Claims are canonical repository-relative files or directories, not globs.
- Normalize Windows separators and case before comparing claims.
- Before completion, compare staged, unstaged, untracked, and committed paths
  since the task base SHA against claims.
- Any mismatch is `SCOPE_BREACH` and cannot integrate.
- A needed new path requires `CLAIM_EXPANSION_REQUEST` before editing.
- Stage exact files only. Never use `git add .` in a shared or dirty checkout.
- Never modify unrelated user work.
- Serialize database/migrations, shared runtime, browser profile, integration
  branch, deployment, and live proof.

Never reset, clean, overwrite, uninstall, prune, drop, truncate, force-push,
or remove data, apps, services, containers, volumes, or worktrees from Codex.

## Destructive Actions

Before mutation, read `destructive-action-guard.md` and classify the pass as
`NOT_REQUIRED`, `OWNER_RUN_REQUIRED`, or `BLOCKED`.

Chat approval is not executable authorization. Codex may create backups,
inventories, restore proof, and `DESTRUCTIVE_REQUEST.md`; the owner runs the
exact final destructive command outside Codex. Linx, Thinx, Worker, Reader,
CHUNK, SIDE, automations, and subagents cannot waive this rule.

For an existing file, recheck its Git blob or SHA-256/size/last-write identity
immediately before writing. Stop on concurrent change.

## Security Before Commit

For app code, runtime-affecting tests, CI/deploy gates, or
implementation-guiding docs:

1. Read `.devad/rules/security/README.md` and its routed read order.
2. Identify touched trust boundaries and risk families.
3. Stage exact claimed files only.
4. Run the repository full security gate, staged file list, and staged diff
   check. In CORE this includes `composer security:precommit` when available.
5. Run focused tests and proof from the security matrix.
6. Run a staged secret check.

Never commit secrets, cookies, auth codes, provider payloads, customer/payment
data, private logs, or `.env` values. Missing/failed required checks set
`Security precommit: BLOCKED` and forbid commit.

## Commit And Attestation

Use a finite two-commit protocol:

1. After security PASS, create source commit `C1` from exact staged scope.
2. Create `.devad/docs/commits/<date>-<lane>-<short-C1>.md` with exact C1 SHA,
   branch, files, security impact, proof, blocks, and next action.
3. Commit that record as `C2`: `docs(x9): attest <short-C1>`.
4. C2 is `ATTESTATION_ONLY` only when limited to C1 record and required
   generated pointers.
5. C2 does not require a third record, but still needs exact staging, diff
   check, and secret check.
6. Validate C1/C2 and push together. Never push required C1 alone.

If no commit occurred, record `Latest commit: NONE` and
`Post-commit docs: NOT_COMMITTED`.

## Push And Deploy

Before source push:

- intended local HEAD/range, remote, and branch policy are exact;
- security and attestation pass;
- active local work is classified;
- no unrelated commit is included.

Before deployment:

- exact deploy SHA and deployment branch are recorded;
- approval applies to that SHA;
- dependencies/migrations pass or are owner-waived;
- rollback and live-proof plans exist;
- Dokploy source branch and environment are verified.

Source push, deploy readiness, live deployment, and live proof are separate
gates. A successful deploy without real user-visible proof is not completion.

## Durable `.devad` Truth

Important Markdown and JSON stay tracked in the private Git repository.
`.devad` remains excluded from production images and public artifacts.

- `.devad/manager/loop-lite/SNAPSHOT.json`: active recovery truth.
- `.devad/manager/loop-lite/runtime/ACTION.json`: ignored one-action view.
- `.devad/features/features.index.json`: generated feature machine index.
- `.devad/features/README.md`: generated human sitemap.
- one stable feature folder: `FEATURE.json`, compact README/spec, artifact
  index, and task/run links.
- Worker result and proof: exact lane/run paths linked by feature/task ID.

Do not use local-only artifact links. Large proof uses private immutable
storage or Git LFS with path/URL, SHA-256, and meaning. Ordinary durable
Markdown/JSON stays in Git.

Managed feature slugs use lowercase ASCII letters, digits, and hyphens, are at
most 24 characters, use at most six levels, and keep repository-relative paths
at or below 160 characters.

## Proof And Claims

- `PASS`: current evidence for exact scope and SHA.
- `PARTIAL`: useful work exists; finish line is not proven.
- `BLOCKED`: exact missing fact or failed hard gate.
- `Unknown`: exact check needed.
- Worker and sidecar claims are evidence to validate, not proof.
- Copied files, one unit test, source push, or deployment alone do not prove
  production readiness.

## Compact Chat, Full Quality

Keep visible chat and progress thinking short, normally one to three lines.
This does not limit reasoning quality, code, tests, prompts, technical docs,
security analysis, proof, or durable task/result contracts. Never hide
uncertainty or reduce verification for shorter chat.

## Manifest-First Durable Routing

Read `.devad/ROUTER.md`, then only the smallest linked file needed. A feature
starts at `.devad/features/<feature-id>/TASK.md`; a Worker receives the exact
machine task packet.

- Controller owns active loop-lite state and generated indexes/views.
- Linx owns only immutable newest owner packet plus real transport receipt.
- Worker owns claimed product files and its exact result/run evidence.
- Thinx owns one decision file.
- `devad-memory` owns `.devad/memory`, never active routing truth.
- `codex-token-budget` owns usage/benchmark evidence, never product decisions.

STATUS.md and HANDOFFS.md are generated human views, never parser authority.
Keep views compact and move detailed unique security, proof, commit, decision,
or blocker evidence into linked run files. Existing `.devad/manager/loop/`
files remain historical and are never rewritten during v6 migration.

## Owner Input Contract

Preserve every task-changing owner message and required attachment as an
immutable `OWNER_PACKET.json` with exact text, atomic requirements, source task
ID, attachment paths/hashes, and visual meaning.

Every receiving role must match the owner packet and each required attachment
hash before planning, coding, approval, PASS, or BLOCKED. Screenshots/images
must be viewed as binaries or through an approved visual Reader with owner
spot-check. A text summary, path, OCR, or filename alone is not proof of
transfer.
