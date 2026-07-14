# Migration

1. Validate the package, source manifest, and Loop Lite v6 shadow reconciliation.
2. Run scripts/migrate_project.py without --apply.
3. Confirm the dry-run lists only missing ROUTER, loop-lite state, activation
   packet, and OLD report.
4. Re-run with --apply. Existing files are preserved, never overwritten.
5. Run shadow validation against `.devad/manager/loop-lite/SNAPSHOT.json` and
   its JSON contracts. Keep `.devad/manager/loop/` as historical evidence.
6. Reuse the existing Thinx. Do not message, rename, retire, or otherwise
   change the current Linx before shadow validation passes.
7. After validation, create a fresh Linx v6 from the generated activation
   packet. It starts from the snapshot, not old task chat or Markdown views.
8. Preserve every old manager file and every worktree. Migration never moves,
   deletes, cleans, resets, stashes, deploys, or activates an existing task.

The first v6 action is reconciliation only. No current Linx or Worker message
is sent until shadow validation is recorded.
