# Manager Pass Lock

**Status:** FREE | ACTIVE | STALE
**Pass ID:** NONE
**Source:** OWNER | EVENT_CALLBACK | OWNER_ONE_SHOT | NONE
**Started:** NONE
**Expires:** NONE
**Owner input ID:** NONE
**Thread/turn:** NONE

Rules:

- One direct owner or event-callback manager pass owns this lock at a time.
- If another unexpired pass is active, return `SKIP_ACTIVE_MANAGER_PASS`.
- A newer owner message cancels callback work when it changes scope.
- Release the lock before receiver execution and before final chat.
- Mark `STALE` only after expiry and a read-only task-status check.
- A stale lock never authorizes mutation or duplicate routing.
