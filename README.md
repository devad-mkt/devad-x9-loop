# Devad X9 Loop Codex Kit v5

Public, file-first orchestration for long Codex projects. The kit keeps X9
execution safety, identifies every task by durable ID, and resumes work through
bounded events instead of chat history or constant polling.

## Quick Install

```powershell
.\scripts\install-suite.ps1 -CodexHome "$HOME\.codex"
.\scripts\install-suite.ps1 -CodexHome "$HOME\.codex" -Apply
```

The first command is a dry run. The second backs up current folders, validates
all six skills, swaps them, and rolls back if validation fails.

## Roles

| Role | Default model | Job |
| --- | --- | --- |
| Linx | `gpt-5.6 high` | Owner bridge and routing |
| Thinx | `gpt-5.6 xhigh` | File-only planning and review |
| Thinx high-risk | `gpt-5.6 ultra` | One hard security, money, architecture, or conflict pass |
| Worker | `gpt-5.6 high` | One bounded implementation packet |
| Worker xhigh | `gpt-5.6 xhigh` | Owner-requested hard implementation |
| Reader/CHUNK/SIDE | Bounded | Extract, split, or challenge exact context |

The manager skill is `devad-x9-loop`. The small `devad-x9-manager` skill keeps
older prompts compatible through v5.

## How Linx Wakes

Files do not wake Linx. After Linx dispatches Thinx or a Worker, the receiver
writes its durable receipt and sends one `EVENT_READY` signal. It targets the
same Linx task ID. Linx verifies role, dispatch ID, packet hash, receipt path/hash,
unseen event, and manager lock before one new pass.

Recurring 15/19-minute pickup is forbidden. It wastes no-change turns and can
overlap owner work. An owner-requested one-shot fallback is allowed only for a
delayed owner decision or an external condition that cannot callback.

This keeps the useful X7 idea - deterministic inbox/outbox and durable handoff
state - while removing timer polling. Files remain truth; direct task messaging
supplies the wake.

<details>
<summary>Existing X9 Worker features</summary>

- Truth and mission locks; current Git/runtime evidence wins.
- Local-work ledger, release states, worktree preservation, and exact staging.
- Full security gate before C1; C2 records C1 without recursive attestation.
- Separate push, deploy-readiness, deployment, and live-proof gates.
- Destructive-action guard, compact Worker state, feature catalog, and proof.

</details>

<details>
<summary>Existing X9 Manager features</summary>

- Thinx file-only verified-read receipts and locked task reuse.
- Linx owner message/attachment hashing and collaborative handover.
- Manager mutex, answered decisions, tool lessons, and one execution authority.
- Secret-safe Reader context plus GLM/Kimi challenge before hard blockers.
- Model benchmarks, automatic Ultra return, and verified direct callback pickup.

</details>

<details>
<summary>New Loop v5 features</summary>

- History-free Linx routing from one compact capsule and unseen events.
- Immutable task-ID roles; task titles are display text only.
- `TITLE_ROLE_MISMATCH` when a title conflicts with the registered role.
- One `dsp-<uuid>` per packet, SHA-256 identity, attempts, and receipts.
- Task graph, resource claims, event cursor, decision gates, scoped completion.
- Two coding Workers by default; promotion to three needs measured proof.
- Three-failure circuit breaker pauses one dispatch for Thinx review.

</details>

<details>
<summary>Safety and deployment gates</summary>

Security precedes C1. C2 contains only the C1 attestation. Push, deploy
readiness, live deploy, and live proof are separate gates. Final destructive
actions remain owner-run.

</details>

<details>
<summary>Supporting skills</summary>

- `codex-x9-backup`: configurable private profile backup and secret scan.
- `codex-token-budget`: model, task, heartbeat, and loop cost diagnosis.
- `devad-memory`: historical retrieval, never active routing truth.

</details>

<details>
<summary>Retired and rejected mechanisms</summary>

- No broad X7 polling, role inference from titles, or blind resend.
- No Orca runtime/database truth, four-Worker default, two-second model polling,
  automatic Worker kill, or age-only worktree moves.

</details>

<details>
<summary>Migration and rollback</summary>

Run `scripts/migrate_project.py` without `--apply` first. It creates only
missing routing/loop state, preserves old manager evidence, and never moves a
worktree. See `docs/MIGRATION.md` and `docs/ROLLBACK.md`.

</details>

## Public Distribution

This repository intentionally omits private rollback archives, project commit
records, security evidence, local model-result runs, credentials, and
machine-specific paths. The benchmark harness and blank ledger remain so each
installation can collect its own results.

`features.registry.json` classifies retained, moved, adapted, new, and retired
features. Validation fails when an old feature has no migration classification.
