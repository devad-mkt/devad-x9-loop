from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "x9-project" / ".devad"
LOOP_FILES = (
    "ROLE_REGISTRY.json",
    "PASS_CAPSULE.json",
    "WORKTREE_INDEX.json",
    "TASK_GRAPH.json",
    "RESOURCE_CLAIMS.json",
    "EVENT_CURSOR.json",
    "DISPATCH_LEDGER.jsonl",
    "DECISION_GATES.json",
)
TASK_ID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def git_fact(repo: Path) -> dict[str, Any]:
    branch = run_git(repo, "branch", "--show-current") or "DETACHED_OR_UNKNOWN"
    head = run_git(repo, "rev-parse", "HEAD") or None
    status = run_git(repo, "status", "--short")
    return {
        "repo": str(repo),
        "branch": branch,
        "head": head,
        "dirty": bool(status),
        "local_change_count": len(status.splitlines()) if status else 0,
    }


def parse_current_roles(repo: Path) -> dict[str, dict[str, Any]]:
    workers = repo / ".devad" / "manager" / "WORKERS.md"
    if not workers.is_file():
        return {}
    text = workers.read_text(encoding="utf-8-sig", errors="replace")
    tasks: dict[str, dict[str, Any]] = {}
    for line in text.splitlines():
        ids = TASK_ID.findall(line)
        if not ids or not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().strip(chr(96)) for cell in line.strip().strip("|").split("|")]
        label = cells[0] if cells else "Unknown"
        lowered = label.lower()
        if "linx" in lowered or "sub manager" in lowered:
            role = "LINX"
        elif "thinx" in lowered or "top manager" in lowered:
            role = "THINX"
        else:
            role = "WORKER"
        task_id = ids[0].lower()
        tasks.setdefault(
            task_id,
            {
                "role": role,
                "title": "",
                "lane_label": label,
                "immutable": True,
                "source": ".devad/manager/WORKERS.md",
                "registered_at": now(),
            },
        )
    lock = repo / ".devad" / "manager" / "MANAGER_PASS_LOCK.md"
    if lock.is_file():
        lock_text = lock.read_text(encoding="utf-8-sig", errors="replace")
        explicit_roles = (
            (r"Replacement Linx:\s*[^0-9a-f]*(" + TASK_ID.pattern + r")", "LINX", "Replacement Linx"),
            (r"Locked THINX:\s*[^0-9a-f]*(" + TASK_ID.pattern + r")", "THINX", "Locked THINX"),
        )
        for pattern, role, title in explicit_roles:
            match = re.search(pattern, lock_text, re.I)
            if not match:
                continue
            task_id = match.group(1).lower()
            tasks[task_id] = {
                "role": role,
                "title": "",
                "lane_label": title,
                "immutable": True,
                "source": ".devad/manager/MANAGER_PASS_LOCK.md",
                "registered_at": now(),
            }
    return tasks


def worktree_records(repositories: list[Path], current_text: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    lowered_current = current_text.lower()
    explicit = {str(path.resolve()).lower() for path in repositories}
    for repository in repositories:
        raw = run_git(repository, "worktree", "list", "--porcelain")
        blocks = [block for block in raw.split("\n\n") if block.strip()]
        if not blocks and (repository / ".git").exists():
            blocks = [f"worktree {repository}\nHEAD {run_git(repository, 'rev-parse', 'HEAD')}"]
        for block in blocks:
            fields: dict[str, str] = {}
            for line in block.splitlines():
                key, _, value = line.partition(" ")
                fields[key] = value
            path_text = fields.get("worktree")
            if not path_text:
                continue
            path = Path(path_text).resolve()
            key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            fact = git_fact(path)
            branch = fields.get("branch", "").removeprefix("refs/heads/") or fact["branch"]
            if key == str(repositories[0].resolve()).lower():
                state, reason = "ACTIVE", "manager and implementation repository"
            elif key in explicit:
                state, reason = "ACTIVE", "explicit independent repository input"
            elif key in lowered_current:
                location = lowered_current.find(key)
                nearby = lowered_current[max(0, location - 120): location + len(key) + 120]
                paused = any(word in nearby for word in ("paused", "idle", "not_loaded", "historical", "canceled"))
                state = "PAUSED" if paused else "ACTIVE"
                reason = "current durable manager text references this checkout"
            else:
                state, reason = "UNKNOWN", "no current durable classification; age not used"
            records.append(
                {
                    "path": str(path),
                    "repository_common_dir": run_git(path, "rev-parse", "--git-common-dir") or None,
                    "branch": branch,
                    "head": fields.get("HEAD") or fact["head"],
                    "dirty": fact["dirty"],
                    "local_change_count": fact["local_change_count"],
                    "activity_state": state,
                    "classification_reason": reason,
                    "preservation": "PRESERVE",
                }
            )
    return records


def read_current_text(repo: Path) -> str:
    parts: list[str] = []
    for relative in (
        ".devad/manager/CURRENT.md",
        ".devad/manager/WORKERS.md",
        ".devad/manager/LOCAL_WORK_LEDGER.md",
        ".devad/manager/MANAGER_PASS_LOCK.md",
        ".devad/manager/HEARTBEAT.md",
    ):
        path = repo / relative
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8-sig", errors="replace"))
    return "\n".join(parts)


def lock_is_free(repo: Path) -> bool:
    path = repo / ".devad" / "manager" / "MANAGER_PASS_LOCK.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8-sig", errors="replace").upper()
    return any(token in text for token in ("STATUS: RELEASED", "RELEASED_", "EXPIRED", "FREE"))


def old_automation_disabled(repo: Path) -> bool:
    path = repo / ".devad" / "manager" / "HEARTBEAT.md"
    if not path.is_file():
        return True
    text = path.read_text(encoding="utf-8-sig", errors="replace").upper()
    active = "ACTIVE" in text and "19 MIN" in text
    disabled = any(token in text for token in ("DISABLED", "DELETED", "INACTIVE"))
    return disabled and not active


def build_state(repo: Path, extra_repos: list[Path]) -> dict[str, Any]:
    repositories = [repo, *extra_repos]
    current_text = read_current_text(repo)
    registry = {
        "schema": "x9-loop-role-registry-v1",
        "updated_at": now(),
        "tasks": parse_current_roles(repo),
    }
    worktrees = worktree_records(repositories, current_text)
    facts = [git_fact(item) for item in repositories]
    local_only = any(item["dirty"] for item in worktrees)
    worker_tasks = [
        {
            "id": task_id,
            "role": entry["role"],
            "status": "CUTOVER_PAUSED",
            "pool": "CODING" if entry["role"] == "WORKER" else "READ_ONLY",
            "dependencies": [],
            "worktree": None,
            "base_sha": None,
            "next_action": "Validate exact packet before activation",
        }
        for task_id, entry in registry["tasks"].items()
    ]
    deployment = facts[1] if len(facts) > 1 else {
        "repo": None,
        "branch": "UNKNOWN",
        "head": None,
        "dirty": None,
        "local_change_count": None,
    }
    capsule = {
        "schema": "x9-loop-pass-capsule-v1",
        "updated_at": now(),
        "status": "CUTOVER_BLOCKED" if not old_automation_disabled(repo) else "READY_FOR_OWNER_REVIEW",
        "owner_input_id": None,
        "mission": "Preserve current X9 work and activate deterministic identity routing",
        "manager_state": facts[0],
        "implementation": facts[0],
        "deployment": deployment,
        "active_task_ids": [],
        "verified_facts": [
            "roles keyed by durable task ID",
            "existing manager files preserved as history",
            "all discovered worktrees marked PRESERVE",
        ],
        "local_work": "LOCAL_ONLY_WORK" if local_only else "CLEAN_OR_REMOTE_ONLY",
        "next_action": "Owner disables old automation, then validates activation packet",
        "must_not": [
            "message existing Linx",
            "route from task title",
            "move, delete, clean, reset, stash, or overwrite worktrees",
        ],
    }
    return {
        "ROLE_REGISTRY.json": registry,
        "PASS_CAPSULE.json": capsule,
        "WORKTREE_INDEX.json": {
            "schema": "x9-loop-worktree-index-v1",
            "updated_at": now(),
            "repositories": facts,
            "worktrees": worktrees,
        },
        "TASK_GRAPH.json": {
            "schema": "x9-loop-task-graph-v1",
            "updated_at": now(),
            "pool_limits": {"CODING": 2, "READ_ONLY": 2, "RUNTIME_PROOF": 1, "DEPLOY": 1},
            "promotion": {
                "coding_limit": 2,
                "eligible": False,
                "required": {
                    "calendar_days": 3,
                    "dispatches": 10,
                    "lost_work": 0,
                    "identity_errors": 0,
                    "resource_conflicts": 0,
                    "critical_errors": 0,
                    "max_orchestration_retries": 1,
                },
            },
            "tasks": worker_tasks,
        },
        "RESOURCE_CLAIMS.json": {
            "schema": "x9-loop-resource-claims-v1",
            "updated_at": now(),
            "claims": [],
        },
        "EVENT_CURSOR.json": {
            "schema": "x9-loop-event-cursor-v1",
            "updated_at": now(),
            "processed_event_ids": [],
            "last_event_at": None,
        },
        "DISPATCH_LEDGER.jsonl": "",
        "DECISION_GATES.json": {
            "schema": "x9-loop-decision-gates-v1",
            "updated_at": now(),
            "gates": [
                {
                    "id": "disable-old-19-minute-automation",
                    "status": "PASS" if old_automation_disabled(repo) else "BLOCKED",
                    "evidence": ".devad/manager/HEARTBEAT.md",
                },
                {
                    "id": "manager-pass-lock-free",
                    "status": "PASS" if lock_is_free(repo) else "BLOCKED",
                    "evidence": ".devad/manager/MANAGER_PASS_LOCK.md",
                },
            ],
        },
    }


def activation_packet(repo: Path, state: dict[str, Any]) -> str:
    capsule = state["PASS_CAPSULE.json"]
    gates = state["DECISION_GATES.json"]["gates"]
    gate_lines = "\n".join(f"- {gate['id']}: {gate['status']}" for gate in gates)
    return f"""# X9 Loop v5 Activation Packet

Do not send automatically. Paste into a new task only after every gate is PASS.

Use $devad-x9-loop as Linx and $devad-x9 as repository router.

ROLE: LINX
MODEL: gpt-5.6 high
REPOSITORY: {repo}
PASS_CAPSULE: .devad/manager/loop/PASS_CAPSULE.json
ROLE_REGISTRY: .devad/manager/loop/ROLE_REGISTRY.json
TASK_GRAPH: .devad/manager/loop/TASK_GRAPH.json
DELIVERY_LEDGER: .devad/manager/loop/DISPATCH_LEDGER.jsonl

Gates:
{gate_lines}

Rules:
- Do not read old chat as authority.
- Do not message a Worker until task ID, role, dispatch ID, and packet hash are durable.
- Do not resend accepted transport without checking the exact receipt once.
- Preserve all worktrees. Route one bounded action only.
- Current local-work state: {capsule['local_work']}.
"""


def old_report(state: dict[str, Any]) -> str:
    rows = []
    for item in state["WORKTREE_INDEX.json"]["worktrees"]:
        rows.append(
            f"| {item['path']} | {item['activity_state']} | "
            f"{'DIRTY' if item['dirty'] else 'CLEAN'} | {item['classification_reason']} | PRESERVE |"
        )
    return """# OLD Migration Report

Planning report only. No checkout was moved, deleted, cleaned, reset, or stashed.
Age alone was not used.

| Checkout | State | Local | Reason | Action |
| --- | --- | --- | --- | --- |
""" + "\n".join(rows) + "\n"


def planned_paths(repo: Path) -> list[Path]:
    loop = repo / ".devad" / "manager" / "loop"
    paths = [repo / ".devad" / "ROUTER.md"]
    paths.extend(loop / name for name in LOOP_FILES)
    passes = repo / ".devad" / "manager" / "passes"
    paths.extend(
        (
            passes / "2026-07-13-x9-loop-v5-activation.md",
            passes / "2026-07-13-x9-loop-v5-old-migration-report.md",
        )
    )
    return paths


def write_new(path: Path, content: str | bytes) -> str:
    if path.exists():
        return f"PRESERVE_EXISTING:{path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
    return f"CREATED:{path}"


def apply_overlay(repo: Path, state: dict[str, Any]) -> list[str]:
    results: list[str] = []
    router = repo / ".devad" / "ROUTER.md"
    results.append(write_new(router, (TEMPLATE / "ROUTER.md").read_bytes()))
    loop = repo / ".devad" / "manager" / "loop"
    for name in LOOP_FILES:
        value = state[name]
        text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=True) + "\n"
        results.append(write_new(loop / name, text))
    passes = repo / ".devad" / "manager" / "passes"
    results.append(write_new(passes / "2026-07-13-x9-loop-v5-activation.md", activation_packet(repo, state)))
    results.append(write_new(passes / "2026-07-13-x9-loop-v5-old-migration-report.md", old_report(state)))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-destructive X9 Loop v5 overlay")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--extra-repo", action="append", default=[], type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    extra = [path.resolve() for path in args.extra_repo]
    if not (repo / ".devad").is_dir():
        print(f"ERROR: missing .devad: {repo}", file=sys.stderr)
        return 2

    paths = planned_paths(repo)
    if not args.apply:
        print("DRY_RUN: no files changed")
        for path in paths:
            action = "PRESERVE_EXISTING" if path.exists() else "WOULD_CREATE"
            print(f"{action}:{path}")
        return 0

    state = build_state(repo, extra)
    for result in apply_overlay(repo, state):
        print(result)
    print("ACTIVATION_NOT_SENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
