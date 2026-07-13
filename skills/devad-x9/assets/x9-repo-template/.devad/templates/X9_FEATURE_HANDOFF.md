# X9 Feature Handoff

Use this compact handoff for completed, partial, or blocked X9 feature slices.
Do not paste secrets, raw provider responses, cookies, tokens, `.env` values, or
full deploy JSON.

## TLDR

| Item | Value |
| --- | --- |
| Feature |  |
| Repo / branch / HEAD |  |
| Next source folder | `<project-root>` |
| Bridge folder status | `none` / `active` / `locked` / `dirty orphan patch` |
| Result | `CODE_READY` / `DEPLOYED` / `LIVE_EXTERNAL_PASS` / `PARTIAL` / `BLOCKED` |
| User-visible proof | pass/fail/partial/blocked |
| Deploy proof | pass/fail/partial/blocked/not in scope |
| `.devad` uploaded | yes/no |
| Unstaged `.devad` leftovers | none / list exact paths |
| Remaining owner action |  |

## Acceptance Matrix

| Requirement | Surface | Expected visible/action result | Evidence | Status |
| --- | --- | --- | --- | --- |

## Files Changed

| File | Area | Change |
| --- | --- | --- |

## .devad Files Uploaded

| File | Purpose |
| --- | --- |

## X9 To v105 Bridge Map

| X9 source commit | v105 bridge commit | Deployment/proof | Bridge status |
| --- | --- | --- | --- |

## Verification

| Check | Command or proof source | Result |
| --- | --- | --- |

## Not Done

| Item | Reason | Next step |
| --- | --- | --- |

## Risks

| Risk | Mitigation |
| --- | --- |

## Reviewer Checklist

- [ ] Acceptance matrix covers every user-named URL/surface/provider.
- [ ] Visible UI proof is rendered evidence, not hidden props or route loads.
- [ ] Deployed branch/commit contains the implementation when deploy is claimed.
- [ ] New feature/debug/docs work happened in `<project-root>`, not in a deploy/v105/bridge checkout.
- [ ] Any v105 bridge was marked `locked` after deploy; dirty bridges are recorded as `dirty orphan patch`, not continued.
- [ ] Exact X9 source commit -> v105 bridge commit mapping is recorded when deploy is claimed.
- [ ] Task-related `.devad` docs/proofs/handoffs/rules are committed and pushed.
- [ ] No raw secrets or raw provider responses are saved.
- [ ] `PASS` is not claimed for partial or blocked rows.
