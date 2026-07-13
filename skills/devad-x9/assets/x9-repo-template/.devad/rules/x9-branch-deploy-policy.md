# X9 Branch And Deploy Truth

Use for branch choice, resume, handoff, deploy, live proof, hotfix, and any
task where GitHub/Dokploy freshness affects the correct source branch.

## Hard Rules

- `<project-root>` on `<implementation-branch>`
  is the X9 feature source.
- `<deployment-branch>` is live/Dokploy deploy-only
  unless the user explicitly asks for a live hotfix.
- Never start new X9 feature work from the v105 branch.
- Any live hotfix made on v105 must be cherry-picked, merged, or recorded as a
  blocker against the X9 feature branch before final handoff.
- If the user asked to deploy, live-proof, or verify production, do not mark
  the goal complete while Dokploy is still serving a branch that lacks the
  implementation. `/health 200` only proves the old live app is healthy.
- Treat `.devad/ACTIVE.md`, handoffs, chat IDs, and GitHub branch page
  timestamps as clues. Exact Git SHAs and fresh Dokploy safe fields decide.
- A checkout whose path contains `deploy`, `bridge`, `v105`, or `x9w\v105`, or
  whose Git state is detached HEAD or the v105 deploy branch, is not a normal
  X9 workspace. It must pass the bridge classification below before any action.

## Fresh Check

Before branch/deploy decisions:

```powershell
git fetch origin --prune
git status --short --branch
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
git ls-remote --heads origin <implementation-branch> <deployment-branch>
```

For deploy/live-proof work, also read `.devad/rules/devad-deploy-dokploy.md`
and `.devad/tooling/dokploy/HOW-TO-USE.md`, then verify safe fields only:

```text
Dokploy app name/slug/id
Dokploy configured branch
latest deployment id/status/title/time
current remote deploy branch SHA
```

Do not print secrets or full Dokploy JSON.

## Bridge Classification

Before coding, classify the current checkout:

| State | Test | Action |
| --- | --- | --- |
| `X9_SOURCE` | path is `<project-root>`, branch is `<implementation-branch>`, not detached | normal X9 work |
| `DEPLOY_BRIDGE_ACTIVE` | clean v105 bridge created for a named X9 commit, before push/deploy | apply only that committed X9 change and verify |
| `DEPLOY_BRIDGE_LOCKED` | bridge after push/deploy/proof, or old bridge behind current v105 | inspect/verify only, no edits |
| `ORPHAN_PATCH` | dirty v105/deploy/bridge/detached checkout with uncommitted work | export diff/report, port to X9 or discard |

If classification is not `X9_SOURCE`, do not start new feature, debug, docs,
or recovery coding. The only allowed bridge actions are:

- inspect current state
- export a diff or file inventory
- verify deploy/health/proof
- cherry-pick or reapply a previously committed X9 commit into a clean bridge

If a bug is found after deploy, return to `<project-root>`, make and
push a new X9 commit, then create a fresh bridge from the current v105 remote
tip. Never continue editing the already-deployed bridge.

## Decision

| Work type | Correct base |
| --- | --- |
| New X9 feature, migration, UI/backend cleanup, provider proof code | `core-x9` / X9 feature branch |
| Live deploy proof of already-pushed code | verify Dokploy selected branch and exact remote SHA first |
| Production hotfix | v105 only when explicitly requested, then reconcile back to X9 |
| Worker chat handoff | report local branch/HEAD, remote branch SHAs, dirty files, touched paths, and whether v105/X9 diverged |

If X9 and v105 diverge, stop feature work on v105 and report the reconciliation
needed before merge/deploy.

## Deploy Closure Gate

When the user requested deploy, live proof, or production verification and
Dokploy is pinned to v105 while implementation is on X9, choose exactly one:

1. Controlled deploy bridge: commit/push the X9 implementation, create a clean
   temporary deploy worktree from `origin/<deployment-branch>`,
   cherry-pick or reapply only the implementation commits, run focused tests,
   push v105, trigger Dokploy, verify `/health` and required browser/API proof,
   record exact X9 commit -> v105 bridge commit mapping, then mark the bridge
   `DEPLOY_BRIDGE_LOCKED`. If reconciliation back to X9 is missing, record it
   as a blocker before any new feature work.
2. Owner branch switch: stop and ask for explicit approval to change Dokploy to
   deploy the X9 branch. Do not switch it silently.
3. Blocked handoff: if neither path is safe, stop with `CODE_READY_DEPLOY_BLOCKED`,
   list exact commits/files/tests, and say production is not running this change.

Never close a goal as complete for deploy/live-proof work unless the deployed
commit/branch contains the implementation and the requested proof passed.

## Dirty Bridge Recovery

When a bridge is `ORPHAN_PATCH`:

1. Do not commit or deploy from it.
2. Export `git diff --binary` plus `git status --short --branch` to a patch
   report outside the bridge, or summarize exact files if the user only asked
   for analysis.
3. Restart in `<project-root>`.
4. Apply-check or manually port only relevant changes.
5. Verify on X9, commit/push X9, then use a fresh v105 bridge only if deploy is
   required.
