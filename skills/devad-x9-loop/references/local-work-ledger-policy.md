# Local Work Ledger Policy

Use this when local dirty/untracked work, GitHub-vs-local gaps, source-only
work, stale handoffs, lost changes, deploy bridges, or "what next" decisions
matter.

## Purpose

`LOCAL_WORK_LEDGER.md` is the small current truth for work that exists locally
but may not be committed, pushed, bridged, deployed, or live-proofed.

GitHub and remote HEAD are incomplete truth when the ledger shows active-lane
local work.

## Location

```text
.devad/manager/LOCAL_WORK_LEDGER.md
```

Build or refresh with:

```powershell
$py = Join-Path $HOME '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$skill = Join-Path $HOME '.codex\skills\devad-x9-loop'
& $py (Join-Path $skill 'scripts\build_local_work_ledger.py') --repo '<project-root>' --write
```

## Release States

| State | Meaning | Manager rule |
| --- | --- | --- |
| `PLANNED_ONLY` | Docs/plans/proof exist but not code-live. | Do not count as shipped. |
| `UNCOMMITTED` | Local dirty or untracked implementation/docs exist. | Classify before push/deploy. |
| `SOURCE_ONLY` | Source branch has it, live branch may not. | Bridge/deploy proof needed. |
| `V105_READY` | Exact v105 branch has intended SHA. | Deploy gate still required. |
| `DEPLOYED` | Dokploy/live target has exact SHA. | Browser/live proof still required. |
| `LIVE_PROOF_PASS` | Live proof passed for exact SHA. | Only that SHA/scope is done. |

## Required Current Block

Every Worker `CURRENT_STATUS` must include:

```md
- Local work: PASS | PARTIAL | BLOCKED
```

Meanings:

| Status | Meaning |
| --- | --- |
| `PASS` | Active-lane local work is absent or deliberately classified in the ledger. |
| `PARTIAL` | Useful local work exists but is not fully committed, pushed, bridged, deployed, or proofed. |
| `BLOCKED` | Local work cannot be classified safely. |

## Hard Gates

- No source push claim with `Local work` other than `PASS`.
- No deploy readiness claim with `Local work` other than `PASS`.
- No live deploy claim with `Local work` other than `PASS`.
- No done claim from GitHub/remote alone while the ledger shows active-lane
  local work.
- No `git add .`, delete, cleanup, reset, stash, or broad stage to "fix" the
  ledger.

## Manager Pass Rule

Before choosing "what next":

1. Read `CENTRAL_FACTS.md`.
2. Read `MISSION_LOCK.md`.
3. Read `ANSWERED_DECISIONS.md`.
4. Read `TOOL_LESSONS.md`.
5. Read `LOCAL_WORK_LEDGER.md`.
6. If the ledger is missing/stale and git is dirty, rebuild it before routing.

If the ledger says `Active-lane local work: YES`, the next action must be one
of:

```text
REQUEST_LOCAL_WORK_LEDGER:<lane>
CLASSIFY_LOCAL_WORK:<lane>
APPROVE_REVIEW_DIFF:<lane>
SOFT_BLOCKER_ROUTE:<lane>:<read_only|top|side|smaller_proof>
```

## Do Not Delete

Old `.devad` files are history. Do not delete or clean them to reduce noise.
Classify them as inventory-only unless they are exact current-lane evidence.
