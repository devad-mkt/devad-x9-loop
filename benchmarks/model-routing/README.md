# X9 Model Routing Benchmark

Purpose: select models by verified-result cost for a task class, not by price,
speed, or one-turn tokens alone.

## Read Route

| Need | Read |
| --- | --- |
| Latest Linx quality regression | results/2026-07-13-linx-quality-regression/REPORT.md |
| Latest Linx selection/return test | results/2026-07-11-linx-routing-return/REPORT.md |
| Current pilot | results/2026-07-11/REPORT.md |
| Machine results | results/2026-07-11/RESULTS.json |
| Current routing proposal | results/2026-07-11/MODEL_ROUTING_POLICY.md |
| Add a new test | templates/EXPERIMENT.md and templates/TASK_CASE.json |
| Compare all tests | MODEL_LEDGER.md |

## Required Method

1. Define one task class and hidden proof before running candidates.
2. Use fresh context and the same packet for every candidate.
3. Freeze and score first-pass output.
4. Count every correction turn until proof passes.
5. Record model, effort, time, tokens, retries, score, safety errors, and proof.
6. Choose the lowest verified-result cost that clears the quality floor.
7. Require at least five real tasks in one class before permanent promotion.

Do not mix routine routing, strategy conflict, bounded debugging, broad
implementation, security, or deploy judgment in one average.

## Promotion Gate

A profile becomes default for a task class only when:

- sample count is at least five;
- pass rate is at least 90%;
- no critical truth or safety failure exists;
- median verified-result tokens beat the current default;
- independent proof is available.

If the tool cannot prove which model/effort ran, record a system-quality
regression and do not score it as evidence for or against a candidate model.
