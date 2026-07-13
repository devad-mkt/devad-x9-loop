# Tool Lessons Policy

Use this when Chrome profile, authenticated browser proof, OpenCode SIDE,
GLM/Kimi, thread tools, MCP, connectors, Dokploy, Playwright, or any repeated
tool route fails, stalls, or succeeds only through a non-obvious fallback.

## Purpose

`TOOL_LESSONS.md` is a small playbook of current tool routes. It prevents the
manager from burning tokens by rediscovering the same Chrome, OpenCode, thread
tool, or MCP behavior.

## Location

```text
.devad/manager/TOOL_LESSONS.md
```

## Required Read Rule

Before repeating a failed or fragile tool route:

1. Read `TOOL_LESSONS.md`.
2. Check whether the route is `GOOD`, `BAD`, `FALLBACK`, or `UNKNOWN`.
3. Try only the next listed safe route.
4. After success or failure, update the row.
5. Do not do a third same-route attempt without a new hypothesis.

## Template

```md
# Tool Lessons

**Updated:** YYYY-MM-DD HH:mm Europe/Istanbul

| Tool/route | Status | Use when | Do first | Do not repeat | Evidence | Updated |
| --- | --- | --- | --- | --- | --- | --- |
| Chrome authenticated proof | FALLBACK | devad.io auth proof | Prefer exposed Chrome/Codex browser tool or owner-approved existing profile/CDP/Windows UI route. | Do not treat fresh Playwright Chrome redirected to login as auth proof. | <path> | YYYY-MM-DD |
| OpenCode SIDE | FALLBACK | GLM/Kimi packet review | Use saved packet only; prefer `$devad-assistant`; if wrapper fails, try direct OpenCode route once. | Do not loop wrapper failures. | <path> | YYYY-MM-DD |
```

## Chrome Auth Proof Rule

- Do not assume a fresh Playwright browser is authenticated.
- Prefer an exposed Codex Chrome/browser tool when present.
- If the owner approved Chrome profile, CDP, or Windows UI automation, use only
  that scoped route and record screenshots/DOM/status.
- If Chrome extension, CDP ports, or browser tools are unavailable, record
  `TOOL_FAILED:<route>` and try the next documented route once.
- Never print cookies, auth headers, raw local storage, OAuth codes, or profile
  database values.

## OpenCode SIDE Rule

- SIDE gets a saved sanitized packet only, never full chat.
- Prefer `$devad-assistant` routes if available.
- Known SIDE uses:
  - `opencode-go/kimi-k2.7-code`: strict migration decision, blocker challenge.
  - `opencode-go/glm-5.2`: test matrix, acceptance checklist, architecture critique.
- If the wrapper route fails, record `TOOL_FAILED:opencode-wrapper` and try one
  direct OpenCode route only when available.
- Save packet, model output, and manager decision under `.devad/manager/sidecar/`.
- SIDE advice is evidence, not truth.

## Stop Labels

```text
MISSING_TOOL_LESSONS
MISSING_TOOL_LESSON:<tool>
REPEATED_TOOL_FAILURE:<tool>
TOOL_ROUTE_EXHAUSTED:<tool>
```

Use `TOOL_FAILED` for the route, not `HARD_BLOCKER`, while another safe route
exists.
