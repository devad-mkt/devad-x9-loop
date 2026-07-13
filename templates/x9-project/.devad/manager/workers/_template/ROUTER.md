# Worker Lane Router

Read this file first. Then read only the smallest linked file needed.

| Need | Read | Writer |
| --- | --- | --- |
| Current lane state | STATUS.md | Worker |
| Latest handoff | HANDOFFS.md | Worker |
| Scope and identity | MANIFEST.json | Linx |
| Current plan | runs/<run-id>/PLAN.md | Worker |
| Work detail | runs/<run-id>/WORKLOG.md | Worker |
| Security evidence | runs/<run-id>/SECURITY.md | Worker |
| Tests/proof | runs/<run-id>/PROOF.md | Worker |
| Commit/attestation | runs/<run-id>/COMMITS.md | Worker |
| Decisions/blockers | runs/<run-id>/DECISIONS.md | Worker |
| Luna-built sidecar context | runs/<run-id>/SIDE_INPUT.md | Worker Reader |
| GLM/Kimi advice and verification | runs/<run-id>/SIDE_REVIEWS.md | Worker |

STATUS.md and HANDOFFS.md are current-only files. Never append old run history
to them.
