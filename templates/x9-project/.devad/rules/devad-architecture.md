# Devad Architecture

Use for CORE/XCO control plane, SITE/POST/AI/CHAT integration, bridge design, workspace scope, API keys, audit, webhooks, and legacy migration.

## Rules

- CORE/XCO remains the Devad control plane. Do not rebase, rewrite, or transplant XCO onto another starter kit.
- Legacy apps can stay live during migration. Use bounded APIs/bridges first; do not share raw DB state or copy legacy modules into CORE.
- Bridge surfaces should be explicit and scoped, such as `PostBridge`, `AiBridge`, `StudioApi`, and `ChatBridge`.
- MCP/agent tools may call safe bridge APIs only. They must not call raw dashboard controllers, arbitrary Eloquent access, or unsafe legacy internals.
- Bridge, credit, audit, API-key, webhook, and agent operations must be scoped to workspace/user/role unless protected superadmin authority is proven.
- Automation/API keys need explicit product scopes such as `site`, `post`, `ai`, `chat`, `read`, `write`, and `admin` where applicable.
- Important bridge calls should emit audit/activity records with workspace, user/key, product, action, result, and correlation id when available.
- Webhook/event payloads need stable envelopes before public, n8n, or agent exposure.
- Defer multi-db tenancy and plugin/theme architecture until workspace scoping and bounded APIs are stable.
- Reference starters are pattern libraries only. Do not blindly copy Blade, Livewire, plugin internals, billing, auth, or tenant code.

## Bias

Prefer changes that reduce Codex mistakes and verification cost. Reject broad cleanup and large diffs unless they protect live revenue, auth, or workspace flows.
