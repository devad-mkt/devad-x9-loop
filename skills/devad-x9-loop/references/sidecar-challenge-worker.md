# SIDE Challenge Reviewer

`SIDE` means a packet-only sidecar reviewer, usually GLM or Kimi. Use this when
a long-running manager or Worker may be losing focus, a blocker is about to be
claimed, a proof path failed, or Codex needs a clearer outside read
without giving another agent the full chat history.

## Core Rule

Create a saved, sanitized packet from current repo truth and evidence. Give
SIDE the packet only. Do not give it the full Codex chat. For Worker plan and
blocker challenges, follow worker-sidecar-context-bridge.md: hidden Luna medium
builds the packet, then both GLM 5.2 and Kimi 2.7 Code review it.

This keeps SIDE focused like GLM/Kimi in the AI-App Task builder thread:
fresh context, full facts, no chat drift, no emotional baggage from repeated
failures.

## When To Use

| Trigger | SIDE action |
| --- | --- |
| High-risk blocker about to be claimed | Ask one SIDE reviewer to challenge the blocker first. |
| Same proof path failed once and second failure would block | Ask for alternate proof paths and stop conditions. |
| Manager thread is long-running or compacted | Ask for a packet-only review before major routing. |
| Worker keeps patching but progress is unclear | Ask for restart vs continue decision. |
| UI/taste/source parity is fuzzy | Ask for acceptance checklist or rubric. |
| Billing/security/deploy risk | Ask for risks and stop rules, not code. |

Do not use SIDE for tiny obvious fixes, direct test failures, or when the
packet would require secrets/customer/provider data.

## Routes

Prefer `$devad-assistant` routes when available.

| Model | Best use |
| --- | --- |
| `opencode-go/kimi-k2.7-code` | Strict migration decision, safest next step, blocker challenge. |
| `opencode-go/glm-5.2` | Test matrix, acceptance checklist, architecture critique. |

Use one SIDE reviewer by default. Use both GLM and Kimi only when:

- the user approved multi-model review,
- the blocker is high-risk,
- or the prior local attempt failed and a bad blocker would stop useful work.

If model/auth/quota/tooling fails, record `SIDECAR_UNAVAILABLE` once and do not
retry in a loop. Also update `.devad/manager/TOOL_LESSONS.md` with the failed
route and the next safe fallback.

For OpenCode-backed SIDE:

- use a saved sanitized packet only,
- prefer `$devad-assistant` when available,
- if the wrapper route fails, record `TOOL_FAILED:opencode-wrapper` and try one
  direct OpenCode route only when available,
- do not loop GLM/Kimi setup failures,
- save packet, output, and manager decision paths.

## Packet Location

Use one of:

```text
.devad/manager/sidecar/<lane>-<topic>-packet-YYYY-MM-DD.md
.devad/features/<feature>/sidecar/<lane>-<topic>-packet-YYYY-MM-DD.md
```

Outputs:

```text
.devad/manager/sidecar/<lane>-<topic>-kimi.md
.devad/manager/sidecar/<lane>-<topic>-glm.md
.devad/manager/sidecar/<lane>-<topic>-decision.md
```

Feature-local sidecar folders are also OK when the feature already owns that
path.

## Packet Shape

```md
# SIDE Challenge Packet: <lane/topic>

## Goal
<concrete outcome>

## Repo Truth
- Repo:
- Branch:
- HEAD:
- Dirty state:
- Worktree:

## Current Claim Or Blocker
<what Codex is tempted to claim>

## Verified Facts
- <local facts only>

## What Codex Tried
| Attempt | Result | Evidence |
| --- | --- | --- |

## Constraints
- Review only.
- Do not edit files.
- Do not run commands.
- Do not ask for secrets.
- Do not assume chat history.
- Use only this packet.

## Required Output
1. Is the blocker real?
2. What is the smallest safe next step?
3. What proof would change your mind?
4. Should we continue, restart lane, ask user, or stop?
5. Risks and stop conditions.
```

## Manager Decision

SIDE output is advice, not truth. The manager must compare SIDE advice
against repo evidence and write a decision:

```md
# SIDE Decision: <lane/topic>

| Reviewer | Useful | Main point | Risk |
| --- | --- | --- | --- |

Decision:
APPROVE_WORKER_CONTINUE | SOFT_BLOCKER_ROUTE | RESTART_LANE |
HARD_BLOCKER | OWNER_DECISION_REQUIRED | BLOCKED_NEED_USER |
BLOCKED_NEED_EVIDENCE | HARNESS_PRUNE | NO_ACTION

Reason:
<short, evidence-backed>
```

## Before Claiming Blocked

For high-risk or long-running lanes, do not claim final `BLOCKED` until one of
these is true:

- SIDE challenge was run and recorded,
- SIDE route was unavailable and recorded,
- blocker involves secrets/live access/user decision where SIDE would not
help,
- user explicitly said not to use SIDE.

If SIDE finds a safe next check, the manager records `SOFT_BLOCKER_ROUTE`
instead of asking the owner. SIDE unavailability is `SIDECAR_UNAVAILABLE` or
`TOOL_FAILED`, not a hard blocker while another safe route exists.

## Safety

- Never send `.env`, tokens, cookies, private keys, raw provider/customer/payment
  data, or raw production logs.
- Never send full old chat transcripts.
- Never let SIDE make final claims, merge decisions, deploy decisions, or
  production truth claims.
- Do not let SIDE edit files or run commands unless the user explicitly
  creates a separate bounded worker for that purpose.
