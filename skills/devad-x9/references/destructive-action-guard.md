# Destructive Action Guard

Read this before any pass that could delete, wipe, overwrite, uninstall, prune,
drop, truncate, reset, clean, or remove files, data, applications, services,
containers, volumes, branches, or infrastructure.

## Non-Negotiable Rule

Codex does not execute the final destructive action. This applies even when:

- the owner says `approved` in chat;
- a Worker, Linx, Thinx, SIDE, automation, hook, or old handoff says PASS;
- the target looks generated, unused, temporary, duplicated, or recoverable;
- Full Access is enabled.

A model can repeat an approval phrase, so a chat token is not a security
boundary. Codex may inspect, inventory, back up, test restore steps, and prepare
one exact owner-run request. The owner runs the final destructive command
outside Codex.

## Required Request

Write `DESTRUCTIVE_REQUEST.md` in the active Worker packet or owner-approved
operations folder:

```md
DESTRUCTIVE_REQUEST:
- Status: OWNER_RUN_REQUIRED
- Type: FILE | DATABASE | APP | SERVICE | CONTAINER | VOLUME | GIT | OTHER
- Exact target:
- Canonical target identity:
- Why removal is needed:
- Dependency/impact inventory:
- Dirty, untracked, or local-only state:
- Backup ID and immutable location:
- Backup hash or snapshot identity:
- Restore command:
- Restore proof: PASS | BLOCKED
- Exact destructive command:
- Expected result:
- Verification after owner action:
- Rollback:
- Created at:
- Expires at:
```

No wildcard, parent directory, drive root, home directory, workspace root,
repository root, `.git`, `.devad`, `.codex`, `.agents`, database server, shared
volume, or multi-app target is permitted in one request.

## Safe Preparation

- Files: inventory exact paths, size, hashes, Git status, links/junctions, and
  owners. Copy to versioned backup; do not move or quarantine the original.
- Git: use a new branch/worktree or recovery commit. Never clean, hard-reset,
  force-push, restore, or delete a branch from Codex.
- Database: use read-only counts and dependency checks. Create a verified dump
  or snapshot and a tested restore plan. Codex never runs DROP, TRUNCATE,
  DELETE, destructive migrations, or volume removal.
- App/runtime: export config and data, map dependencies, record resource IDs,
  and prove rollback. Codex never uninstalls apps or removes services,
  containers, volumes, namespaces, or Dokploy resources.
- Existing non-Git files: create a sibling candidate and compare it. Do not
  overwrite the original from a shell command.

## Concurrent Change Lock

Before editing any existing file, record its identity from the current read
(Git blob when tracked; otherwise SHA-256, size, and last-write time). Recheck
immediately before write. If it changed, stop with
`CONCURRENT_CHANGE_BLOCKED:<path>` and reread; never overwrite another task's
newer work.

## Machine Guard

The packaged managed policy disables Full Access, keeps read-only/workspace
profiles, and runs
`managed-guard/x9_destructive_guard.py` as a `PreToolUse` hook.

The hook is defense in depth, not a complete OS boundary. Keep versioned,
offline or immutable backups for irreplaceable data.
