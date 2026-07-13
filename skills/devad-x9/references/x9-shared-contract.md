# X9 Shared Contract

This is the single normative contract shared by `devad-x9` and
`devad-x9-loop`. The temporary `devad-x9-manager` name redirects here. Read this before code, routing, commit, push, deploy, or done
claims.

## Authority

Use this order:

1. Current Git, filesystem, test, browser, provider, and runtime evidence.
2. `CENTRAL_FACTS.md`, `MISSION_LOCK.md`, and `LOCAL_WORK_LEDGER.md` after they
   have been checked against current evidence.
3. Current Worker STATUS and packet.
4. Current feature contract and task files.
5. Historical handoffs and chat only when a durable fact points to them.

Never let an old PASS, remote branch, or chat summary override current local
work or runtime evidence.

## Manager Role Boundary

- Linx captures owner input, maintains manager truth, routes roles, validates
  receipts, and reports verified status. Linx never codes or generates product,
  preview, test, proof, commit, push, bridge, or deploy artifacts.
- Thinx makes file-only strategy and contradiction decisions. It never codes
  or manages Workers directly.
- Worker performs implementation and proof inside its packet.
- A stalled Worker is corrected, resumed, or replaced after durable handoff;
  Linx never takes over its work.

An owner correction, contradiction, "why" question, historical reconstruction,
acceptance mismatch, screenshot/UI judgment, or implemented/deployed claim is
`JUDGMENT_REQUIRED`. Linx must preserve the exact owner input and route current
evidence to locked Thinx. If evidence is incomplete, answer `Unknown` plus the
exact check; never make a negative or completion claim from summary memory.

## Manager Pass Mutex

Every direct manager pass and heartbeat uses
`.devad/manager/MANAGER_PASS_LOCK.md`. One pass owns the lock at a time. The
lock records pass ID, source (`OWNER` or `HEARTBEAT`), start, expiry, status,
and newest owner-input ID.

- If another unexpired pass is active, return `SKIP_ACTIVE_MANAGER_PASS`.
- A newer owner message outranks and cancels heartbeat work.
- A heartbeat never overlaps an owner turn or another wake.
- Release the lock at final chat or mark it `STALE` only after expiry and a
  read-only task-status check.
- A stale lock never authorizes mutation or a second implementation action.

## Truth Lock

Before choosing what is next, record or verify:

```md
- Repository root:
- Manager-state branch:
- Manager-state HEAD:
- Implementation branch:
- Implementation HEAD:
- Deployment branch:
- Deployment HEAD:
- Active lane:
- Feature ID:
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

Do not compare the manager-state checkout with the implementation branch as if
they are one branch. Each branch field must name its own HEAD.

## Local Work

`LOCAL_WORK_LEDGER.md` is required when the checkout is dirty or an active lane
contains untracked, uncommitted, source-only, or deployment-only work.

The ledger records `Checkout role`, `Checkout branch`, and `Checkout HEAD`.
The role is `MANAGER_STATE`, `IMPLEMENTATION`, `DEPLOYMENT`, or `OTHER`; never
rename an implementation checkout as the manager-state checkout.

Classify each active lane as:

- `PLANNED_ONLY`
- `UNCOMMITTED`
- `SOURCE_ONLY`
- `V105_READY`
- `DEPLOYED`
- `LIVE_PROOF_PASS`

GitHub is not complete truth while active-lane local work exists. Do not push,
bridge, deploy, or claim done until local-only work is classified.

## Worktree Discipline

`core-x9` (or the declared manager-state checkout) is the durable routing and
documentation home. An implementation worktree is a temporary isolated copy,
not a second project or hidden source of truth.

Before creating, routing, or reusing a worktree, read
`.devad/manager/WORKTREE_REGISTRY.md`. Linx maintains it from `git worktree
list --porcelain` and active Worker packets. Each row records feature ID, lane,
path, branch, HEAD, local-work state, purpose, and preservation state.

- Reuse the existing active worktree for the same feature ID.
- Allow one active implementation worktree per feature ID.
- A second worktree needs `PARALLEL_WORKTREE_OK:<feature>:<reason>` from the
  owner or a documented non-overlapping integration/review requirement.
- Use a stable short path such as `x9w/<feature-slug>`; do not make timestamped
  copies for ordinary retries, reviews, or model changes.
- Before a terminal worktree can be retired, classify its local work, preserve
  its commit/remote/artifact facts in the registry, and mark `ARCHIVED_SAFE`.
- Codex never removes a worktree. It prepares an owner-run destructive request
  only after the registry says `ARCHIVED_SAFE` and the owner approves.

If the registry is missing or stale, block new worktree creation with
`WORKTREE_REGISTRY_STALE`; rebuild it before routing.

## Exact Scope

- Use exact allowed files and exact staging.
- Never use `git add .` in a shared or dirty checkout.
- Never reset, clean, delete, overwrite, uninstall, prune, drop, truncate,
  force-push, or remove data, apps, services, containers, or volumes from
  Codex. Read `destructive-action-guard.md`; prepare an owner-run request.
- Never modify unrelated user work.
- A source push is not deploy approval. Deploy readiness, live deploy, and live
  proof are separate gates.

## Destructive Actions

Before any mutating pass, read `destructive-action-guard.md` and classify the
pass as `Destructive guard: NOT_REQUIRED`, `OWNER_RUN_REQUIRED`, or `BLOCKED`.

Chat approval is not executable authorization. Codex may create backups,
inventories, restore proof, and `DESTRUCTIVE_REQUEST.md`, but the owner must run
the exact final destructive command outside Codex. Thinx, Linx, Worker,
Reader, CHUNK, SIDE, automations, and subagents cannot waive this rule.

For an existing file, recheck its Git blob or SHA-256/size/last-write identity
immediately before writing. Stop on mismatch instead of overwriting concurrent
work.

## Security Before Commit

For `<project-root>` changes to app code, runtime-affecting tests,
CI/deploy gates, or implementation-guiding docs:

1. Read `.devad/rules/security/README.md` and its complete routed read order.
2. Identify touched trust boundaries and risk families.
3. Stage exact files only.
4. Run:

```powershell
composer security:precommit
git diff --cached --name-only
git diff --cached --check
```

5. Run focused tests and proof from the security proof matrix.
6. Run a staged secret check. Never commit secrets, cookies, auth codes, raw
   provider payloads, customer/payment data, private logs, or `.env` values.

If a required check is missing or fails, set `Security precommit: BLOCKED` and
do not commit.

## Commit And Attestation

Use a finite two-commit protocol:

1. After the security gate, create source commit `C1`.
2. Create `.devad/docs/commits/<date>-<lane>-<short-C1>.md` containing the exact
   C1 SHA, branch, files, security impact, proof, blocks, and next action.
3. Commit that record as `C2` with message `docs(x9): attest <short-C1>`.
4. C2 is `ATTESTATION_ONLY` only when its staged files are limited to the C1
   commit record and directly required current-status pointers.
5. An `ATTESTATION_ONLY` commit does not require a third commit record. It still
   requires exact staging, diff check, and secret check.
6. Validate C1 and C2, then push them together. Never push C1 alone when the
   post-commit record is required.

Required commit record fields:

```md
Commit: <full C1 SHA>
Branch: <implementation branch>
Worker lane: <lane>
Security precommit: PASS | BLOCKED | NOT_REQUIRED
Attestation commit: <full C2 SHA or PENDING before C2>
Files committed:
Security impact:
Proof:
Remaining blocks:
Next:
```

`Post-commit docs: PASS` is valid only when a tracked record mentions C1. If no
commit happened, use `Latest commit: NONE` and `Post-commit docs: NOT_COMMITTED`.

## Push And Deploy

Before source push:

- local intended HEAD and commit range are known;
- security and attestation gates pass;
- active local work is classified;
- the remote target and branch policy are verified;
- no unrelated commits are included.

Before deploy:

- exact deploy SHA and deployment branch are recorded;
- deploy approval applies to that SHA;
- dependencies and migrations are PASS or owner-waived;
- rollback and live-proof plans exist;
- Dokploy source branch and environment are verified.

After deploy, verify health plus the real user-visible behavior. Deployment
success without live behavior proof is not completion.

## Durable `.devad` Truth

Important Markdown and JSON are tracked in the private Git repository.
`.devad` must remain excluded from production images and public artifacts.

Feature truth uses:

- `.devad/features/features.index.json` as generated machine index;
- `.devad/features/README.md` as generated human sitemap;
- one stable short feature folder with FEATURE.json, compact README, spec files,
  and an artifact index;
- worker packets under `.devad/manager/workers/`, linked by feature ID.

Do not duplicate Worker STATUS inside feature folders. Do not use local-only
artifact links. Important large artifacts require Git LFS or private immutable
storage plus path/URL, SHA-256, and proof meaning. Ordinary durable Markdown
and JSON stay in Git and do not need S3.

Managed feature slugs use lowercase ASCII letters, digits, and hyphens, are at
most 24 characters, have at most six levels under `.devad/features`, and keep
repository-relative paths at or below 160 characters.

## Proof And Claims

- `PASS` requires current evidence for the exact scope and SHA.
- `PARTIAL` means useful work exists but the finish line is not proven.
- `BLOCKED` names the missing fact or failed gate.
- `Unknown` names the check needed.
- A worker claim is evidence to validate, not proof by itself.
- Never call copied files, a passing unit test, a source push, or a successful
  deploy production-ready without the required acceptance and live proof.

## Compact Chat, Full Quality

Keep visible chat and visible thinking text short, normally one to three lines
for progress. Use small tables only when they help. Do not repeat old context.

This limit does not apply to internal reasoning quality, code, tests, prompts,
technical docs, security analysis, proof, or durable handoffs. Never reduce
verification or hide uncertainty to make chat shorter.

## Manifest-First Durable Routing

When `.devad/ROUTER.md` exists, read it first and then only the smallest linked
file needed. A feature starts at `.devad/features/<feature-id>/TASK.md`; a
Worker lane starts at
`.devad/manager/workers/<lane>/ROUTER.md`.

Ownership is strict:

- Linx owns manager current truth, indexes, and Worker packet shells.
- Worker owns only its lane STATUS.md, HANDOFFS.md, current run details, and
  affected feature evidence.
- Thinx owns decision pass files only.
- devad-memory owns `.devad/memory`, not active routing truth.
- codex-token-budget owns benchmark/usage evidence, not product decisions.

STATUS.md and HANDOFFS.md contain current truth only. Keep each at or below 120
lines and 12 KB. Before the cap, move replaced detail into the active
`runs/<run-id>/` folder and preserve relative links. Never drop unique
security, proof, commit, decision, or blocker evidence.

## Owner Input Contract

Linx preserves every task-changing owner message and required attachment under
`.devad/manager/owner-input/<input-id>/`. The bundle contains the exact owner
message, atomic requirements, attachment identities, and visual context.

Every receiving role must prove `OWNER_CONTEXT_RECEIPT: PASS` for the exact
request hash and each required attachment hash before planning, coding,
approval, PASS, or BLOCKED. Required screenshots/images must be viewed as
binaries or through an approved visual Reader with decision-owner spot-check.
A text summary, path, OCR, or attachment name alone is not proof the context
was transferred.
