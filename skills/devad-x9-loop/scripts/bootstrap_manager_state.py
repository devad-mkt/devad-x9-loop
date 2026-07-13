#!/usr/bin/env python3
"""Create missing .devad/manager state files without overwriting by default."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def write_if_missing(path: Path, text: str, force: bool, changed: list[str], skipped: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        skipped.append(str(path))
        return
    path.write_text(text, encoding="utf-8", newline="\n")
    changed.append(str(path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Devad X9 manager state files.")
    parser.add_argument("--repo", required=True, help="Path to core-x9 repo")
    parser.add_argument("--mission", default="Use one lightweight X9 manager to coordinate worker threads without fake done claims.")
    parser.add_argument("--current", default="Bootstrap Devad X9 manager state.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing manager files")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        print(json.dumps({"status": "BLOCKED", "error": f"repo not found: {repo}"}, indent=2))
        return 2

    manager = repo / ".devad" / "manager"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    changed: list[str] = []
    skipped: list[str] = []

    (manager / "workers").mkdir(parents=True, exist_ok=True)
    (manager / "passes").mkdir(parents=True, exist_ok=True)
    (manager / "handoffs").mkdir(parents=True, exist_ok=True)
    (manager / "sidecar").mkdir(parents=True, exist_ok=True)
    (manager / "traces").mkdir(parents=True, exist_ok=True)

    write_if_missing(
        manager / "MISSION.md",
        f"""# Manager Mission

## Original Goal

{args.mission}

## Current User Priority

{args.current}

## Non-Goals

- Do not make the manager an app-code worker.
- Do not make Top Manager read thread chats or worker chats.
- Do not run a heavy autonomous swarm.
- Do not treat worker PASS as verified truth.
- Do not revive X7 manager-control inbox/outbox loops.

## Hard Gates

- truth lock before manager decisions
- Top Manager reads durable `.md` state only
- Sub Manager writes missing chat facts into `.devad`
- Sub Manager saves reusable owner answers in ANSWERED_DECISIONS.md
- Sub Manager saves repeated tool routes and failures in TOOL_LESSONS.md
- worker packet before worker assignment
- worker STATUS.md plus top CURRENT_STATUS before trusting handoffs
- proof before PASS
- separate source push, deploy readiness, and live deploy gates
- no deploy without DEPLOY_GATE.md and DEPLOY_APPROVED for the exact SHA
- newest user instruction overrides old callback or legacy heartbeat
- no merge without manager verification
- no secrets in artifacts
- local-only work must be classified in LOCAL_WORK_LEDGER.md before push, deploy, or done claims
- Thinx uses GPT-5.6 Sol Ultra; Linx uses GPT-5.6 Sol extra high; Worker, CHUNK, and SIDE use GPT-5.6 Terra extra high unless owner writes LOWER_MODEL_OK:<role>:<reason>

## Last Updated

{now} Europe/Istanbul
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "CENTRAL_FACTS.md",
        f"""# Central Facts

CENTRAL_FACTS:
- Updated: {now} Europe/Istanbul
- Latest user override: {args.current}
- Active lane: none
- Feature ID: none
- Role: Sub Manager
- Repo root: {repo}
- Manager-state worktree: {repo}
- Manager-state branch: UNKNOWN
- Manager-state HEAD: UNKNOWN
- Implementation worktree: UNKNOWN
- Implementation branch: UNKNOWN
- Implementation HEAD: UNKNOWN
- Deployment branch: UNKNOWN
- Deployment HEAD: UNKNOWN
- Target SHA: UNKNOWN
- Must reach: UNKNOWN
- Must not: code, push, deploy, or route workers until this file is refreshed
- Required proof: UNKNOWN
- Current blocker: bootstrap facts need refresh
- Exact next action: refresh truth lock and mission lock
- Detail links: MISSION.md, CURRENT.md, TRUTH_LOCK.md, QUEUE.md, HANDOFF_INDEX.md
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "MISSION_LOCK.md",
        f"""# Mission Lock

MISSION_LOCK:
- Updated: {now} Europe/Istanbul
- Owner goal: {args.mission}
- Active lane: none
- Feature ID: none
- Repo root: {repo}
- Implementation branch: UNKNOWN
- Deployment branch: UNKNOWN
- Target SHA: UNKNOWN
- Must reach: UNKNOWN
- Finish only when: required proof is explicit and verified
- Forbidden actions: code, push, deploy, or broad worker routing until lock is refreshed
- Required gates: truth lock, branch check, central facts, proof plan
- Owner waivers: none
- If mismatch: stop with MISSION_LOCK_MISMATCH
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "CURRENT.md",
        f"""# Current Manager State

**Latest user override:** {args.current}
**Status:** BOOTSTRAP
**Updated:** {now} Europe/Istanbul
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "LOCAL_WORK_LEDGER.md",
        f"""# Local Work Ledger

Updated: {now} Europe/Istanbul

CURRENT_LOCAL_WORK:
- Ledger status: BLOCKED
- Active lane: none
- Repo root: {repo}
- Checkout role: OTHER
- Checkout branch: UNKNOWN
- Checkout HEAD: UNKNOWN
- Manager-state branch: UNKNOWN
- Manager-state HEAD: UNKNOWN
- Implementation branch: UNKNOWN
- Implementation HEAD: UNKNOWN
- Deployment branch: UNKNOWN
- Deployment HEAD: UNKNOWN
- Target SHA: UNKNOWN
- Tracked dirty files: UNKNOWN
- Untracked files: UNKNOWN
- Active-lane local work: UNKNOWN
- Exact next check: run build_local_work_ledger.py --repo <repo> --write

## Release States

| State | Meaning | Manager rule |
| --- | --- | --- |
| `PLANNED_ONLY` | Docs/plans/proof exist but not code-live. | Do not count as shipped. |
| `UNCOMMITTED` | Local dirty or untracked implementation/docs exist. | Classify before push/deploy. |
| `SOURCE_ONLY` | Source branch has it, live branch may not. | Bridge/deploy proof needed. |
| `V105_READY` | Exact v105 branch has intended SHA. | Deploy gate still required. |
| `DEPLOYED` | Dokploy/live target has exact SHA. | Browser/live proof still required. |
| `LIVE_PROOF_PASS` | Live proof passed for exact SHA. | Only that SHA/scope is done. |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "TOP_MANAGER.md",
        f"""# Top Manager

**Status:** ACTIVE
**Updated:** {now} Europe/Istanbul
**Rule:** read `.md` state only; do not read thread chats, worker chats, old manager chat, or conversation memory.

## Current View

| Lane | Status | Risk | Missing MD | Next |
| --- | --- | --- | --- | --- |

## One Next Action

NO_ACTION
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "MODEL_POLICY.md",
        f"""# X9 Model Policy

**Updated:** {now} Europe/Istanbul
**Status:** ACTIVE

| Thread title | Compatibility role | Model | Thinking | Waiver |
| --- | --- | --- | --- | --- |
| Thinx | Top Manager | `GPT-5.6 Sol Ultra` | `Ultra` | `LOWER_MODEL_OK:Top Manager:<reason>` |
| Linx | Sub Manager | `GPT-5.6 Sol` | `xhigh` / extra high | `LOWER_MODEL_OK:Sub Manager:<reason>` |
| Worker | Worker | `GPT-5.6 Terra` | `xhigh` / extra high | `LOWER_MODEL_OK:Worker:<reason>` |
| Worker Reader | Hidden non-decision subagent | `gpt-5.6-luna` | `medium` | standing owner exception |
| Worker CHUNK | CHUNK Codex helper | `GPT-5.6 Terra` | `xhigh` / extra high | `LOWER_MODEL_OK:CHUNK:<reason>` |
| Worker SIDE | SIDE Codex helper | `GPT-5.6 Terra` | `xhigh` / extra high | `LOWER_MODEL_OK:SIDE:<reason>` |

Use the host-supported identifier for each named profile. Title new threads
`Thinx`, `Linx`, or `Worker` as shown above.

Worker Reader may use its cheaper profile only as a hidden Thinx subagent for
exact-file extraction with a digest and verified receipt. Never create a
visible Reader task. It cannot make decisions.

If a tool cannot enforce model/thinking, write
`MODEL_PROFILE_NOT_TOOL_ENFORCED:<role>:<thread>` in the pass note.
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "TRUTH_LOCK.md",
        f"""# X9 Truth Lock

**Updated:** {now} Europe/Istanbul
**Latest user override:** {args.current}
**Status:** BOOTSTRAP

Refresh this file with current git truth before using it for manager decisions.
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "WORKERS.md",
        """# Workers

Generated by `collect_worker_handoffs.py --write-workers`.
Use the installed X9 manager model policy; do not hand-edit a second model table.

| Lane | Feature | Status | Packet | Worktree | Branch | Next |
| --- | --- | --- | --- | --- | --- | --- |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "QUEUE.md",
        """# Manager Queue

| Priority | Lane | Owner | Status | Blocker | Next action | Updated |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | none | - | empty | - | - | - |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "LIMITS.md",
        """# Manager Limits

| Budget | Top Manager | Sub Manager | Worker |
| --- | ---: | ---: | ---: |
| Thread chat reads | 0 | 1 per missing/contradictory handoff | own chat only |
| Active lanes reviewed per pass | 8 | 6 | 1 |
| Same-method proof failures | 0 | 2 | 2 |
| Continuous routing time | 20 min | 90 min | per contract |
| Major direction changes before handover | 1 | 2 | 1 |

If a budget is exceeded, write a pass note and choose handover, restart,
watchdog check, or user decision. Do not keep routing from tired context.
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "OWNER_WAIT.md",
        """# Owner Wait

**Status:** OFF
**Created:** none
**Deadline:** none
**Question:** none
**Default verdict if no answer:** none
**Must not do before deadline:** none

## Options

| Option | Risk | Proof needed | Worker impact |
| --- | --- | --- | --- |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "HANDOFF_MONITOR.md",
        """# Handoff Monitor (Legacy)

**Status:** RETIRED
**Recurring pickup:** FORBIDDEN
**Replacement:** manager/loop/DISPATCH_LEDGER.jsonl plus EVENT_CURSOR.json

Normal continuation uses a verified EVENT_READY callback to the same registered
Linx task. This file is retained only so older projects are not deleted.
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "HEARTBEAT.md",
        """# Manager Heartbeat (Legacy)

**Status:** OFF
**Recurring pickup:** FORBIDDEN
**One-shot fallback:** OWNER_REQUEST_ONLY
**Replacement:** verified EVENT_READY direct callback
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "HANDOFF_INDEX.md",
        """# Worker Handoff Index

**Updated:** never

| Lane | Feature | Status | Local | Security | Commit | Push | Deploy | Live | Next | Updated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | - | - | - | - | - | - | - | - | - | - |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "ANSWERED_DECISIONS.md",
        f"""# Answered Decisions

**Updated:** {now} Europe/Istanbul

| Key | Answer | Scope | Status | Source | Updated |
| --- | --- | --- | --- | --- | --- |
| bootstrap | No reusable owner answers recorded yet. | all | NEEDS_REFRESH | bootstrap | {now} |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "TOOL_LESSONS.md",
        f"""# Tool Lessons

**Updated:** {now} Europe/Istanbul

| Tool/route | Status | Use when | Do first | Do not repeat | Evidence | Updated |
| --- | --- | --- | --- | --- | --- | --- |
| Chrome authenticated proof | UNKNOWN | devad.io auth proof | Check exposed Chrome/Codex browser tool or owner-approved existing profile/CDP/Windows UI route. | Do not treat fresh Playwright login redirect as auth proof. | none | {now} |
| OpenCode SIDE | UNKNOWN | GLM/Kimi packet review | Use saved packet only; prefer devad-assistant, then one direct OpenCode fallback if available. | Do not loop wrapper failures. | none | {now} |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "DEPLOY_GATE.md",
        """# Manager Deploy Gate

**Status:** BLOCKED
**Target SHA:** none
**DEPLOY_APPROVED:** none
**Updated:** never

| Check | Status | Proof |
| --- | --- | --- |
| Security review for exact commit range | BLOCKED | missing |
| Local intended HEAD equals source remote HEAD | BLOCKED | missing |
| Sidecar/live dependencies ready or owner-waived | BLOCKED | missing |
| Dokploy branch policy verified | BLOCKED | missing |
| Live proof plan exists | BLOCKED | missing |
| No stale PASS in handoff used as authority | BLOCKED | missing |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "DECISIONS.md",
        """# Decisions

| Time | Decision | Scope | Source |
| --- | --- | --- | --- |
""",
        args.force,
        changed,
        skipped,
    )

    write_if_missing(
        manager / "RISKS.md",
        """# Risks

| Risk | Impact | Owner | Status | Next |
| --- | --- | --- | --- | --- |
""",
        args.force,
        changed,
        skipped,
    )

    result: dict[str, Any] = {
        "status": "PASS",
        "repo": str(repo),
        "manager": str(manager),
        "changed": changed,
        "skipped_existing": skipped,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
