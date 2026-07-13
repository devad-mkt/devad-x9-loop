---
name: codex-token-budget
description: Use when tracking or diagnosing Codex token usage, token burn, context bloat, manager or worker thread cost, weekly or 5-hour usage limits, task budget percentage, long-run /goal loops, orchestration overhead, heartbeat/polling cost, repeated tool-output cost, or when the user asks why Codex work is consuming many tokens.
---

# Codex Token Budget

Use this skill as a token-burn diagnostic, not only as a hard budget tracker. It should work for any Codex task: coding, planning, manager/worker orchestration, browser proof, `/goal`, repair loops, or thread audits.

## Source Of Truth

- Official remaining percentages come from `https://chatgpt.com/codex/cloud/settings/analytics#usage` or interactive `/status`.
- Local estimates come from `<codex-usage-lite>` only when
  it supports the current telemetry schema.
- Current Codex logs may use `codex_core::session::turn` with cumulative
  `total_usage_tokens`. A tracker that reads only old `response.completed`
  rows can incorrectly report zero.
- Local thread totals from Codex state are fallback/lifetime signals and can look huge. Do not treat them as live burn without checking response-event windows.
- Do not claim exact official tokens unless the official UI or API exposes them.

## Fast Commands

Run the local tracker:

```powershell
powershell -ExecutionPolicy Bypass -File <codex-usage-lite>\run.ps1
```

Set a baseline before a task or audit:

```powershell
powershell -ExecutionPolicy Bypass -File <codex-usage-lite>\run.ps1 --set-baseline
```

Track a task cap:

```powershell
powershell -ExecutionPolicy Bypass -File <codex-usage-lite>\run.ps1 --task-weekly-percent 1
```

## Audit Workflow

1. Classify the request:
   - `budget`: stay under a known cap.
   - `burn audit`: explain where tokens are going.
   - `manager audit`: inspect manager/worker thread overhead.
   - `watch`: take a baseline, wait or schedule a later sample, then compare.
2. Run the tracker and record:
   - response-event tokens counted,
   - rolling 5h/7d/month windows,
   - task delta since baseline,
   - top thread lifetime/fallback totals,
   - report path.
3. If threads are involved, inspect only metadata first: title, cwd, status, preview, updated time, and whether the thread is active. Read full thread turns only when needed to explain a specific burn source.
4. For manager/worker orchestration, classify burn by cause:
   - broad old-chat or transcript reads,
   - full skill/reference loading when a narrow reference would do,
   - polling/heartbeat loops,
   - too many active workers,
   - repeated repo truth scans,
   - repeated browser/proof loops,
   - large tool outputs copied into context,
   - workers ending in chat instead of durable handoffs,
   - manager revalidating all lanes instead of only changed handoffs,
   - `/goal` or repair loops with weak stop criteria.
5. Report fixes as recommendations only unless the user explicitly asks to change orchestration, packets, code, automations, or threads.

## Model Benchmark Mode

Use this mode when selecting a model or thinking level for X9.

1. Define one task class. Do not average routine routing with architecture,
   security, deploy judgment, or broad coding.
2. Use fresh context, the same packet, and a hidden proof for every candidate.
3. Record first-pass score before corrections.
4. Count every retry until independent proof passes.
5. Compare total verified-result tokens, active time, retries, pass rate, and
   critical truth/safety errors.
6. Require at least five real samples before permanent promotion.

If the X9 suite benchmark exists, update its MODEL_LEDGER.md and add a dated
result folder. Keep raw logs out of Git; store compact evidence, hashes, and
meaning.

Selection rule: choose the lowest profile that scores at least 90/100, has no
critical safety error, passes independent proof, and minimizes total
verified-result tokens. A cheap first turn that needs repeated repair loses.

## Manager Thread Rules

- Prefer durable handoff pickup over heartbeat polling.
- Keep active implementation workers to two or fewer until token burn is understood.
- Manager reads compact `.devad/manager/HANDOFF_INDEX.md` first, not every worker transcript.
- Manager reads `.devad/ROUTER.md` and current files, not full historical
  STATUS.md/HANDOFFS.md. Flag either file above 120 lines or 12 KB as context
  bloat.
- Worker final messages should be short and point to `HANDOFFS.md`.
- Manager validation should target changed or claimed lanes only.
- Old X7-style inbox/outbox, registry, leases, broad observe loops, and multi-model fan-out are high-risk token multipliers.

## Watch Mode

For a short watch such as 30 minutes:

1. Run the tracker now.
2. Record active/recent manager and worker thread metadata.
3. Use a thread heartbeat or a manual second sample at the requested time.
4. Rerun the tracker.
5. Compare response-event delta first, then thread lifetime/fallback changes.
6. Produce a report only unless fixes were explicitly requested.

Do not create a watch loop with frequent polling unless the user asks for it. One baseline plus one later sample is usually enough for a 30-minute diagnosis.

## Stop And Ask Lines

- If task cap used reaches 70%, switch to low-token mode: narrow reads, no broad logs, no old chats, no full-suite reruns unless needed.
- If task cap used reaches 90%, stop and ask before continuing expensive work.
- If a manager audit requires reading large thread histories or raw rollout logs, explain why and ask before doing broad reads.

## Report Shape

```md
TLDR: <main burn source and safest quality-preserving fix>

| Field | Value |
| --- | --- |
| Mode | budget | burn audit | manager audit | watch |
| Official source | checked | not checked |
| Local tracker | <summary> |
| Baseline delta | <tokens/unknown> |
| Response-event burn | <tokens/window> |
| Thread fallback signal | <top relevant threads, with caveat> |
| Risk | LOW | MEDIUM | HIGH |

## Findings
- <evidence-backed token burn source>

## Quality-Preserving Fixes
- <recommendation only unless user asked to implement>

## What Not To Do
- <changes that save tokens but lower quality too much>
```

## X9 Loop v5 Audit

For Linx/Thinx/Worker cost, read PASS_CAPSULE.json, EVENT_CURSOR.json,
TASK_GRAPH.json, and DISPATCH_LEDGER.jsonl before any chat logs.

Measure:
- model tokens per acknowledged dispatch and accepted completion;
- no-change passes and duplicate receipt checks;
- attempts per dispatch and orchestration-caused retries;
- capsule size, unseen event count, and files read per manager pass;
- first-pass proof rate and critical truth/safety errors.

Flag token burn when a pass rereads historical manager files, processes no new
event, resends an accepted dispatch, or uses model work for deterministic role,
hash, dependency, resource, or delivery checks.
