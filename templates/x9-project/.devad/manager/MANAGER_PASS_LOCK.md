# Manager Pass Lock

**Status:** FREE | ACTIVE | STALE
**Pass ID:** NONE
**Source:** OWNER | HEARTBEAT | NONE
**Started:** NONE
**Expires:** NONE
**Owner input ID:** NONE
**Thread/turn:** NONE

Rules:

- One direct manager pass or heartbeat owns this lock at a time.
- If another unexpired pass is active, return `SKIP_ACTIVE_MANAGER_PASS`.
- A newer owner message cancels heartbeat work.
- Release the lock before final chat.
- Mark `STALE` only after expiry and a read-only task-status check.
- A stale lock never authorizes mutation or duplicate routing.
