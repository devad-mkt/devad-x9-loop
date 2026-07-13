# Commit Security And Docs Gate

The normative commit gate is in:

`../../devad-x9/references/x9-shared-contract.md`

Apply its `Security Before Commit` and `Commit And Attestation` sections. Do
not maintain a second copy of those rules here.

## Handoff Wake Reality

`STATUS.md` and `HANDOFFS.md` are passive files. After writing the exact
receipt, Worker or Thinx sends one identity-checked `EVENT_READY` callback to
the same registered Linx task. Recurring 15/19-minute pickup is forbidden.
Callback delivery is bounded to three attempts; failure writes
`MANAGER_WAKE_FAILED` and requires manual pickup.

## Required Status Fields

```md
- Security precommit: PASS | BLOCKED | NOT_REQUIRED
- Post-commit docs: PASS | BLOCKED | NOT_REQUIRED | NOT_COMMITTED
- Latest commit: <C1 sha> | NONE
- Attestation commit: <C2 sha> | NONE
```

Validate a claimed commit with `validate_worker_packet.py`. Accept
`Post-commit docs: PASS` only when a tracked `.devad/docs/commits` record names
the exact C1 SHA. An attestation-only C2 is exempt from recursive records under
the shared contract.
