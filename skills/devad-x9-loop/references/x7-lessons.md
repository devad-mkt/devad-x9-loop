# X7 Lessons

X7 was a useful failed experiment. Learn from it, but do not revive it.

## Keep

| X7 idea | X9 manager form |
| --- | --- |
| Context gate before old logs/proofs | Deny old context by default. Read old files only with a narrow reason. |
| Worker path ownership | Allowed and forbidden files in worker packets. |
| Claims vs actual changed files | `validate_worker_packet.py --worktree`. |
| Base SHA and branch drift checks | `check_x9_manager_state.py` and worker packet validation. |
| `git diff --check` | Required manager verification. |
| Conflict marker scan | Required manager verification. |
| Strict worker report envelope | `STATUS.md`, top `CURRENT_STATUS`, and `HANDOFFS.md`; old handoff text is history. |
| `CLAIMED_PASS` before manager verification | Keep exactly. |
| No transcript scraping | Keep exactly. |

## Reject

| X7 part | Reason |
| --- | --- |
| Manager-control inbox/outbox | Too much protocol and token overhead. |
| Heartbeat after every major worker step | Creates polling noise. |
| Registry + leases + claims + snapshots + reports | Too many state files to keep fresh. |
| Default four-chat layout | Too much parallelism when trust is low. |
| Model ladder and sidecar routing by default | Expands scope and token use. |
| Context gate script before normal source reads | Use narrow reads directly unless old context is involved. |
| Active `.devad/coordination/control/*` protocol | Becomes a system to manage instead of a check. |

## Porting Rule

Port X7 checks, not X7 control.

The X9 manager should be a small verifier:

```text
truth lock -> worker packet -> read-only git/proof check -> correction or one next action
```

Do not add a daemon, worker inbox/outbox, broad observe loop, multi-model fan-out, or autonomous merge controller unless the user explicitly accepts the token and merge-risk cost for a bounded experiment.
