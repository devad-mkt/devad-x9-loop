# Model Ledger

Record local measurements here. Do not promote a model from one sample.

| Date | Task class | Candidate | Samples | First-pass proof rate | Median tokens to proof | Critical errors | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |

Promotion requires at least five comparable samples for the same task class,
no critical truth/safety errors, and lower total tokens-to-proof than the
current model. Include retries and orchestration overhead, not only one turn.

Default policy remains:

- Linx: `gpt-5.6 high`.
- Thinx: `gpt-5.6 xhigh`; one `ultra` pass only for very hard gated work, then
  return to xhigh.
- Worker: `gpt-5.6 high`; xhigh only when the owner explicitly asks.
