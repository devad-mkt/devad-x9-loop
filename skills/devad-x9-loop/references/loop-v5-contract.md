# X9 Loop v5 Contract

## Authority

1. Current Git/runtime proof.
2. X9 shared contract.
3. Current owner packet and decision gates.
4. Valid compact loop state.
5. Historical manager files.
6. Chat narration.

Chat never overrides task identity, packet hash, receipt, current local work,
or a current owner decision.

## Immutable Roles

`ROLE_REGISTRY.json` is keyed by Codex task ID. Allowed roles are `LINX`,
`THINX`, `WORKER`, `READER`, `CHUNK`, and `SIDE`. Add roles; never change
one in place. A correction is a superseding event with owner or Thinx approval.
Titles are never routing data.

## Dispatch Identity

A dispatch is:

`dispatch_id + sender_task_id + target_task_id + target_role + packet_sha256`

The append-only ledger records creation, attempts, acknowledgement, receipt,
supersession, and circuit-breaker events. Rewriting ledger lines is forbidden.
Packet mutation always creates a new dispatch.

## Event Completion And Pickup

Worker completion is accepted only when task ID, dispatch ID, role `WORKER`,
packet SHA-256, and Worker-owned receipt match. Thinx decisions use the same
identity checks with role `THINX`. Record the accepted immutable event ID in
`EVENT_CURSOR.json` before routing dependent work.

After durable state is written, Worker or Thinx sends one `EVENT_READY`
callback to the same registered Linx task. Linx validates the exact receipt
before acting. Recurring 15/19-minute pickup is forbidden. Direct delivery is
bounded to three attempts; failure writes `MANAGER_WAKE_FAILED`.

## Scheduling

Dependencies must be complete and resource claims free. Claims cover files,
database, browser/runtime, providers, and deployment. Shared browser/runtime
and deploy are single-owner pools. Three failures pause the dispatch and open
a Thinx decision gate; they do not block the feature.

## Linx Barrier

Linx may read only the newest owner turn directly. It first saves exact text,
attachments, hashes, and visual receipt. Later passes use durable owner packet,
pass capsule, registry, unseen events, task graph, claims, gates, worktree
index, and exact Worker packet. Historical chat is ignored.

## Orca Concepts Adopted

Adopt task/dispatch identity, dependency-ready queue, decision gates, scoped
completion authority, three-failure circuit breaker, stale-Worker warning, and
full-handoff versus supervised-dispatch modes.

Do not integrate Orca runtime. Reject runtime DB truth, four-Worker default,
20-commit staleness, two-second model polling, automatic Worker kill, or
external orchestration replacing `.devad` and Git truth.
