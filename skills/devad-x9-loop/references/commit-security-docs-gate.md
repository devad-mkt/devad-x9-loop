# Commit Security And Docs Gate

The normative commit gate is in:

`../../devad-x9/references/x9-shared-contract.md`

Apply its `Security Before Commit` and `Commit And Attestation` sections. Do
not maintain a second copy of those rules here.

## Handoff Wake Reality

`STATUS.md` and `HANDOFFS.md` are passive files. They do not wake a Codex task.
A Sub Manager wakes only from a user message, a bounded automation/monitor, or
a manual pickup pass.

If auto-pickup is requested, use a bounded change-detecting monitor that runs
`collect_worker_handoffs.py`. It must stop when there is no actionable delta.

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
