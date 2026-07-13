# Devad Headless CLI Sidecars

Use when Codex delegates a bounded review packet to a headless CLI model.

## Rule

Direct CLI is the only supported sidecar transport for this workflow.

Do not use:

- `opencode acp`
- `cursor-agent-acp`
- PI ACP or PI workflow execution
- OpenRouter model IDs
- broad multi-model benchmarks

## OpenCode Go Commands

Preferred wrapper:

```powershell
.\.devad\tooling\opencode-cli\run-opencode-cli-packet.ps1 `
  -RepoRoot <source-root> `
  -Packet .devad\features\<feature>\prompts\<packet>.md `
  -Model opencode-go/kimi-k2.7-code `
  -Output .devad\features\<feature>\sidecar\<packet>-kimi.md
```

Direct command:

```powershell
opencode run `
  --model opencode-go/glm-5.2 `
  --dir <source-root> `
  --file .devad\features\<feature>\prompts\<packet>.md `
  --title "Devad sidecar review" `
  "Read the attached packet. Return concise markdown only. PLAN/REVIEW ONLY. Do not run commands. Do not edit files."
```

## Readiness

```powershell
opencode --version
opencode models | Select-String -Pattern "opencode-go/glm-5.2|opencode-go/kimi-k2.7-code"
```

Do not override `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, or `XDG_STATE_HOME` for real model runs unless the OpenCode provider config/auth is copied into that isolated home. Isolated empty homes can make listed models fail at runtime.

## Phase Shape

1. Local Codex inspection first.
2. One markdown packet.
3. One sidecar model.
4. Plan/options/checklist output only.
5. Codex verifies useful claims locally.
6. Record model use in the handoff.

## Safety

- No secrets, `.env`, provider tokens, raw production logs, cookies, or customer data.
- No production deploys, live DB writes, provider dashboard actions, tenant resets, or final claims delegated to a sidecar.
- If the model asks for more files, Codex decides the next narrow packet.
- If the model fails, times out, routes through OpenRouter, or asks to use ACP/PI, stop that route for the task.
