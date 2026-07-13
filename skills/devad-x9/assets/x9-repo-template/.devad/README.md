# Devad X9 Repo Memory

X9 is the active repo-local router for this checkout.

Use `<project-root>` for new X9 work. Paths containing `deploy`,
`bridge`, `v105`, or `x9w\v105`, detached HEAD checkouts, and the
`<deployment-branch>` branch are deploy bridges only:
inspect, export diff, verify deploy, or apply a committed X9 change. Do not
resume feature/debug/docs work there.

Read order for nontrivial work:

1. `.devad/X9.md`
2. `.devad/ACTIVE.md` only for branch, resume, deploy, merge-risk, or handoff work
3. Current feature `HANDOFF.md` only when routed
4. `.devad/rules/x9-read-policy.md` only for broad/noisy tasks or domain-pack selection
5. One routed `.devad/rules/*.md` domain pack
6. Focused source/runtime evidence

Do not read all `.devad/rules` by default.

## Preserved History

- `.devad/features/` is preserved.
- `.devad/docs/` is preserved.
- X5/X7 router originals and retired X7/ACP control-plane material are archived
  under `.devad/archive/x5-x7-disabled-2026-06-22/`.

Do not read archived X5/X7 material, old proof folders, generated reports, or
old chat exports unless the current task gives a narrow reason.

## Sidecars

Sidecars are direct headless CLI only through `.devad/tooling/opencode-cli/`.
Do not use ACP, PI workflow execution, or OpenRouter routes.
