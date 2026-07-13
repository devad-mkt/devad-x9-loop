# X9 Read Policy

Use for broad/noisy tasks, old `.devad` temptation, token pressure, overbuild
risk, or choosing between Devad/XCO/Laravel/domain rule packs.

## Read Once

- Read `.devad/X9.md` once at task start and keep a tiny note of the routed
  packs.
- Read `.devad/ACTIVE.md` and the current handoff once only when branch, resume,
  deploy, merge-risk, or explicit handoff work requires them.
- Read one domain rule pack, then current source/runtime evidence. Add a second
  domain pack only when touched files cross domains.
- Do not reread rules or handoffs after every tool call. Refresh only after a
  branch switch, merge/rebase, deploy, verification result, or user scope
  change.
- Prefer `rg`, focused file reads, and exact source lines before folder-wide
  reads.

## Gated Surfaces

- `.devad/docs/` is curated docs and handoff history. Open only a named file
  cited by the user, current handoff, or exact task signal.
- `.devad/features/` is feature history. Open only the current feature handoff,
  a named evidence file, or a prompt/report you are explicitly updating.
- `.devad/archive/`, `.devad-dont-read/`, old reports, old proof trees, and old
  chat exports are denied by default. Require a narrow reason and read the
  smallest named file.
- Never load all `.devad/rules`, `.devad/docs`, or `.devad/features`.

## Commit Discipline

- Treat `.devad` as the project's working reference layer. Task-related
  `.devad` docs, feature handoffs, prompts, proof summaries, ledgers, and rule
  changes are not noise; commit and push them with the implementation.
- Keep reads narrow, but keep Git upload complete: stage the `.devad` files that
  explain the work and leave unrelated old feature/proof trees unstaged unless
  the task touched them.
- Before final, run a scoped status check for `.devad` and report any unstaged
  task-related files. Do not hide them behind "unrelated .devad noise".
- Never commit `.devad` files containing secrets, raw provider responses,
  cookies, OAuth codes, `.env` values, full deploy JSON, or token-bearing logs.

## Domain Pack Selector

| Task signal | Read |
| --- | --- |
| CORE/XCO product boundary, SITE/POST/AI/CHAT, bridge, audit, workspace scope | `.devad/rules/devad-architecture.md` |
| Laravel routes, controllers, services, migrations, policies, jobs, Cashier, Socialite, Wayfinder, Pest | `.devad/rules/devad-backend-laravel.md` |
| Dashboard/admin/sidebar/app tabs/authenticated React | `.devad/rules/devad-dashboard-frontend.md` |
| Public/marketing/free-tools/SEO/header/footer | `.devad/rules/devad-public-frontend.md` |
| `/chat-offer`, checkout CTA visuals, Core Theme v2 | `.devad/rules/devad-marketing-theme.md` |
| Deploy/env/domain/Dokploy/logs | `.devad/rules/devad-deploy-dokploy.md` |
| Merge risk/security/auth/billing/workspace scope/review | `.devad/rules/devad-pr-review-gate.md` |

## Default

If no domain pack clearly matches, read source first. Do not read more `.devad`
to compensate for unclear task scope; ask the user or make a small, verified
inspection plan.
