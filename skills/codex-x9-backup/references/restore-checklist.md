# Codex X9 Restore Checklist

Use this checklist after a PC format or when validating a backup.

## Restore Dry Run

Run:

```powershell
& "<backup-clone>\scripts\restore-codex-x9-backup.ps1" -TargetProfile "$HOME" -DryRun
```

Check that the dry run sees:

- `snapshot/dot-codex/sessions`
- `snapshot/dot-codex/session_index.jsonl`
- `snapshot/dot-codex/state_5.sqlite`
- `snapshot/dot-codex/.codex-global-state.json`
- `snapshot/dot-codex/skills`
- `snapshot/dot-codex/memories`
- `snapshot/dot-agents`

## Apply Restore

Before applying:

- Fully exit `Codex.exe` and `codex.exe`.
- Keep a copy of the current local profile if there is anything to preserve.
- Confirm the target profile path is the current Windows user profile.

Apply:

```powershell
& "<backup-clone>\scripts\restore-codex-x9-backup.ps1" -TargetProfile "$HOME" -Apply
```

## Proof

Do not call restore `PASS` from disk files alone.

Proof requires:

- restored `session_index.jsonl`
- restored `state_5.sqlite`
- restored `.codex-global-state.json`
- Codex app-layer thread visibility through `list_threads`
- Codex app-layer project/sidebar visibility through `list_projects`

If sessions are present but old chats or project roots are not visible in the
live Codex app, report `PARTIAL`, not `PASS`.
