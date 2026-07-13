# Devad Tools Readiness

Use for Graphify, CodeFlow, ast-grep, Laravel MCP/Boost, browser, Chrome, Playwright, dependency truth, and headless sidecar readiness.

## Tool Truth

- `rg` plus exact source lines is first-shot truth for labels, routes, setting keys, owners, and UI inventory.
- `ast-grep`/`sg` is for structural code search when text search can lie.
- Graphify is an architecture map, not proof of exact labels, routes, settings, or permissions.
- CodeFlow is a locator for owning functions/files, not final inventory proof.
- Laravel MCP/Boost is useful for Laravel routes, schema, docs, logs, and backend facts after dependency isolation and app boot.
- External models are critique only unless Codex verifies locally.
- Browser proof is required for visible UI claims when a browser path is available.

## Dependency Checks

- Before Laravel MCP/Boost, `php artisan`, tests, builds, CodeFlow, or frontend checks in a fresh/recovery worktree, verify `vendor` and `node_modules` are local real folders, not junctions/symlinks/reparse points into another worktree.
- Verify `vendor/autoload.php` and `php artisan` boot when Laravel facts are needed.
- Before telling the user to manually test visible UI, check available browser paths and use the cheapest one that can prove the claim.
- Use Codex/browser in-app tools for unauthenticated/local/deployed rendering and console errors.
- Use Chrome/profile control only when logged-in cookies, installed extensions, saved permissions, or exact Chrome profile state matters.
- Known local Chrome profile preference: `codex`.

## Headless Sidecar Readiness

- Sidecars are direct headless CLI only.
- Do not use ACP for OpenCode or PI.
- Do not use OpenRouter routes or OpenRouter model IDs.
- Do not use PI workflow execution unless the owner explicitly reopens it in a later task.
- Use OpenCode Go models via direct CLI:
  - `opencode-go/glm-5.2`
  - `opencode-go/kimi-k2.7-code`
- Wrapper: `.devad/tooling/opencode-cli/run-opencode-cli-packet.ps1`.

Readiness commands:

```powershell
opencode --version
opencode models | Select-String -Pattern "opencode-go/glm-5.2|opencode-go/kimi-k2.7-code"
```

Do not set isolated XDG homes for real sidecar runs unless the OpenCode provider config/auth is present there. Empty isolated XDG homes can make `opencode run` reject models that are listed in the default config.

## Historical Notes

- Cursor direct and Cursor ACP were previously inconsistent; do not use Cursor/ACP routes for current X7 work.
- OpenCode ACP and OpenRouter routes are retired for current Devad routing because they caused repeated transport/provider failures.
- PI remains a concept source only: advisory agents inspect, verify, report, synthesize evidence, and keep usage/status accounting separate from host context.
