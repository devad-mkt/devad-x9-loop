---
name: codex-x9-backup
description: Back up, verify, and restore personal Codex/X9 profile state to a user-configured private Git repository. Use for daily backup, format rescue, session or skill backup, profile restore, secret scanning, and verified Git backup sync.
---

# Codex X9 Backup

Preserve the local Codex profile needed for recovery without committing raw
auth tokens, cookies, install caches, or runtime payloads.

## Configure

- Profile root defaults to `$HOME`.
- The scripts live in this skill folder.
- Pass `-RepoPath <private-backup-clone>` for the local backup clone.
- Set `CODEX_X9_BACKUP_REMOTE` or pass `-RepoUrl` only when the clone must be
  created. Keep that remote private.
- Pass `-Python <python.exe>` when `python` is not on `PATH`.

## Commands

```powershell
& "$HOME\.codex\skills\codex-x9-backup\scripts\sync-codex-x9-backup.ps1" `
  -Mode DryRun -RepoPath "<private-backup-clone>"

& "$HOME\.codex\skills\codex-x9-backup\scripts\sync-codex-x9-backup.ps1" `
  -Mode Daily -Push -RepoPath "<private-backup-clone>"

& "$HOME\.codex\skills\codex-x9-backup\scripts\restore-codex-x9-backup.ps1" `
  -RepoPath "<private-backup-clone>" -TargetProfile "$HOME" -DryRun
```

## Rules

- Read `references/backup-policy.md` before changing scope or secret handling.
- Read `references/restore-checklist.md` before applying a restore.
- `PASS` requires redaction, manifest, secret scan, commit, push, and LFS proof.
- Restore stays `PARTIAL` until Codex shows restored tasks and project roots.
- Never print raw secrets, auth JSON, cookies, provider keys, or full matches.
- Project `.devad` remains source-controlled in its private project repo.
- Verify the X9 Loop Lite v6 README, source manifest, and benchmark ledger before
  calling an X9 profile backup complete.

## Status

- `PASS`: committed and pushed; redaction, scan, manifest, and LFS passed.
- `PARTIAL`: copied or committed locally, but push/app proof is missing.
- `BLOCKED`: secret scan, Git auth, repo access, LFS, or running Codex prevents
  the requested operation.
