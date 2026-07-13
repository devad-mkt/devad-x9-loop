# Continuation And Timer Policy

Files are passive truth. They do not wake a Codex task. Normal unattended
continuation uses `references/direct-event-callback.md`: Worker or Thinx writes
its durable receipt, then sends one `EVENT_READY` signal to the same registered
Linx task.

## Default

A replacement Linx cannot act before a valid `LINX_ACTIVATION_OK`. A callback
pass that sees an active lock returns `SKIP_ACTIVE_MANAGER_PASS`.

- Recurring pickup automation: `OFF`.
- Recurring 15/19-minute pickup is forbidden.
- Do not create a recurring monitor merely to keep work moving.
- Do not recreate an automation that the owner paused or disabled.
- `PAUSE_NOT_DELETE`: pause it and archive its definition/location. Deletion
  requires exact owner approval.
- One bounded action means one action per Linx pass. The next valid callback
  starts the next pass.

Before dispatch, Linx records exact task/role/dispatch/packet/receipt identity.
Linx releases `MANAGER_PASS_LOCK` before Worker or Thinx execution. On callback,
Linx reacquires the lock, validates the event, performs one pass, saves durable
state, and releases the lock.

## Direct Callback

The target must send this only after durable state is written:

```text
EVENT_READY
LINX_TASK_ID: <registered Linx task id>
SOURCE_TASK_ID: <registered source task id>
SOURCE_ROLE: WORKER | THINX
DISPATCH_ID: dsp-<uuid>
PACKET_SHA256: <64 hex>
EVENT_TYPE: PLAN_READY | HANDOFF_READY | DECISION_READY | BLOCKED | FAILED
RECEIPT_PATH: <repository-relative path>
RECEIPT_SHA256: <64 hex>
```

Linx validates the same registered Linx task, source role/task, dispatch,
packet hash, unseen event, receipt path/hash, owner scope, and pass lock. Chat
text cannot replace the receipt.

Retry unchanged callback delivery at most three times using the same identity.
After failure, write `MANAGER_WAKE_FAILED` and require manual pickup. Never
replace failure with recurring polling.

## Owner-Requested One-Shot Fallback

A one-shot timer is allowed only when the owner explicitly asks for:

- a delayed owner-decision deadline, or
- an external wait that cannot send a callback.

Required: exact target, absolute deadline/timezone, one run, one allowed action,
and no renewal. Silence never approves push, deploy, merge, spend, destructive
work, branch changes, or live mutation.

## Stale And Safety Stops

Reject or stop pickup for:

- wrong task/role/dispatch/packet/receipt identity,
- reused or already acknowledged event,
- stale capsule/local-work truth,
- an active unexpired manager pass lock,
- a newer owner message or direction that changes scope,
- branch/HEAD or resource-claim conflict,
- missing security, commit, push, deploy, or live-proof gate.

A callback may route only the smallest currently authorized next action. It
never invents approval.
