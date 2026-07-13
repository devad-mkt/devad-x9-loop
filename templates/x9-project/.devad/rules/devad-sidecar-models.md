# Devad Sidecar Models

Use for bounded external model review packets. Codex owns scope, local verification, diff review, tests, browser checks, deploy decisions, docs decisions, and final claims.

## Current Policy

- Use headless CLI only.
- Do not use ACP for OpenCode or PI.
- Do not use PI as an execution dependency.
- Do not use OpenRouter routes or OpenRouter model IDs.
- Use one sidecar by default. Multi-model fan-out needs explicit owner approval.
- Sidecars are reviewers/co-designers, not authorities. Every useful claim must be verified locally before edits or final claims.
- Send selected files, source slices, extracted tables, screenshot notes, or narrow summaries. Do not send whole repos, secrets, raw production logs, customer data, cookies, `.env`, provider dashboards, or whole chat history.
- If a model emits fake commands, broadens scope, asks for secrets, claims success without evidence, or cannot access tools it claimed to use, stop using that route for the task.

## Active Routes

| Route | Use case | Phase |
| --- | --- | --- |
| `opencode run --model opencode-go/kimi-k2.7-code` | Coding-oriented migration plans, risk review, stop conditions, small/medium implementation options | Plan/options only unless user approves write scope |
| `opencode run --model opencode-go/glm-5.2` | Implementation checklist, test matrix, acceptance gates, plan critique | Plan/options/checklist |
| `opencode run --model opencode/deepseek-v4-flash-free` | Free-model check only when owner explicitly asks | Summary/checklist |
| `opencode run --model opencode/mimo-v2.5-free` | Free-model check only when owner explicitly asks | Summary/checklist |

Use the wrapper at `.devad/tooling/opencode-cli/run-opencode-cli-packet.ps1` when possible. It rejects OpenRouter models and keeps output captured.

## Packet Rules

- Packet must be a markdown file, not a tiny inline prompt.
- Include repo path, branch, HEAD, dirty state, objective, allowed files/slices, denied paths, local facts, and what Codex already tried.
- Include stop conditions and output format.
- Default phase is `PLAN/OPTIONS ONLY. Do not code. Do not edit files. Do not run commands.`
- Any build/execute sidecar phase requires a separate accepted plan and explicit approved write scope.
- If a sidecar needs more context, Codex chooses the next tiny packet; do not let the sidecar roam.

## Retired Routes

| Route | Status | Reason |
| --- | --- | --- |
| OpenCode ACP | Retired | User chose direct headless CLI only. |
| OpenRouter model IDs | Retired | Repeated provider/credit/model routing failures. |
| PI / PI workflow engine | Retired as dependency | Useful concepts only: advisory agents inspect, verify, report, and synthesize evidence. |
| Cursor ACP | Retired for this lane | Adapter readiness was not model-response proof. |

## Proof

Record every sidecar use in the feature handoff:

| Tool/model | Route | Useful? | Misses/risks | Use again? |
| --- | --- | --- | --- | --- |

If a provider, model, quota, or config error occurs, record the route unavailable for the task and do not retry in a loop.
