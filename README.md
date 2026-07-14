# Devad X9 Loop Lite v6 Codex Kit

Production-oriented orchestration for long Codex work. A standard-library
controller owns identity, claims, dispatches, callbacks, and recovery. Models
still reason and code, but Linx no longer rewrites orchestration files or reads
history on every pass.

## Quick Install

```powershell
.\scripts\install-suite.ps1 -CodexHome "$HOME\.codex"
.\scripts\install-suite.ps1 -CodexHome "$HOME\.codex" -Apply
```

The first command is a dry run. Apply stages and validates all six skills,
backs up current folders, swaps them, and rolls back on failure.

## Roles

| Role | Model | One job |
| --- | --- | --- |
| Linx | `gpt-5.6-sol high` | Reconcile, read one action, transport, record result |
| Thinx | `gpt-5.6-sol xhigh` | File-only strategy or review |
| Thinx high-risk | `gpt-5.6-sol Ultra` | One hard decision, then return to xhigh |
| Worker | `gpt-5.6-terra high` | One exact task in one worktree |
| Worker xhigh | `gpt-5.6-terra xhigh` | Owner-requested hard implementation |
| Reader/CHUNK/SIDE | Bounded | Extract, split, or challenge; no authority |

The real manager skill is `devad-x9-loop`. Temporary `devad-x9-manager`
redirects old prompts. The existing Thinx task is reused.

## Fast Loop

```text
Owner/callback
  -> loopctl reconcile
  -> Linx reads ACTION.json
  -> one real transport
  -> loopctl record-delivery
  -> Worker event-scoped receipt + direct callback
```

No recurring heartbeat or frequent polling. A callback gets one retry, then
`CALLBACK_FAILED` and manual one-shot pickup. Existing v5 state stays as
historical evidence.

## Rollout

| Clean dispatches | Coding Workers | Rule |
| --- | ---: | --- |
| 0-2 | 1 | Shadow and first live passes |
| 3-9 | 2 | Exact non-overlapping claims |
| 10+ | 3 | Zero safety, identity, scope, or context incidents |

Three coding Workers are the maximum. Database, browser, runtime, integration,
deployment, and live proof remain serialized.

## Performance Gates

- Deterministic reconciliation: under five seconds.
- Routine Linx callback: median under 60 seconds, p95 under two minutes.
- At most one Linx model turn and one state transaction per event.
- No manual manager-state patches.
- Track wall time, prompt bytes, reads, writes, retries, compactions, and
  first-pass success.
- Real token telemetry only. Missing telemetry is `Unknown`; fallback lifetime
  totals are forbidden.

<details>
<summary>Existing X9 Worker features</summary>

- Current Git/runtime truth and mission lock.
- Local-work ledger, release states, worktree preservation, exact staging.
- Full security before C1; C2 attests C1 without recursive documentation.
- Separate source push, deploy readiness, deployment, and live-proof gates.
- Destructive-action guard, feature catalog, compact lane state, durable proof.

</details>

<details>
<summary>Existing X9 Manager features</summary>

- Immutable owner text and attachment hashes.
- Locked, file-only Thinx with verified read receipts.
- Answered decisions, tool lessons, central facts, and collaborative handover.
- Role identity by task ID, honest delivery receipts, and local-work checks.
- Secret-safe Reader plus bounded GLM/Kimi challenge before hard blockers.

</details>

<details>
<summary>New Loop v5 features retained</summary>

- Task and dispatch identity, packet SHA-256, dependency graph, decision gates.
- Role/title mismatch warning and worker-owned completion receipt.
- Direct event callback instead of recurring pickup.
- Worktree and resource ownership plus stale-completion rejection.

</details>

<details>
<summary>New Loop Lite v6 features</summary>

- `loopctl.py` standard-library controller with disposable SQLite cache.
- Tracked `SNAPSHOT.json` recovery truth below 8 KB.
- Generated `ACTION.json` below 4 KB: the only action Linx performs.
- Exact file/directory ownership and actual Git scope verification.
- One, two, then three Worker promotion based on clean dispatch evidence.
- Generated Markdown views; no Markdown parser authority or orphan locks.
- Content-addressed local-only owner packets/artifacts, bounded local-work packet, immutable event receipts, security/tests C1/C2 proof, and three-failure Thinx review.

</details>

<details>
<summary>Safety and deployment gates</summary>

The X9 shared contract remains authority. Security precedes source commit C1.
C2 contains only C1 attestation. Source push, deploy readiness, live deploy,
and live proof are separate. Final destructive actions remain owner-run.

</details>

<details>
<summary>Supporting skills</summary>

- `codex-x9-backup`: private profile backup, secret scan, restore proof.
- `codex-token-budget`: model, task, callback, and orchestration cost diagnosis.
- `devad-memory`: historical retrieval, never active routing truth.
- `devad-x9`: Worker coding, Git, security, proof, commit, and release gates.

</details>

<details>
<summary>Retired and rejected mechanisms</summary>

- No X7 broad polling, 15/19-minute heartbeat, sleep loop, or blind resend.
- No role inference from titles or completion from old handoffs.
- No Orca runtime, message bus, terminal groups, global reset, or database truth.
- No automatic Worker kill, worktree cleanup, or four-Worker default.

</details>

<details>
<summary>Migration and rollback</summary>

Run `scripts/migrate_project.py` without `--apply` first. Migration creates a
new `manager/loop-lite/` overlay and preserves all old manager files and
worktrees. Validate shadow reconciliation before activating a fresh Linx v6.
Reuse Thinx. Retire old Linx only after snapshot acknowledgement. See
`docs/MIGRATION.md` and `docs/ROLLBACK.md`.

</details>

`features.registry.json` classifies every inherited and new feature. Validation
fails if an old feature disappears without a migration status and test.
## How Linx Wakes

Files do not wake Linx. Worker or Thinx writes the durable event receipt, then
sends one EVENT_READY callback to the same Linx task ID. Linx verifies task,
role, dispatch, packet, event, and receipt identity before one new pass.

Recurring 15/19-minute pickup is forbidden. An owner-requested one-shot fallback
is allowed only when direct callback delivery fails or an external condition
cannot callback.

## Public Distribution

This repository intentionally omits private rollback archives, project
commit/security evidence, local model-result runs, credentials, private backup
remotes, and machine-specific paths. Configure CODEX_X9_BACKUP_REMOTE or pass
-RepoUrl for your own private backup repository.