# X9 Project Router

Read this file first. Then read only the smallest linked file needed.

## Current Route

| Need | Read | Writer |
| --- | --- | --- |
| One current project summary | manager/CURRENT.md | Linx |
| Mission and exclusions | manager/MISSION_LOCK.md | Linx |
| Stable facts | manager/CENTRAL_FACTS.md | Linx |
| Local-only work | manager/LOCAL_WORK_LEDGER.md | Linx |
| Answered owner decisions | manager/ANSWERED_DECISIONS.md | Linx |
| Known tool lessons | manager/TOOL_LESSONS.md | Linx |
| Current role model/effort | manager/MODEL_STATE.md | Linx |
| Manager pass concurrency | manager/MANAGER_PASS_LOCK.md | Linx callback/owner turn |
| Linx replacement transition | manager/LINX_HANDOVER_STATE.md | Old/new Linx by phase |
| Exact owner messages and attachments | manager/owner-input/INDEX.md | Linx |
| Worker handoff changes | manager/HANDOFF_INDEX.md | Linx/generated |
| Feature lookup | features/features.index.json | Linx/generated |
| One Worker lane | manager/workers/<lane>/ROUTER.md | Worker/Linx |
| One feature | features/<feature-id>/TASK.md | Feature owner |
| Old project context | memory/CHAT-CATALOG.md | devad-memory |

## Rules

- Do not scan all manager, Worker, feature, memory, run, proof, or archive files.
- STATUS.md and HANDOFFS.md contain current truth only.
- Follow relative links from the selected router.
- Git/runtime evidence beats stale durable text; update or block on the stale file.
- Missing required truth is MISSING_MD, not permission to read old chats.
- One manager pass at a time. A callback pass never overlaps an owner turn.
- A new Linx has no execution authority before validated `LINX_ACTIVATION_OK`.

## Loop v5 Fast Route

| Need | Read |
| --- | --- |
| Current verified pass | manager/loop/PASS_CAPSULE.json |
| Real task roles | manager/loop/ROLE_REGISTRY.json |
| All local worktrees | manager/loop/WORKTREE_INDEX.json |
| Unseen Worker events | manager/loop/EVENT_CURSOR.json |
| Ready/dependent tasks | manager/loop/TASK_GRAPH.json |
| Resource ownership | manager/loop/RESOURCE_CLAIMS.json |
| Dispatch delivery truth | manager/loop/DISPATCH_LEDGER.jsonl |
| Owner/Thinx gates | manager/loop/DECISION_GATES.json |

Role comes from task ID, never title. Before retry, check the exact dispatch ID,
packet hash, attempt count, Worker acknowledgement, and exact callback receipt.
Recurring 15/19-minute pickup is forbidden.
