# Codex X9 Restore Checklist

## Dry Run

```powershell
& "$HOME\.codex\skills\codex-x9-backup\scripts\restore-codex-x9-backup.ps1" `
  -RepoPath "<private-backup-clone>" -TargetProfile "$HOME" -DryRun
```

Confirm the snapshot contains sessions, index/database state, global state,
skills, memories, and `.agents`.

## Apply

Fully exit `Codex.exe` and `codex.exe`, preserve any newer local profile state,
then run:

```powershell
& "$HOME\.codex\skills\codex-x9-backup\scripts\restore-codex-x9-backup.ps1" `
  -RepoPath "<private-backup-clone>" -TargetProfile "$HOME" -Apply
```

## Proof

Disk files alone are not `PASS`. Confirm restored index/database/global state,
then verify task and project visibility in the Codex app. Otherwise report
`PARTIAL`.
