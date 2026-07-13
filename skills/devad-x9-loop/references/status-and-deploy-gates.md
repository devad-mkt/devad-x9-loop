# Current Status And Deploy Gates

Use this file when a manager, worker, heartbeat, or handoff mentions PASS,
push, deploy, live proof, Dokploy, source branch, or stale handoffs.

## Current Status Is Authority

Every worker packet must have:

```text
.devad/manager/workers/<lane>/STATUS.md
.devad/manager/workers/<lane>/HANDOFFS.md
```

`STATUS.md` is the current truth. `HANDOFFS.md` keeps one compact current
handoff plus links to archived pass records. Older append-only sections are
historical only and should be rotated without deleting proof.

Managers must read in this order:

1. `STATUS.md`
2. top `CURRENT_STATUS` block in `HANDOFFS.md`
3. newest proof files
4. older handoff sections only for background

Never infer current PASS, deploy, or push status from old body text.

## Required Current Block

This block must be the first non-title block in both `STATUS.md` and
`HANDOFFS.md`:

```md
CURRENT_STATUS:
- Lane:
- Updated:
- Scope:
- Lane status: PLANNED | ACTIVE | CLAIMED_PASS | VERIFIED_PASS | PARTIAL | BLOCKED | FAILED | REJECTED | ABANDONED
- Mission lock: PASS | BLOCKED
- Central facts: PASS | BLOCKED
- Local work: PASS | PARTIAL | BLOCKED
- Security review: PASS | PARTIAL | BLOCKED | NOT_REQUIRED
- Security precommit: PASS | BLOCKED | NOT_REQUIRED
- Post-commit docs: PASS | BLOCKED | NOT_REQUIRED | NOT_COMMITTED
- Source push: PASS | BLOCKED | NOT_REQUESTED
- Deploy readiness: PASS | BLOCKED | WAIVED_BY_OWNER | NOT_REQUESTED
- Live deploy: PASS | BLOCKED | NOT_REQUESTED
- Live proof: PASS | BLOCKED | NOT_REQUESTED
- Latest commit:
- Attestation commit:
- Exact next action:
- Must not do:
```

If `Lane status` is missing, the manager must mark the lane
`MISSING_CURRENT_STATUS`, not guess from other fields.

## Gate Meanings

| Gate | Means | Does not mean |
| --- | --- | --- |
| `Lane status: CLAIMED_PASS` | Worker thinks scoped work is done. | Manager verified, pushed, merged, deployed. |
| `Lane status: VERIFIED_PASS` | Manager/evaluator verified scope and proof. | Live deploy happened. |
| `Local work: PASS` | Active-lane local-only work is absent or deliberately classified in `LOCAL_WORK_LEDGER.md`. | Remote/GitHub alone proves live state. |
| `Security precommit: PASS` | Commit gate used `.devad/rules/security` and passed or was safely documented. | Push or deploy is approved. |
| `Post-commit docs: PASS` | `.devad/docs` has the exact commit record. | Security proof passed by itself. |
| `Source push: PASS` | Intended source commit is on remote. | Dokploy picked it up. |
| `Deploy readiness: PASS` | Deploy may start for this exact SHA. | Live is already updated. |
| `Live deploy: PASS` | Dokploy reports the exact SHA deployed and health checks pass. | User-visible behavior passed. |
| `Live proof: PASS` | Required user-visible behavior passed for the exact deployed SHA. | Future deploys are safe. |

Plain `PASS` anywhere else is evidence only. Treat it as `CLAIMED_PASS` until
the current block and proof say otherwise.

## Hard Deploy Rule

No deploy may start unless `DEPLOY_GATE.md` exists for the lane or manager pass
and all checks are `PASS` or explicitly owner-waived.

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
| Active-lane local work classified | PASS | LOCAL_WORK_LEDGER.md |
```

Hard stops:

- If `DEPLOY_APPROVED:<sha>` is missing, deploy is `BLOCKED`.
- If the SHA in `DEPLOY_GATE.md` differs from `CURRENT_STATUS` latest commit,
  deploy is `BLOCKED`.
- If sidecar metadata, pgvector, n8n proof, provider secrets, branch policy, or
  live proof are unknown, deploy is `BLOCKED` unless owner-waived in
  `DECISIONS.md` and `DEPLOY_GATE.md`.
- `CLAIMED_PASS`, `Source push: PASS`, or a green test does not authorize deploy.
- `Deploy readiness: PASS` requires `Local work: PASS`.

## Push Gate

Source push and deploy are separate gates.

Before source push:

- exact staged files are listed,
- `git diff --cached --name-only` contains only lane-owned files,
- branch/head/base are written in `STATUS.md`,
- security review is complete for touched trust boundaries.
- `Local work: PASS` is written in `STATUS.md` and backed by
  `.devad/manager/LOCAL_WORK_LEDGER.md`.

If the branch is ahead by more than one commit, or the range contains commits
from more than one lane, require one of:

```text
PUSH_APPROVED_BY_OWNER:<branch>:<sha>
PUSH_REVIEWED_BY_MANAGER:<branch>:<sha>
```

Without that approval, push is `BLOCKED`, even if tests pass.

## Outbound Fetch Security Gate

For code touching outbound HTTP, scraping, URL import, RSS, webhooks, browser
automation, n8n callbacks, provider fetch, or any server-side URL handling:

1. write the threat review before code,
2. verify DNS rebinding, localhost/private IP, redirect, timeout, size, and
   content-type controls after code,
3. set `Security review: PASS` only with exact proof.

If this review is missing, deploy readiness is `BLOCKED`.

## Heartbeat Gate

Heartbeat may monitor and notify by default. It must not push, deploy, merge,
route new implementation work, or mark PASS unless the current status block and
the exact gate file authorize that action.

If a heartbeat sees stale or missing `STATUS.md`, it must stop with:

```text
BLOCKED_STALE_STATUS:<lane>
```
