---
name: devad-x9
description: Use for Devad X9 repository work that changes or reviews code, tests, implementation-guiding docs, Git commits, security gates, proof, source pushes, deployment, local work, feature catalogs, worktrees, or Worker execution. Also use as the repository router paired with devad-x9-loop.
---

# Devad X9 v6

## Load First

Read `references/x9-shared-contract.md`. Before mutation also read
`references/destructive-action-guard.md`. The shared contract owns truth,
local work, Git safety, security, commits, proof, release gates, and durable
docs. `$devad-x9-loop` owns deterministic identity, dispatch, callbacks,
claims, dependencies, and recovery.

Current repository evidence wins over durable narration. Never perform the
final destructive action.

## Role

X9 is the repository and Worker router. It codes only when this task is the
registered `WORKER`, or when the owner directly asks this task to implement.
Linx and Thinx never code or rescue a Worker by taking its scope.

## Startup

1. Resolve repo root, branch, HEAD, remotes, every worktree, and staged,
   unstaged, untracked, and committed paths from current Git.
2. Read `.devad/ROUTER.md` and
   `.devad/manager/loop-lite/SNAPSHOT.json`.
3. Read the exact `TASK.json`; verify task, Worker, dispatch, packet, worktree,
   base SHA, claims, resources, dependencies, gates, and finish line.
4. Read only linked central facts, mission lock, local-work truth, feature
   contract, and applicable project/security rules.
5. Keep manager-state, implementation, integration, deployment, and live-proof
   branches/HEADs separate.
6. If durable facts conflict with Git/runtime, stop the stale route and run
   deterministic reconciliation. Never patch orchestration state manually.

No push, deploy, integration, cleanup, or next-action decision is valid while
active local-only work is unclassified.

## Worker Pass

Normal Worker model is `gpt-5.6 Terra high`. Use Terra xhigh only when the
owner explicitly asks.

1. Verify identity and exact claims before editing.
2. Inspect the narrow implementation surface and active rules.
3. Make the smallest coherent change inside owned files.
4. If a new file is required, request `CLAIM_EXPANSION_REQUEST` first.
5. Run focused tests, formatting, and the full repository security gate.
6. Reconcile actual staged, unstaged, untracked, and committed paths. Any path
   outside claims is `SCOPE_BREACH` and cannot integrate.
7. Create source commit C1 from exact staged files only.
8. Write `.devad/docs/commits/<C1>.md` and commit only attestation files as C2.
   C2 does not require another record.
9. Write the exact hashed `RESULT.json` with changed files, proof, C1/C2, and
   blocker state, then send one direct callback.

Never use `git add .`, broad cleanup, reset, stash, worktree removal, database
or app deletion, or infrastructure destruction.

## Security And Release

Read applicable rules under `.devad/rules/security` before every commit. Run
the full security gate against exact staged scope and record evidence.

Release states are `PLANNED_ONLY`, `UNCOMMITTED`, `SOURCE_ONLY`,
`V105_READY`, `DEPLOYED`, and `LIVE_PROOF_PASS`. Source push, deploy
readiness, live deployment, and live proof are separate exact-SHA gates.
Historical PASS does not open a current gate.

## Durable Files

`SNAPSHOT.json`, `TASK.json`, and `RESULT.json` are machine authority.
`STATUS.md` and `HANDOFFS.md` are generated human views, never parser
authority. Detailed plan, worklog, security, tests, commits, decisions,
side reviews, and proof remain under `runs/<run-id>/` and are linked.

Use stable feature folders. Subfeatures exist only for independent acceptance
or lifecycle. Local-only artifact links are forbidden; large proof uses
private storage or LFS with path, hash, and meaning recorded.

## Sidecars And Blockers

Before a nontrivial plan or final blocker, use one bounded, secret-safe Reader
packet containing owner requirement, claims, relevant diff/proof, failure, and
one question. Run `opencode_doctor.py`. Ask configured GLM 5.2 and Kimi 2.7
Code at most once each when available. The Worker verifies all advice.

`TOOL_UNAVAILABLE` is nonblocking and never triggers a retry loop. Three
failed Worker attempts pause that task for Thinx review; they do not
automatically block the feature.

## Manager Shortcut

```text
Use $devad-x9-loop as Thinx. Also use $devad-x9 as repo router.
Use $devad-x9-loop as Linx. Also use $devad-x9 as repo router.
Use $devad-x9-loop as Worker. Also use $devad-x9 as repo router.
```

Old `$devad-x9-manager` prompts use the temporary compatibility redirect.

## Completion

Require current code, Git, test, security, runtime, and release-gate proof,
plus exact Worker-owned completion identity. Unknown evidence is `Unknown`,
not a guessed PASS or blocker. Keep visible chat short and point to durable
proof.
