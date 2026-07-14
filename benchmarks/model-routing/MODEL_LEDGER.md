# Model Ledger

| Date | Task class | Candidate | Samples | Pass rate | Median tokens to proof | Critical errors | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 2026-07-11 | Linx routine | Luna medium | 1 | 100% | 25,577 | 0 | PILOT |
| 2026-07-11 | Linx routine | Sol medium | 1 | 100% | 25,788 | 0 | PILOT |
| 2026-07-11 | Linx routine | Sol xhigh | 1 | 100% | 25,839 | 0 | PILOT |
| 2026-07-11 | Thinx strategy | Sol xhigh | 1 | 100% | 25,828 | 0 | PILOT |
| 2026-07-11 | Thinx strategy | Sol ultra | 1 | 100% | 25,781 | 0 | PILOT |
| 2026-07-11 | Worker bounded debug | Terra xhigh | 1 | 100% final | 43,515 | 0 | PILOT |
| 2026-07-11 | Worker bounded debug | Sol high | 1 | 100% final | 32,516 | 0 | PILOT |
| 2026-07-11 | Linx return routing | Sol medium | 1 | 100% first | 25,812 | 0 | PILOT_NOT_PROMOTED |
| 2026-07-11 | Linx return routing | Luna high | 1 | 0% first; 100% final | 26,373 | 1 | NOT_SELECTED |

Permanent promotion: none. Each task class needs at least five samples.

2026-07-13 decision: revoke the lower Linx baseline. The long-running LINX task
produced an incorrect first answer, crossed into Worker artifact generation,
and had overlapping active turns. The task tool exposed gpt-5.5 but did not
prove the requested Sol profile or thinking effort, so this is a system-quality
regression, not a valid model-vs-model score. Conservative baseline:
`gpt-5.5 xhigh` for Linx, Thinx, and Workers.

2026-07-13 owner override: Linx `gpt-5.6 high`; Worker `gpt-5.6 high` with
xhigh when the owner explicitly asks extra high; Thinx `gpt-5.6 xhigh` for
normal planning/review and ultra for very-hard issues. This is an owner policy
choice, not a benchmark promotion claim.
