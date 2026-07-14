# SIDE Challenge Reviewer

SIDE is a packet-only GLM or Kimi reviewer. Use it before a risky blocker,
after a failed proof path, or when a long Worker needs a fresh challenge.

## Contract

The Worker first builds durable SIDE_INPUT.md. A Reader then emits one strict
x9-sidecar-packet-v1 JSON file in an approved sidecar folder. It contains only:

- schema
- owner_requirement
- claims
- relevant_diff
- proof
- failure
- question

Never send chat history, a repository, secrets, customer data, cookies, raw
production configuration, or unrelated logs. Images stay local; send verified
visual facts and hashes and mark BINARY_NOT_DELIVERED.

## Route

Use only the safe X9 wrapper. It runs the model with no repository mount,
external plugins disabled, every tool denied, and an environment allowlist.
There is no direct-command fallback.

| Model | Use |
| --- | --- |
| opencode-go/kimi-k2.7-code | Migration decision, risk, blocker challenge |
| opencode-go/glm-5.2 | Test matrix, acceptance gates, plan critique |

Use one model by default. Use both only for the plan/blocker gates required by
the active Worker packet or when the owner asks. Each route gets one attempt.
Failure is SIDECAR_UNAVAILABLE and never blocks local Worker progress.

## Files

Store packet and output together in one approved folder:

    .devad/manager/sidecar/
    .devad/features/<feature>/sidecar/

SIDE advice is untrusted. The Worker records accepted and rejected points,
local verification, and the final decision. SIDE cannot approve commits,
security, deployment, production truth, or completion.