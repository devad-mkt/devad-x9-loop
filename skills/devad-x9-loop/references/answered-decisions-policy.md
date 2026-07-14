# Answered Decisions Policy

Use this when the owner says a question was already answered, when a Worker asks
a repeated question, before asking the owner anything, or when Top Manager
reports `MISSING_MD:<lane>:<fact>`.

## Purpose

`ANSWERED_DECISIONS.md` stores reusable owner answers in a small current table.
`DECISIONS.md` can remain historical and broad. This file is for answers that
must stop Workers and managers from asking again.

## Location

```text
.devad/manager/ANSWERED_DECISIONS.md
```

## Required Read Rule

Before asking the owner:

1. Read `CENTRAL_FACTS.md`.
2. Read `MISSION_LOCK.md`.
3. Read `ANSWERED_DECISIONS.md`.
4. Read `DECISIONS.md`.
5. Read the active Worker `STATUS.md` and top `CURRENT_STATUS`.
6. If the answer exists, use it.
7. If the answer exists only in chat, write it into `.devad` first.
8. Ask the owner only when the durable files show the answer is missing, stale,
   unsafe, or still an `OWNER_DECISION`.

## Template

```md
# Answered Decisions

**Updated:** YYYY-MM-DD HH:mm Europe/Istanbul

| Key | Answer | Scope | Status | Source | Updated |
| --- | --- | --- | --- | --- | --- |
| deploy-branch | Use `feature/post-v105-native-migration-2026-06-18` for live v105 deploy proof. | ai-blog | ACTIVE | owner/manager pass | YYYY-MM-DD |
```

## Status Values

| Status | Meaning |
| --- | --- |
| `ACTIVE` | Use this answer now. |
| `SUPERSEDED` | Historical only; do not use for routing. |
| `NEEDS_REFRESH` | Check current repo/runtime before use. |
| `OWNER_DECISION` | Still needs owner choice. |

## Write Rule

Sub Manager must update this file when:

- the owner answers a question that Workers may ask again,
- Top Manager reports `MISSING_MD`,
- a branch, deploy, access, model, secret-source, proof, or risk choice is made,
- a Worker asks a question that is already answered in chat or old handoffs.

## Stop Labels

```text
MISSING_ANSWERED_DECISIONS
MISSING_ANSWERED_DECISION:<field>
STALE_ANSWERED_DECISION:<field>
REPEATED_OWNER_QUESTION:<field>
```

If a Worker asks a repeated question, Sub Manager should send a correction with
the exact `ANSWERED_DECISIONS.md` row instead of asking the owner again.
