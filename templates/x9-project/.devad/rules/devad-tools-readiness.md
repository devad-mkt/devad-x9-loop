# Devad Tools Readiness

Use for Graphify, CodeFlow, ast-grep, Laravel MCP/Boost, browser, Chrome,
Playwright, dependencies, and headless sidecars.

## Tool Truth

- rg plus exact source lines is first-shot source truth.
- Structural search helps when text search can lie.
- Architecture maps locate ownership; they do not prove exact behavior.
- External models provide critique only. Codex verifies every useful claim.
- Visible UI claims need browser proof when a browser path exists.

## Dependency Checks

- In a fresh or recovery worktree, verify vendor and node_modules are local
  real folders, not links into another worktree.
- Verify required framework boot before using framework tooling as evidence.
- Use the cheapest browser path that proves the claim.
- Use an authenticated Chrome profile only when saved login or extension state
  is required. Never inspect or print cookie values.

## Sidecar Readiness

Only the installed X9 OpenCode doctor may call GLM 5.2 or Kimi 2.7 Code:

    python "$HOME\.codex\skills\devad-x9-loop\scripts\opencode_doctor.py" doctor

The doctor uses the real executable, disables external plugins and all model
tools, strips unneeded environment values, and never mounts the repository.
Do not run OpenCode directly, use ACP, or use OpenRouter routes.

TOOL_UNAVAILABLE is nonblocking. Record it once and continue with local proof.