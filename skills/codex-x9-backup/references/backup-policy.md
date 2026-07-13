# Codex X9 Backup Policy

## Include

Back up restore-critical customization state under `<profile-root>`:

- `.codex/sessions`, `.codex/archived_sessions`, and `session_index.jsonl`
- `.codex/state_5.sqlite`, `.codex/.codex-global-state.json`, and `config.toml`
- `.codex/skills`, `.codex/skills-disabled`, `.codex/memories`, and `.codex/rules`
- `.codex/automations`, `.codex/state`, `.codex/tooling`, and `.codex/attachments`
- `.codex/generated_images` and `.codex/recovered_project_chats`
- `.agents` and `.config/opencode`

Store them below `snapshot/` with timestamped manifests.

## Exclude

Never back up raw secrets, process state, install weight, or caches:

- `auth.json`, `cap_sid`, `.sandbox-secrets`, `.env`, `.env.*`, and cookies
- `*.sqlite-wal`, `*.sqlite-shm`, `logs_*.sqlite`, and `*.log`
- plugin appserver/cache, packages, runtime caches, sandboxes, temp folders,
  `node_modules`, and application-local runtime data

## Git LFS

Use Git LFS for `*.jsonl`, `*.sqlite`, `*.sqlite.bak*`, and `*.db`. A backup is
not `PASS` when large restore data is stored as normal Git blobs.

## Secret Gate

Run `scripts/redact-secrets.py` only on `snapshot/`, then run
`scripts/secret-scan.py`. Reports may contain path, rule, location, count, and a
hash, but never the matched value. If the scan still blocks, do not commit or
push.
