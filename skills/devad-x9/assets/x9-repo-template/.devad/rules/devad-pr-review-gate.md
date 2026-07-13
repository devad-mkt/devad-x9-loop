# Devad PR Review Gate

Use for PR review, merge readiness, architecture/security/business correctness, and AI reviewer setup.

## Review Focus

Ignore style/linter issues unless they hide a real bug. Focus on:

- Business logic correctness.
- Authorization and workspace/tenant scope.
- Auth, billing, payments, subscriptions, and entitlements.
- Data deletion, destructive actions, migrations, rollback.
- SQL injection and unsafe query patterns.
- N+1 queries and major performance regressions.
- Provider callbacks, webhooks, API key scope, secrets, logs, and PII.
- UI/settings changes that bypass admin or tenant controls.

## Merge Policy

- Critical findings block merge.
- Warnings are informational until owner review.
- AI review is a second-pass safety layer, not final proof.
- CodeRabbit or another AI reviewer can be used when installed/authenticated, but Codex must still inspect source and run focused verification.
- Do not require hard GitHub status gating for every tiny PR until the review flow proves reliable on real PRs.
