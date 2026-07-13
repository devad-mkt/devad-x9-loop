# Direct Event Callback

Use this for normal unattended continuation after Linx dispatches a Worker or
Thinx. Durable files carry truth; one direct task message carries only the wake
signal.

## Required Flow

1. Linx records the target task ID, immutable role, `DISPATCH_ID`, packet
   SHA-256, and expected receipt in durable loop state.
2. Linx releases `MANAGER_PASS_LOCK` before the target begins. The lock protects
   manager passes; it must not block Worker or Thinx execution.
3. The target writes `STATUS.md`, `HANDOFFS.md`, its immutable event, and the
   owned receipt before sending any callback.
4. The target sends one `EVENT_READY` message to the same registered Linx task.
5. Linx validates identity, receipt hash, unseen event, current lock, and current
   owner scope before starting one new manager pass.
6. Linx acknowledges the exact callback and processes at most one bounded next
   action. A new callback starts a new pass.

`One bounded action` means one action per manager pass. It does not mean stop
the project after dispatch.

## Callback Envelope

```text
EVENT_READY
LINX_TASK_ID: <registered Linx task id>
SOURCE_TASK_ID: <registered Worker or Thinx task id>
SOURCE_ROLE: WORKER | THINX
DISPATCH_ID: dsp-<uuid>
PACKET_SHA256: <64 hex>
EVENT_TYPE: PLAN_READY | HANDOFF_READY | DECISION_READY | BLOCKED | FAILED
RECEIPT_PATH: <repository-relative durable path>
RECEIPT_SHA256: <64 hex>
```

The message is a signal, not authority. Linx reads the exact durable receipt and
event before acting. Wrong role, task, dispatch, packet, receipt, or reused event
is rejected.

## Delivery Rules

- Send to the same registered Linx task; never create a replacement Linx.
- Use the same dispatch ID and packet hash when retrying an unchanged callback.
- Record every callback attempt and acknowledgement in the delivery ledger.
- Make at most three direct delivery attempts.
- Exact acknowledgement stops retries.
- Transport accepted without acknowledgement: check the receipt once before
  retrying; never resend blindly.
- Changed payload creates a superseding event/dispatch identity.
- After bounded failure, write `MANAGER_WAKE_FAILED` with attempts and durable
  receipt details, then tell the owner manual pickup is needed.

## Timer Rule

Recurring 15/19-minute pickup is forbidden. Do not create or renew recurring
pickup after dispatch, handoff, Thinx review, or Linx activation.

An owner-requested one-shot fallback is allowed only for an explicit delayed
owner decision or an external condition that cannot send a callback. It must
have one target, one deadline, one run, and no renewal. A direct callback remains
the default.
