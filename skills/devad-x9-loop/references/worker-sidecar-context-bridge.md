# Worker Sidecar Context Bridge

Use this inside the Worker task. It does not create visible Codex tasks.

## Flow

    Worker durable task context
      -> hidden gpt-5.6-luna medium Reader
      -> runs/<run-id>/SIDE_INPUT.md
      -> strict sidecar/<review>.json
      -> safe wrapper: `opencode-go/glm-5.2` and `opencode-go/kimi-k2.7-code`
      -> runs/<run-id>/SIDE_REVIEWS.md
      -> Worker verifies and decides

The Luna Reader receives full durable task context: the current packet,
contract, plan, relevant code excerpts, exact failures, proof, constraints, and
questions. Never send raw chat, secrets, cookies, tokens, private customer
data, payment data, or unbounded logs.

Full durable task context includes the active owner-input bundle: exact owner
message, atomic requirements, attachment manifest, visual context, and required
attachment identities. When a sidecar route cannot receive image binaries,
state BINARY_NOT_DELIVERED and include verified visual facts plus hashes. Never
claim GLM/Kimi saw an image when they received only text.

Luna performs extraction and compression only. It cannot decide, approve,
code, mutate files, claim a blocker, or replace Worker judgment.

## PLAN_CHALLENGE

Run once after the Worker drafts its plan and before first mutation when the
task is nontrivial, high-risk, cross-file, migration, architecture, security,
money, deploy, or expected to run longer than 30 minutes.

1. Worker lists the exact questions and candidate plan.
2. Hidden gpt-5.6-luna medium builds SIDE_INPUT.md from full durable task
   context with a read receipt and omitted-secret statement.
3. Convert SIDE_INPUT.md into strict x9-sidecar-packet-v1 JSON, then ask both
   configured models through the safe wrapper to challenge the plan.
4. Worker writes SIDE_REVIEWS.md with advice, local verification, accepted
   points, rejected points, and final plan delta.

Tiny one-file obvious tasks may record PLAN_CHALLENGE: SKIPPED_TINY with reason.

## BLOCKER_CHALLENGE

Before final BLOCKED, reuse the existing SIDE_INPUT.md and add only the new
failure delta, attempts, evidence, and blocker question. Do not resend broad
history.

Ask both sidecars:

1. Is the blocker real?
2. What safe route remains?
3. What proof would change the verdict?
4. What assumption is likely wrong?
5. Continue, restart, ask owner, or stop?

The Worker must verify suggestions locally. Sidecar agreement is not proof.

## Bounded Use

- One PLAN_CHALLENGE per run.
- One BLOCKER_CHALLENGE per blocker claim.
- One attempt per sidecar route; record SIDECAR_UNAVAILABLE and continue with
  the safe local fallback.
- Reuse SIDE_INPUT.md; emit a new content-bounded JSON packet for each delta.
- No polling and no repeated multi-model debate.

## Required SIDE_INPUT.md

- Task identity, feature, lane, run, repo, branch, HEAD, dirty state.
- Goal, finish line, allowed and forbidden files.
- Relevant code/files with hashes or exact excerpts.
- Current plan or blocker claim.
- Attempts, tests, security/proof results.
- Constraints, answered decisions, tool lessons.
- Exact questions.
- READ_RECEIPT and SECRET_SAFE: PASS.

## Required SIDE_REVIEWS.md

- GLM output path and TLDR.
- Kimi output path and TLDR.
- Worker verification of each actionable point.
- Accepted/rejected advice with reason.
- Final plan delta or blocker verdict.
- No model may write PASS, deploy approval, or production truth.
