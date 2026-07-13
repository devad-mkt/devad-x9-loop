# Owner Wait And Handoff Continuation

Use this when Linx should wait for the owner before routing, or when Worker or
Thinx will finish later.

## Normal Handoff Continuation

Handoff files are passive. Normal unattended pickup is:

```text
Linx dispatch -> receiver writes durable receipt -> receiver sends EVENT_READY
-> same registered Linx validates -> one new manager pass
```

Recurring 15/19-minute pickup is forbidden.

Before final chat after a dispatch, Linx must prove all of these are recorded:

- exact registered Linx and receiver task IDs and roles,
- `DISPATCH_ID` and packet SHA-256,
- expected durable receipt path,
- receiver instruction to send `EVENT_READY`,
- manager pass lock released before receiver execution.

The receiver retries unchanged callback delivery at most three times. On
failure it writes `MANAGER_WAKE_FAILED`; manual pickup is then required. Linx
must not create recurring polling as a fallback.

## Continuation States

| State | Meaning |
| --- | --- |
| `CALLBACK_ARMED` | Receiver has exact Linx callback identity. |
| `EVENT_READY` | Durable receipt exists and callback was sent. |
| `CALLBACK_ACKNOWLEDGED` | Linx accepted the exact event identity. |
| `MANAGER_WAKE_FAILED` | Direct delivery failed after bounded attempts. |
| `OWNER_WAIT_ACTIVE` | Owner has a deadline/default in `OWNER_WAIT.md`. |
| `HARD_BLOCKED` | No safe fallback exists without owner, secret, or destructive action. |
| `OWNER_DECISION_REQUIRED` | Owner must choose risk, scope, money, deploy, or priority. |
| `NO_ACTION_VERIFIED` | No active actionable event remains. |

Do not finish with advice only after dispatch. Arm the direct callback and
release the lock.

## One-Hour Owner Wait

When the owner asks Linx to wait before choosing:

1. write `.devad/manager/OWNER_WAIT.md`,
2. record the exact owner question and safe options,
3. record an absolute deadline with timezone,
4. state the safest default verdict,
5. create one owner-requested one-shot fallback for that deadline only,
6. route no new implementation during the wait except a safety stop or
   explicitly allowed read-only evidence collection.

`OWNER_WAIT.md`:

```md
# Owner Wait

**Status:** ACTIVE | ANSWERED | EXPIRED | CANCELLED
**Question:** <exact owner decision>
**Created:** YYYY-MM-DD HH:mm Europe/Istanbul
**Deadline:** YYYY-MM-DD HH:mm Europe/Istanbul
**Default verdict:** <safest honest non-destructive action>
**One-shot target:** <same Linx task id>
**One-shot runs:** 0 | 1
**No silent approvals:** push, deploy, merge, spend, destructive actions
```

At the one-shot deadline:

1. check for a newer owner answer,
2. if answered, mark `ANSWERED` and follow it,
3. if unanswered, mark `EXPIRED`,
4. refresh durable truth and relevant receipts,
5. do bounded safe research,
6. choose the recorded safest non-destructive verdict,
7. do not renew the timer.

Owner silence never approves push, deploy, merge, provider spend, branch
changes, destructive cleanup, or live mutation.

## Allowed Without Owner

Linx may request missing durable status, proof paths, security evidence, or
read-only validation. It may stop unsafe work. It may not invent product scope,
accept money/security risk, or perform external mutations.
