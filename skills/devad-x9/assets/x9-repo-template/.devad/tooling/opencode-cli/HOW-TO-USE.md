# Devad OpenCode CLI Sidecar

Use this for direct headless OpenCode sidecar packets.

Do not use ACP. Do not use OpenRouter model IDs. Do not use PI as an execution dependency.

## Models

| Model | Use |
| --- | --- |
| `opencode-go/kimi-k2.7-code` | Coding-oriented migration plans, risk review, stop conditions |
| `opencode-go/glm-5.2` | Test matrix, acceptance gates, plan critique |
| `opencode/deepseek-v4-flash-free` | Free-model check only when owner asks |
| `opencode/mimo-v2.5-free` | Free-model check only when owner asks |

## Run

```powershell
.\.devad\tooling\opencode-cli\run-opencode-cli-packet.ps1 `
  -RepoRoot <source-root> `
  -Packet .devad\features\<feature>\prompts\<packet>.md `
  -Model opencode-go/glm-5.2 `
  -Output .devad\features\<feature>\sidecar\<packet>-glm.md
```

## Packet Rules

- Markdown packet only.
- Plan/review by default.
- Exact allowed files and denied paths.
- No secrets, `.env`, tokens, cookies, raw production logs, or customer data.
- No commands, edits, deploys, live DB writes, or provider dashboard actions unless Codex/user explicitly approve a separate build packet.

## Failure Rule

If OpenCode reports model-not-found, provider, quota, credit, max-token, or auth errors, record the route unavailable and stop. Do not retry in a loop.
