# Rollback

The installer keeps each replaced skill under:

```text
CODEX_HOME/x9-install-backups/<timestamp>/
```

It never deletes a failed installation. On validation or swap failure it moves
the candidate folders to `x9-install-failed` and restores the local backup.

Manual rollback:

1. Stop new X9 Loop routing and any direct callback routing.
2. Keep project loop files as evidence; they do not execute by themselves.
3. Move the current six skill folders aside through an owner-approved action.
4. Restore the timestamped folders to `CODEX_HOME/skills`.
5. Restart Codex and validate all six skill names.

The public package does not contain private pre-v6 archives. Keep your own
private backup and hash manifest before installation.
