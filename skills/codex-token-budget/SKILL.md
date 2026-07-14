---
name: codex-token-budget
description: Use when tracking or diagnosing Codex token usage, token burn, context bloat, manager or worker task cost, weekly or 5-hour usage limits, task budget percentage, long-run goals, orchestration overhead, heartbeat/polling cost, retries, repeated tool-output cost, or when the user asks which model solves work most cheaply after proof.
---

# Codex Token Budget

Use this skill for any Codex task: coding, planning, orchestration, browser
proof, repair loops, model benchmarks, or task audits. Optimize total cost to a
verified result, not the cheapest first turn.

## Source Of Truth

- Official remaining percentages come from the Codex usage UI or interactive
  `/status` when available.
- Local trackers are estimates and must support the current event schema.
- Current logs may expose cumulative `total_usage_tokens`; calculate a bounded
  response/task delta, not the whole task lifetime.
- Exact token data that is not exposed is `Unknown`.
- Fallback lifetime totals are forbidden for X9 v6 decisions. They can be
  misleading after compaction, retries, imports, and long-running tasks.
- Never claim exact official tokens from a local estimate.

## Audit Workflow

1. Choose one mode: `budget`, `burn audit`, `manager audit`, `watch`, or
   `model benchmark`.
2. Set one baseline before the measured task when real telemetry exists.
3. Record only the measured window:
   - official percentage delta, if visible;
   - response/task token delta, if exposed;
   - wall time and active model time;
   - prompt bytes, files read, and state writes;
   - transport and callback retries;
   - context compactions;
   - first-pass success and final proof result.
4. Read task metadata first. Read full turns only to explain one specific burn
   source that metadata cannot prove.
5. Keep missing fields `Unknown`; never backfill them from lifetime totals.

## Burn Classes

- broad old-chat, transcript, or manager-history reads;
- full skill/reference loading instead of one linked rule;
- heartbeat, sleep, or no-change polling loops;
- model work used for hashes, roles, claims, dependencies, or delivery state;
- too many active Workers or conflicting worktrees;
- repeated Git/runtime scans with no changed event;
- large tool output copied into model context;
- repeated browser/full-suite proof without a changed surface;
- cheap model retries that cost more than one stronger first pass;
- Worker ending in long chat instead of a compact durable result.

## Model Benchmark

Compare candidates only on the same task class and packet.

1. Use fresh context, the same immutable input, hidden expected facts, and the
   same stop rule.
2. Record first-pass score before correction.
3. Count every retry until independent proof passes.
4. Compare total verified-result tokens, wall time, retries, first-pass rate,
   and critical truth/safety errors.
5. Require at least five real samples before permanent model promotion.

Choose the lowest profile that scores at least 90/100, has no critical safety
error, passes independent proof, and minimizes total verified-result cost. A
cheap model that needs repeated repair loses.

## X9 Loop Lite v6 Audit

Read only:

- `.devad/manager/loop-lite/SNAPSHOT.json`;
- the latest generated `runtime/ACTION.json`, when present;
- the exact task/result and controller metric output;
- current Codex transport metadata for that event.

Do not read old `manager/loop/` files or chats unless investigating one named
historical incident.

Measure per event:

| Metric | Expected |
| --- | --- |
| Deterministic reconcile wall time | under 5 seconds |
| Routine Linx callback | median under 60 seconds; p95 under 2 minutes |
| Linx model turns | at most 1 |
| State transactions | at most 1 |
| Manual state writes | 0 |
| Prompt bytes | measured |
| Files read / state writes | measured |
| Delivery/callback retries | measured |
| Context compactions | 0 |
| First-pass success | measured |
| Real token telemetry | exact value or `Unknown` |

Flag burn when Linx reads outside `ACTION.json`, reviews code, manually edits
state, processes no new event, resends an accepted packet, or performs work the
controller can do deterministically.

## Watch Mode

For a time-bounded watch:

1. Capture one baseline.
2. Record active task IDs, models, and current event/dispatch IDs.
3. Use a manual or supported one-shot later sample.
4. Compare only the measured window.
5. Produce a report unless the user explicitly asks for fixes.

Do not create frequent polling or recurring model wakeups for measurement.

## Quality Guard

- Do not lower reasoning for security, money, architecture, destructive risk,
  or conflicting proof merely to save tokens.
- Prefer deterministic controller work, smaller packets, exact file claims,
  and one independent proof over weaker reasoning.
- A higher-cost first pass is cheaper when it avoids several failed repairs.
- If a task cap reaches 70%, narrow reads and proof scope without weakening the
  finish line.
- At 90%, stop before optional expensive work and report the exact remaining
  required proof.

## Report

```md
TLDR: <main burn source and safest quality-preserving fix>

| Field | Value |
| --- | --- |
| Mode | budget / burn / manager / watch / benchmark |
| Official source | checked / not exposed |
| Measured window | <start/end or task/event> |
| Token delta | <exact or Unknown> |
| Wall time | <duration> |
| Prompt bytes | <count> |
| Reads / writes | <count> |
| Retries / compactions | <count> |
| First-pass proof | PASS / FAIL / Unknown |
| Risk | LOW / MEDIUM / HIGH |

## Findings
- <evidence-backed cause>

## Quality-Preserving Fixes
- <recommendation or implemented change>

## Do Not Do
- <cheap change that would lower correctness>
```
