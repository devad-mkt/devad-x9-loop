# Devad Headless CLI Sidecars

Use when Codex asks an external model for one bounded review.

## Only Route

Use .devad/tooling/opencode-cli/run-opencode-cli-packet.ps1. Direct opencode
run, ACP, PI, OpenRouter routes, and broad model fan-out are forbidden.

The wrapper must call the installed X9 OpenCode doctor. That doctor runs in a
temporary no-repository directory with external plugins disabled, every tool
permission denied, and a small environment allowlist.

## Flow

1. Codex inspects local truth.
2. Write one strict x9-sidecar-packet-v1 JSON file in an approved sidecar folder.
3. Run the doctor once.
4. Ask one configured model once.
5. Verify useful advice locally.
6. Record the result or TOOL_UNAVAILABLE.

## Safety

- No repo mount, source browsing, commands, edits, deploys, or live writes.
- No secrets, .env values, tokens, cookies, customer data, or raw production logs.
- No whole chat history or unrelated files.
- If more context is needed, Codex creates a new small packet.
- A provider failure is nonblocking and is never retried in a loop.