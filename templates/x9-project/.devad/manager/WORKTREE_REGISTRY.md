# Worktree Registry

Read this before creating, routing, or retiring a worktree.

| Feature ID | Lane | Path | Branch / HEAD | Local work | Purpose | State | Next |
| --- | --- | --- | --- | --- | --- | --- | --- |
| _template_ | _lane_ | `x9w/<feature-slug>` | `<branch>` / `<sha>` | `PASS \| PARTIAL \| BLOCKED` | implementation \| review \| integration | ACTIVE \| ARCHIVED_SAFE | one action |

Rules:

- One active implementation worktree per feature ID.
- Reuse the listed path for retries and normal review.
- A second path needs `PARALLEL_WORKTREE_OK:<feature>:<reason>`.
- Before retirement: classify local work, record commit/remote/artifact facts,
  then mark `ARCHIVED_SAFE`.
- Never delete a worktree from Codex. Prepare an owner-run request only after
  `ARCHIVED_SAFE`.
