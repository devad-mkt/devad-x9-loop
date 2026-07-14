# Devad Sidecar Models

Sidecars are bounded reviewers. Codex owns scope, edits, tests, security,
browser proof, deployment, documentation, and final claims.

## Active Routes

| Model | Use | Authority |
| --- | --- | --- |
| opencode-go/kimi-k2.7-code | Migration plan, risk review, stop conditions | Advice only |
| opencode-go/glm-5.2 | Checklist, test matrix, plan critique | Advice only |

Use one model by default. A second model is allowed only after the first leaves
a concrete unresolved risk or the owner asks for both. Kimi 2.6 and OpenRouter
routes are unavailable.

## Packet Contract

Use strict x9-sidecar-packet-v1 JSON with exactly:

- owner_requirement
- claims
- relevant_diff
- proof
- failure
- question

Keep it below 32 KB. No whole repo, whole chat, secrets, raw production logs,
customer data, cookies, or provider configuration.

## Execution

Use only .devad/tooling/opencode-cli/run-opencode-cli-packet.ps1. Direct
OpenCode commands and ACP are forbidden. The safe wrapper disables tools,
external plugins, repo access, and unneeded environment values.

Verify useful advice locally. Record model, result, misses, and whether it
should be used again. TOOL_UNAVAILABLE is nonblocking and gets no retry loop.