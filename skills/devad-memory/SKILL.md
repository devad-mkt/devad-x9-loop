---
name: devad-memory
description: "Use for Devad X9 durable memory work: searching or updating `.devad/memory`, extracting Codex session history into SESSION.md/topics/reports/md/extracted folders, maintaining CHAT-CATALOG.md and PROJECT-NAMES.md, creating read/no-read TLDR routing, preserving Devad requirements/decisions/proof without raw chats or secrets, and avoiding broad token-burning searches over old sessions."
---

# Devad Memory

## Authority

Default memory root:

```text
<repo>\.devad\memory
```

Resolve <repo> from the current Git worktree. If the user gives a different memory root, use the user-provided root.

Before any memory search or update, read only these startup files:

```text
<memory>\CHAT-CATALOG.md
<memory>\projects\PROJECT-NAMES.md
```

When creating or updating session memory, also read:

```text
<memory>\skill\X9-SESSION-EXTRACTION-SKILL.md
```

Do not read the full `.devad`, `.devad/memory`, raw session archive, or feature folders by default.

Memory is not active routing truth. Do not write manager CURRENT.md,
CENTRAL_FACTS.md, STATUS.md, HANDOFFS.md, or Worker run files. Linx and Workers
own those files. Memory may distill replaced history only after the active
owner has preserved the current route.

## Routing

- For a quick answer, use `CHAT-CATALOG.md` first and read only the listed session/topic files that match the task.
- For extraction/backfill, follow `X9-SESSION-EXTRACTION-SKILL.md` exactly.
- For implementation context, read only the relevant `SESSION.md`, `topics/*.md`, and copied `md/*.md` files selected by the catalog.
- For method changes, edit the memory method files directly and keep the skill compact.
- When a project has `.devad/ROUTER.md`, use it to locate the exact memory
  catalog; do not follow unrelated manager or feature routes.

## Search Rules

Start with unique anchors from the user request:

- exact chat UUIDs
- exact document titles
- exact unusual phrases, for example `gemini ast`, `POST Migration`, `laravel migration`
- exact feature folder names
- exact route names, provider names, or product names only when paired with the project/task

Do not start with broad terms such as `migration`, `post`, `laravel`, `plan`, `handoff`, `TASK.md`, or model names alone. Use broad terms only inside already-confirmed candidate sessions or repo folders.

For raw Codex sessions, inspect metadata and first user messages before reading full JSONL. Do not open large rollouts unless an exact anchor or catalog row makes them a strong candidate.

## Session Structure

Use canonical project folders:

```text
<memory>\projects\<exact Codex project name>\sessions\<session-folder>\
  SESSION.md
  ARTIFACTS.md
  topics\
  reports\
  md\
  extracted\
```

Never create `artifacts/` folders.

Use exact project names from:

```text
<memory>\projects\PROJECT-NAMES.md
```

## Content Rules

Each `SESSION.md` needs source paths searched, aliases, chat IDs, tags, status, read/no-read TLDR, read-this-for, do-not-read-this-for, topic links, copied markdown, search ledger, and sensitive material notes.

Each topic file must be useful enough for a new chat to resume without reading the old chat. Include objective, user requirements, options, what failed, correction, final/current decision, why, risks, relevant paths, related sessions, copied markdown, next safe steps, verification, and do-not-repeat lessons.

Each `CHAT-CATALOG.md` row must include a meaningful `Read for:` and `Skip for:` sentence.

Do not store raw chats, full JSONL exports, secrets, `.env`, OAuth codes, cookies, provider logs, payment data, private emails, or credentials.

## Completion

After memory edits:

1. Update `CHAT-CATALOG.md`.
2. Update compact lookup files such as `INDEX.md` only when needed.
3. Update the affected project `PROJECT-CATALOG.md`.
4. Run or adapt the verification script from `X9-SESSION-EXTRACTION-SKILL.md`.
5. Report only the extracted TLDR, session folders, topics, copied markdown, known gaps, and verification result.

## X9 Loop Lite v6 Boundary

`.devad/manager/loop-lite/SNAPSHOT.json` is active routing recovery truth and
outranks memory. Files under `.devad/manager/loop/` are historical evidence in
v6; memory may index them but cannot restore their old routing authority.

Memory may explain history but cannot assign a role, acknowledge a dispatch,
complete a task, release a resource, or open a deploy gate.
