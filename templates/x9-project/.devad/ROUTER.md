# X9 Project Router

Read this file first. Then read only the smallest linked file needed.

## Loop Lite v6 Fast Route

| Need | Read | Writer |
| --- | --- | --- |
| Current recovery truth | manager/loop-lite/SNAPSHOT.json | `loopctl.py` |
| One permitted Linx action | manager/loop-lite/runtime/ACTION.json | `loopctl.py` |
| Owner message and attachments | manager/loop-lite/contracts/OWNER_PACKET.json | Linx once |
| Exact Worker task | manager/loop-lite/contracts/TASK.json | `loopctl.py` |
| Worker completion | manager/loop-lite/contracts/RESULT.json | Worker |
| Feature lookup | features/features.index.json | Catalog builder |
| One Worker lane | manager/workers/<lane>/ROUTER.md | Worker/generated |
| One feature | features/<feature-id>/TASK.md | Feature owner |

Linx runs `loopctl.py reconcile`, reads only `runtime/ACTION.json`, performs
that exact transport action, and records its real result. Role comes from task
ID, never title. SQLite is ignored cache; `SNAPSHOT.json` is tracked recovery
truth.

## Stable Project Truth

These files remain useful when the exact task or shared X9 gate links them:

| Need | Read |
| --- | --- |
| Mission and exclusions | manager/MISSION_LOCK.md |
| Stable facts | manager/CENTRAL_FACTS.md |
| Local-only work | manager/LOCAL_WORK_LEDGER.md |
| Answered owner decisions | manager/ANSWERED_DECISIONS.md |
| Known tool lessons | manager/TOOL_LESSONS.md |
| Exact owner packet index | manager/owner-input/INDEX.md |
| Old project context | memory/CHAT-CATALOG.md |

## Historical v5 Evidence

Existing `manager/loop/`, `MANAGER_PASS_LOCK.md`, `LINX_HANDOVER_STATE.md`,
and large manager Markdown remain historical evidence. Do not delete, rewrite,
or parse them as current v6 authority.

## Rules

- Do not scan all manager, Worker, feature, memory, run, proof, or archive files.
- `STATUS.md` and `HANDOFFS.md` are generated human views, never parser authority.
- Current Git/runtime evidence beats stale durable narration.
- Missing required truth is `MISSING_MD`, not permission to read old chats.
- No recurring heartbeat, periodic poll, sleep loop, or Markdown pass lock.
- Preserve all worktrees and uncommitted work.
- Dispatch only dependency-ready tasks with exact, disjoint claims.
- Record unknown evidence as `Unknown`; never infer PASS.
