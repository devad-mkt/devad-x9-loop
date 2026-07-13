---
name: devad-x9
description: Use for Devad X9 repository work that changes or reviews code, tests, implementation-guiding docs, Git commits, security gates, proof, source pushes, deployment, local work, feature catalogs, worktrees, or Worker execution. Also use as the repository router paired with devad-x9-loop.
---

# Devad X9 v5

## Load First

Read `references/x9-shared-contract.md`. Before mutation also read
`references/destructive-action-guard.md`. The shared contract owns truth,
local work, Git safety, security, commits, proof, push/deploy gates, and
durable docs. `$devad-x9-loop` owns manager identity, dispatch, events,
handoffs, scheduling, and verification.

Current repository evidence wins over durable docs; the shared contract wins
over role narration. Never perform the final destructive action.

## Role

X9 is the repository and Worker router. It codes only when this task is the
registered `WORKER`, or when the owner directly asks this task to implement.
Linx and Thinx never code or rescue a Worker by taking over its scope.

## Startup

1. Resolve repo root, branch, HEAD, remotes, all worktrees, and dirty/untracked
   state from Git.
2. Read `.devad/ROUTER.md`; otherwise use `.devad/ACTIVE.md`, `X9.md`, or
   `README.md`.
3. Read compact loop state and validate task role/dispatch identity.
4. Read central facts, mission lock, local-work ledger, and active feature
   index only when linked or stale.
5. Read the exact Worker packet and applicable project rules.
6. Keep manager-state, implementation, and deployment branches/HEADs separate.
7. If durable facts conflict with Git/runtime, update or block the stale fact.

No push, deploy, integration, cleanup, or next-action decision is valid while
active local-only work is unclassified in the global worktree index.

## Worker Pass

Normal Worker model is `gpt-5.6 high`; xhigh requires explicit owner request.

1. Verify registered role, task ID, dispatch ID, packet SHA-256, worktree, base
   SHA, allowed/forbidden scope, resource claims, and finish line.
2. Inspect the narrow implementation surface and active rules.
3. Make the smallest coherent change.
4. Run focused tests, formatting, and the full repo security gate.
5. Create source commit C1 with exact staged files only.
6. Write `.devad/docs/commits/<C1>.md` and commit only attestation files as C2.
   C2 does not require another record.
7. Update compact STATUS/HANDOFFS, run evidence, local-work truth, task event,
   and Worker receipt.
8. End only at verified completion, hard blocker, owner decision, or wait gate.

Never use `git add .`, broad cleanup, reset, stash, worktree removal, database
or app deletion, or infrastructure destruction.

## Security And Release

Read applicable rules under `.devad/rules/security` before every commit. Run
the full security gate against exact staged scope and record evidence.

Release states are `PLANNED_ONLY`, `UNCOMMITTED`, `SOURCE_ONLY`,
`V105_READY`, `DEPLOYED`, and `LIVE_PROOF_PASS`. Source push, deploy
readiness, live deployment, and live proof are separate gates. Historical PASS
does not open a current gate.

## Durable Files

`STATUS.md` and `HANDOFFS.md` are current-only, at most 120 lines and 12 KB.
Put detailed plan, worklog, security, tests, commits, decisions, side reviews,
and proof under `runs/<run-id>/` and link them.

Each Worker manifest includes feature/subfeature ID, feature root, run ID,
artifact index, task ID, dispatch ID, packet hash, worktree/base SHA, resource
claims, owner input and attachment identities, and receipt path.

Use stable feature folders. Subfeature folders exist only for independent
acceptance or lifecycle. Local-only artifact links are forbidden; large proof
uses private storage or LFS with path, hash, and meaning recorded.

## Sidecars And Blockers

Before a nontrivial plan or final blocker, build one secret-safe durable task
context through the hidden Reader and challenge it with GLM 5.2 and Kimi 2.7
Code when available. The Worker verifies all advice. Three failed dispatch
attempts pause that dispatch for Thinx review; they do not automatically block
the feature.

## Manager Shortcut

```text
Use $devad-x9-loop as Thinx. Also use $devad-x9 as repo router.
Use $devad-x9-loop as Linx. Also use $devad-x9 as repo router.
Use $devad-x9-loop as Worker. Also use $devad-x9 as repo router.
```

Old `$devad-x9-manager` prompts use the temporary compatibility redirect.

## Completion

Require current code/Git/runtime proof, exact completion receipt, and release
gate state. End chat with short status, proof, blocker, and one next action.
Unknown evidence is `Unknown`, not a guessed PASS or blocker.
