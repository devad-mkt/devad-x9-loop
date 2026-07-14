# Codex X9 Backup Policy

## Include

Back up the restore-critical and customization state:

- `<profile>\.codex\sessions`
- `<profile>\.codex\archived_sessions`
- `<profile>\.codex\session_index.jsonl`
- `<profile>\.codex\state_5.sqlite`
- `<profile>\.codex\.codex-global-state.json`
- `<profile>\.codex\config.toml`
- `<profile>\.codex\skills`
- `<profile>\.codex\skills-disabled`
- `<profile>\.codex\memories`
- `<profile>\.codex\rules`
- `<profile>\.codex\automations`
- `<profile>\.codex\state`
- `<profile>\.codex\tooling`
- `<profile>\.codex\attachments`
- `<profile>\.codex\generated_images`
- `<profile>\.codex\recovered_project_chats`
- `<profile>\.agents`
- `<profile>\.config\opencode`

Repo layout:

- `snapshot/dot-codex/...`
- `snapshot/dot-agents/...`
- `snapshot/dot-config-opencode/...`
- `manifests/latest.json`
- `manifests/runs/<timestamp>.json`

## Exclude

Do not back up raw secrets, process state, install/runtime weight, or caches:

- `auth.json`
- `cap_sid`
- `.sandbox-secrets`
- `.env`, `.env.*`
- cookie files
- `*.sqlite-wal`, `*.sqlite-shm`
- `logs_*.sqlite`
- `*.log`
- `.codex\plugins\.plugin-appserver`
- `.codex\plugins\cache`
- `.codex\packages`
- `.cache\codex-runtimes`
- `AppData\Local\OpenAI`
- `.sandbox`, `.sandbox-bin`
- `.tmp`, `tmp`, `cache`, `.cache`
- `node_modules`

## Git LFS

Use Git LFS for large restore data:

- `*.jsonl`
- `*.sqlite`
- `*.sqlite.bak*`
- `*.db`

Run `git lfs install --local` before staging backup files. A backup is not
`PASS` if large session JSONL or SQLite files are committed as normal Git
blobs.

## Secret Scan Gate

Run `scripts/redact-secrets.py` on the snapshot before the final scan. The
redactor must:

- update only `snapshot/`, never the live profile
- replace high-confidence secrets with `[REDACTED:<rule>:<hash>]`
- use SQLite updates plus `VACUUM` for `.sqlite` and `.db` files
- write only path, rule, line/row, and counts
- never print raw matched text

Run `scripts/secret-scan.py` before commit/push. The scanner must:

- scan `snapshot/`
- fail closed on high-confidence secret patterns
- write only path, line, rule, and a hash of the matched value
- never print raw matched text

If the scanner still blocks after redaction, leave local files unpushed and
report `BLOCKED`.
