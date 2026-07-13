# X9 Acceptance And Visible Proof

Use for tasks with user-named URLs, visible UI behavior, deploy/live proof,
provider/platform proof, API/CLI/MCP proof, or any request where "done" depends
on what a user can actually see or use.

## Before Coding

Turn the user's exact bullets into an acceptance matrix before edits:

| Requirement | Surface | Expected visible/action result | Proof method | Status |
| --- | --- | --- | --- | --- |

Rules:

- Every user-named URL, page, provider, platform, command, or output gets a row.
- Keep wording concrete: expected labels, buttons, toggles, cards, account IDs,
  publish options, external marker, or API response state.
- If a row needs owner secrets, provider approval, live write permission, or a
  branch/deploy decision, mark it `BLOCKED` before coding instead of hiding it.
- Do not expand scope silently. Add rows only for the requested behavior and the
  smallest dependent proof needed to make it real.

## Proof Semantics

- UI `PASS` requires rendered user-visible evidence in the browser/DOM/screenshot
  for the exact named surface. Route loads, hidden Inertia props, config arrays,
  source constants, tests, and `/health 200` are not UI proof.
- Deploy `PASS` requires the deployed branch/commit to contain the change plus
  the requested browser/API proof. `/health 200` alone only proves the app is
  alive.
- Provider/platform `PASS` requires CORE/API success plus exact unique marker
  visible on the external provider URL/page/message when live proof is in scope.
- API-only success is not final provider PASS. Use a partial status instead.
- CLI/MCP proof must call CORE API/services only. They must not write directly
  to social providers.
- Never write secrets, tokens, cookies, OAuth codes, raw provider responses,
  `.env` values, or real API keys into docs, payloads, screenshots, packets, or
  Git.

## .devad Upload Requirement

- If an acceptance matrix, proof matrix, handoff, prompt, progress ledger, or
  rule file is created or updated for the task, it must be staged, committed,
  and pushed with the implementation commit or a clearly named companion commit.
- Final status must include `.devad uploaded: yes/no`. If no, list the exact
  `.devad` files and why they were not uploaded.
- Do not use "unrelated .devad noise" as a reason to skip task-related docs.
  Only unrelated old history stays unstaged.

## Result Vocabulary

Use these terms consistently:

| Status | Meaning |
| --- | --- |
| `CODE_READY` | Source changes and local checks are ready, not deployed/proven live. |
| `DEPLOYED` | Correct commit is deployed, but full requested proof is not complete. |
| `LIVE_EXTERNAL_PASS` | Live CORE/API plus external marker or visible user proof passed. |
| `PARTIAL` | Some acceptance rows passed; at least one requested row is missing. |
| `BLOCKED` | A required row needs owner action, credentials, approval, or unsafe scope. |

Do not report `Ready to merge? yes`, `complete`, or final `PASS` while any
required row is `PARTIAL` or `BLOCKED` unless the user explicitly accepted that
reduced scope after seeing the matrix.

## Optional Feature References

Feature folders are reference packs, not startup memory.

- POST API/CLI/MCP/proof tasks may read only:
  `.devad/features/post-mcp-cli-api--2026-06-22/TASK.md`
- POST platform expansion tasks may read only:
  `.devad/features/post-platfroms-expansion-2026-06-22/execution-plan-full/TASK.md`

After reading a task file, read at most one linked section file that matches the
current lane. Never load either full folder by default.

## Final Proof Matrix

Finish with a visible proof matrix:

| Requirement | Surface | Evidence | Status |
| --- | --- | --- | --- |

If the evidence is "route loaded", "props present", "config exists", "tests
passed", or "health 200" for a visible UI requirement, mark the row `PARTIAL`,
not `PASS`.
