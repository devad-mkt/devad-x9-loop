# Devad Safety Gates

Use for branch/base risk, mission scope, settings authority, proof, browser verification, noisy context, and token budget.

## Hard Gates

- If the request is broad, sensitive, or ambiguous, define mission, current slice, non-goals, proof path, rollback/fallback, and owner decisions before coding.
- Short replies like `ok`, `continue`, or `fix it` are not approval for merge, deploy, reset, force-push, secret rotation, data deletion, billing/auth changes, or broad scope expansion.
- Before branch work, compare repo path, Git branch, upstream, HEAD, dirty files, `.devad/ACTIVE.md`, and current `HANDOFF.md`. If Git and ACTIVE disagree, stop before edits.
- Base new work on the verified remote tip or verified deployed commit, not a same-named stale local branch.
- Refresh `.devad/ACTIVE.md` and feature `HANDOFF.md` after branch switch/start/resume, base/merge-target change, commit, push, PR/compare URL, deploy, verification, blocked state, or final handoff.
- For settings-controlled UI/behavior, build a compact authority map before edits: setting key, owner scope, dashboard location, code reader/writer, affected roles, allowed change, and proof source.
- Source proves ownership; browser/runtime proves visible behavior; tests/build/deploy evidence prove claims. External models do not prove facts.
- For old chats, raw JSONL, logs, broad reports, generated output, or noisy history, use targeted searches and small capped slices only.
- If token burn or budget is mentioned, avoid broad logs, broad deploy objects, old chats, full reports, multi-model fan-out, and full-suite reruns unless required.

## Completion

Do not call a hard task done unless the final answer separates mission complete, slice complete, skipped, blocked, and remaining owner action.
