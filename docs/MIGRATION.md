# Migration

1. Validate this package and `SOURCE_MANIFEST.sha256`.
2. Run `scripts/migrate_project.py` without `--apply`.
3. Confirm the dry run lists only missing router/loop state, activation packet,
   and worktree classification report.
4. Re-run with `--apply`. Existing files are preserved, never overwritten.
5. Review `ROLE_REGISTRY.json` by task ID. Never infer a role from its title.
6. Disable any old recurring manager automation and verify the pass lock is free.
7. Validate loop state and paste the activation packet into the intended Linx.

Migration preserves historical manager files. It does not message tasks, move
worktrees, clean, reset, stash, deploy, or activate Linx.
