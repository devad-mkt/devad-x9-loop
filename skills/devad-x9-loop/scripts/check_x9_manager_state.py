#!/usr/bin/env python3
"""Read-only Devad X9 manager state checker."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED_MANAGER_FILES = [
    "MISSION.md",
    "CENTRAL_FACTS.md",
    "MISSION_LOCK.md",
    "LOCAL_WORK_LEDGER.md",
    "CURRENT.md",
    "TRUTH_LOCK.md",
    "WORKERS.md",
    "HANDOFF_INDEX.md",
    "ANSWERED_DECISIONS.md",
    "TOOL_LESSONS.md",
]
OPTIONAL_MANAGER_FILES = ["HEARTBEAT.md", "DECISIONS.md", "RISKS.md"]


def run_git(repo: Path, args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        return {
            "cmd": "git " + " ".join(args),
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"cmd": "git " + " ".join(args), "returncode": 127, "stdout": "", "stderr": "git not found"}
    except subprocess.TimeoutExpired:
        return {"cmd": "git " + " ".join(args), "returncode": 124, "stdout": "", "stderr": "git command timed out"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_status(stdout: str, max_files: int) -> dict[str, Any]:
    tracked: list[str] = []
    untracked: list[str] = []
    for line in stdout.splitlines():
        if not line or line.startswith("##"):
            continue
        path = line[3:].strip() if len(line) >= 4 else line.strip()
        if " -> " in path:
            path = path.split(" -> ")[-1]
        path = path.replace("\\", "/")
        if line.startswith("??"):
            untracked.append(path)
        else:
            tracked.append(path)
    return {
        "tracked_count": len(tracked),
        "untracked_count": len(untracked),
        "tracked_top": tracked[:max_files],
        "untracked_top": untracked[:max_files],
    }


def ls_remote(repo: Path, remote: str, branch: str) -> dict[str, Any]:
    if not branch:
        return {"branch": branch, "sha": "", "status": "skipped"}
    ref = branch if branch.startswith("refs/") else f"refs/heads/{branch}"
    res = run_git(repo, ["ls-remote", remote, ref], timeout=30)
    sha = ""
    if res["returncode"] == 0 and res["stdout"]:
        sha = res["stdout"].split()[0]
    return {
        "remote": remote,
        "branch": branch,
        "ref": ref,
        "sha": sha,
        "status": "ok" if sha else "missing",
        "error": res["stderr"] if res["returncode"] != 0 else "",
    }


def parse_field(text: str, field: str) -> str:
    pattern = re.compile(rf"^\s*\*\*{re.escape(field)}:\*\*\s*(.+?)\s*$", re.I | re.M)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    pattern = re.compile(rf"^\s*[-*]\s*{re.escape(field)}:\s*(.+?)\s*$", re.I | re.M)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    pattern = re.compile(rf"^\s*{re.escape(field)}:\s*(.+?)\s*$", re.I | re.M)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def parse_datetime(value: str) -> datetime | None:
    if not value or value.lower() in {"none", "n/a"}:
        return None
    cleaned = value.replace("Europe/Istanbul", "").strip()
    cleaned = cleaned.replace("T", " ").replace("Z", "+00:00")
    if "+" in cleaned:
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            cleaned = cleaned.split("+", 1)[0].strip()
    match = re.search(r"\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?", cleaned)
    if match:
        cleaned = match.group(0)
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def is_attestation_head(repo: Path, recorded_head: str, current_head: str) -> bool:
    if not recorded_head or not current_head:
        return False
    parent = run_git(repo, ["rev-parse", "HEAD^"])
    subject = run_git(repo, ["show", "-s", "--format=%s", "HEAD"])
    if parent["returncode"] != 0 or subject["returncode"] != 0:
        return False
    recorded = recorded_head.strip().strip("`")
    parent_sha = parent["stdout"].strip()
    return (
        (parent_sha == recorded or parent_sha.startswith(recorded) or recorded.startswith(parent_sha[:12]))
        and subject["stdout"].strip().lower().startswith("docs(x9): attest ")
    )


def heartbeat_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "status": "missing", "stale": False, "warnings": []}
    text = read_text(path)
    status = parse_field(text, "Status") or "unknown"
    version = parse_field(text, "Version")
    expires = parse_field(text, "Expires")
    max_wakes_raw = parse_field(text, "Max wakes")
    wakes_used_raw = parse_field(text, "Wakes used")
    warnings: list[str] = []
    if status.upper() == "ACTIVE":
        warnings.append("recurring heartbeat active; v5 requires direct EVENT_READY callback")

    expiry = parse_datetime(expires)
    expired = bool(expiry and datetime.now(expiry.tzinfo) > expiry)
    if expired:
        warnings.append("heartbeat expired")

    try:
        max_wakes = int(re.search(r"\d+", max_wakes_raw or "").group(0)) if max_wakes_raw else None
    except AttributeError:
        max_wakes = None
    try:
        wakes_used = int(re.search(r"\d+", wakes_used_raw or "").group(0)) if wakes_used_raw else None
    except AttributeError:
        wakes_used = None
    over_wakes = bool(max_wakes is not None and wakes_used is not None and wakes_used >= max_wakes)
    if over_wakes:
        warnings.append("heartbeat max wakes reached")

    inactive = status.upper() not in {"ACTIVE", "OFF", "STOPPED", "EXPIRED"}
    if inactive:
        warnings.append("heartbeat status unrecognized")

    return {
        "exists": True,
        "status": status,
        "version": version,
        "expires": expires,
        "max_wakes": max_wakes,
        "wakes_used": wakes_used,
        "expired": expired,
        "over_wakes": over_wakes,
        "stale": expired or over_wakes or status.upper() == "EXPIRED",
        "warnings": warnings,
    }


def central_fact_state(manager: Path, branch: str, head: str) -> dict[str, Any]:
    facts_path = manager / "CENTRAL_FACTS.md"
    lock_path = manager / "MISSION_LOCK.md"
    warnings: list[str] = []

    facts_text = read_text(facts_path) if facts_path.is_file() else ""
    lock_text = read_text(lock_path) if lock_path.is_file() else ""
    facts_lines = [line for line in facts_text.splitlines() if line.strip()]
    lock_lines = [line for line in lock_text.splitlines() if line.strip()]

    if not facts_path.is_file():
        warnings.append("missing CENTRAL_FACTS.md")
    if not lock_path.is_file():
        warnings.append("missing MISSION_LOCK.md")
    if facts_lines and len(facts_lines) > 45:
        warnings.append("CENTRAL_FACTS.md exceeds compact line budget")

    manager_branch = parse_field(facts_text, "Manager-state branch")
    manager_head = parse_field(facts_text, "Manager-state HEAD")
    implementation_branch = parse_field(facts_text, "Implementation branch") or parse_field(facts_text, "Source branch")
    implementation_head = parse_field(facts_text, "Implementation HEAD") or parse_field(facts_text, "Current HEAD")
    deployment_branch = parse_field(facts_text, "Deployment branch") or parse_field(facts_text, "Deploy branch")
    deployment_head = parse_field(facts_text, "Deployment HEAD")
    lock_branch = parse_field(lock_text, "Implementation branch") or parse_field(lock_text, "Source branch")
    lock_head = parse_field(lock_text, "Target SHA")
    short = head[:12] if head else ""
    repo = manager.parent.parent

    def mismatches(value: str, current: str, current_short: str = "") -> bool:
        if not value or value.upper() in {"UNKNOWN", "NONE", "N/A", "NOT_USED", "NOT-USED"}:
            return False
        if value == current:
            return False
        if current_short and value == current_short:
            return False
        return True

    if branch and branch == manager_branch:
        if manager_head and head and mismatches(manager_head, head, short):
            warnings.append("CENTRAL_FACTS manager-state HEAD differs from current checkout")
    elif branch and branch == implementation_branch:
        if implementation_head and head and mismatches(implementation_head, head, short) and not is_attestation_head(repo, implementation_head, head):
            warnings.append("CENTRAL_FACTS implementation HEAD differs from current checkout")
    elif branch and branch == deployment_branch:
        if deployment_head and head and mismatches(deployment_head, head, short):
            warnings.append("CENTRAL_FACTS deployment HEAD differs from current checkout")
    elif branch and any((manager_branch, implementation_branch, deployment_branch)):
        warnings.append("current checkout branch is not a recorded X9 branch role")

    return {
        "central_facts": {
            "exists": facts_path.is_file(),
            "path": str(facts_path),
            "line_count": len(facts_lines),
            "active_lane": parse_field(facts_text, "Active lane"),
            "manager_state_branch": manager_branch,
            "manager_state_head": manager_head,
            "implementation_branch": implementation_branch,
            "implementation_head": implementation_head,
            "deployment_branch": deployment_branch,
            "deployment_head": deployment_head,
            "v105_role": parse_field(facts_text, "v105 role"),
            "current_head": manager_head,
            "must_reach": parse_field(facts_text, "Must reach"),
            "exact_next_action": parse_field(facts_text, "Exact next action"),
        },
        "mission_lock": {
            "exists": lock_path.is_file(),
            "path": str(lock_path),
            "line_count": len(lock_lines),
            "active_lane": parse_field(lock_text, "Active lane"),
            "implementation_branch": lock_branch,
            "deployment_branch": parse_field(lock_text, "Deployment branch") or parse_field(lock_text, "Deploy branch"),
            "v105_role": parse_field(lock_text, "v105 role"),
            "target_sha": lock_head,
            "must_reach": parse_field(lock_text, "Must reach"),
        },
        "warnings": warnings,
    }


def local_work_ledger_state(manager: Path, active_lane: str, head: str, dirty: dict[str, Any]) -> dict[str, Any]:
    path = manager / "LOCAL_WORK_LEDGER.md"
    warnings: list[str] = []
    if not path.is_file():
        if dirty.get("tracked_count", 0) or dirty.get("untracked_count", 0):
            warnings.append("LOCAL_WORK_LEDGER.md missing while checkout has local work")
        return {"exists": False, "path": str(path), "status": "missing", "warnings": warnings}

    text = read_text(path)
    ledger_status = parse_field(text, "Ledger status") or "UNKNOWN"
    ledger_lane = parse_field(text, "Active lane")
    ledger_head = (
        parse_field(text, "Checkout HEAD")
        or parse_field(text, "Manager-state HEAD")
        or parse_field(text, "Current HEAD")
    )
    active_local = parse_field(text, "Active-lane local work")
    line_count = len([line for line in text.splitlines() if line.strip()])
    short = head[:12] if head else ""

    if active_lane and ledger_lane and ledger_lane != active_lane:
        warnings.append("LOCAL_WORK_LEDGER active lane differs from CENTRAL_FACTS")
    repo = manager.parent.parent
    if head and ledger_head and ledger_head not in {head, short} and not is_attestation_head(repo, ledger_head, head):
        warnings.append("LOCAL_WORK_LEDGER current HEAD differs from git HEAD")
    if (dirty.get("tracked_count", 0) or dirty.get("untracked_count", 0)) and ledger_status.upper() == "PASS":
        warnings.append("LOCAL_WORK_LEDGER says PASS while checkout has local work")
    if active_local.upper() == "YES" and ledger_status.upper() == "PASS":
        warnings.append("LOCAL_WORK_LEDGER active-lane local work cannot be PASS")

    return {
        "exists": True,
        "path": str(path),
        "status": ledger_status,
        "active_lane": ledger_lane,
        "current_head": ledger_head,
        "active_lane_local_work": active_local,
        "line_count": line_count,
        "warnings": warnings,
    }


def active_state(repo: Path, branch: str, head: str) -> dict[str, Any]:
    path = repo / ".devad" / "ACTIVE.md"
    if not path.is_file():
        return {"exists": False, "status": "missing", "path": str(path)}
    text = read_text(path)
    short = head[:12] if head else ""
    branch_ok = bool(branch and branch in text)
    recorded_head = parse_field(text, "Implementation HEAD") or parse_field(text, "Current HEAD")
    head_ok = bool(
        head
        and (
            head in text
            or short in text
            or is_attestation_head(repo, recorded_head, head)
        )
    )
    status = "fresh" if branch_ok and head_ok else "stale"
    return {
        "exists": True,
        "status": status,
        "path": str(path),
        "branch_found": branch_ok,
        "head_found": head_ok,
    }


def manager_files(manager: Path) -> dict[str, Any]:
    required = {name: (manager / name).is_file() for name in REQUIRED_MANAGER_FILES}
    optional = {name: (manager / name).is_file() for name in OPTIONAL_MANAGER_FILES}
    workers_dir = manager / "workers"
    workers: list[dict[str, Any]] = []
    if workers_dir.is_dir():
        for lane in sorted(p for p in workers_dir.iterdir() if p.is_dir()):
            workers.append(
                {
                    "lane": lane.name,
                    "manifest": (lane / "MANIFEST.md").is_file(),
                    "task": (lane / "TASK.md").is_file(),
                    "ledger": (lane / "LEDGER.md").is_file(),
                    "handoffs": (lane / "HANDOFFS.md").is_file(),
                    "proof_dir": (lane / "proof").is_dir(),
                }
            )
    return {
        "exists": manager.is_dir(),
        "required": required,
        "optional": optional,
        "workers_dir": workers_dir.is_dir(),
        "workers": workers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Devad X9 manager truth state, read-only.")
    parser.add_argument("--repo", required=True, help="Path to the core-x9 repo")
    parser.add_argument("--remote", default="origin", help="Git remote to query")
    parser.add_argument("--source-branch", default="AI-1-migrate")
    parser.add_argument("--deploy-branch", default="<deployment-branch>")
    parser.add_argument("--max-files", type=int, default=30, help="Maximum changed/untracked files to print")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    result: dict[str, Any] = {
        "status": "UNKNOWN",
        "repo": str(repo),
        "errors": [],
        "warnings": [],
    }

    if not repo.exists():
        result["status"] = "BLOCKED"
        result["errors"].append(f"repo not found: {repo}")
        print(json.dumps(result, indent=2))
        return 2

    git_status = run_git(repo, ["status", "--short", "--branch"])
    head_res = run_git(repo, ["rev-parse", "HEAD"])
    branch_res = run_git(repo, ["branch", "--show-current"])
    upstream_res = run_git(repo, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    worktree_res = run_git(repo, ["worktree", "list"])
    remote_res = run_git(repo, ["remote", "-v"])

    branch = branch_res["stdout"].splitlines()[0] if branch_res["stdout"] else ""
    head = head_res["stdout"].splitlines()[0] if head_res["stdout"] else ""
    status_summary = parse_status(git_status["stdout"], args.max_files)
    manager = repo / ".devad" / "manager"

    central = central_fact_state(manager, branch, head)
    local_work = local_work_ledger_state(
        manager,
        central.get("central_facts", {}).get("active_lane", ""),
        head,
        status_summary,
    )

    result.update(
        {
            "git": {
                "branch": branch,
                "head": head,
                "upstream": upstream_res["stdout"] if upstream_res["returncode"] == 0 else "",
                "upstream_error": upstream_res["stderr"] if upstream_res["returncode"] != 0 else "",
                "status_header": git_status["stdout"].splitlines()[0] if git_status["stdout"] else "",
                "dirty": status_summary,
                "worktrees_top": worktree_res["stdout"].splitlines()[: args.max_files],
                "remote_v": remote_res["stdout"].splitlines()[: args.max_files],
            },
            "remote_refs": {
                "source": ls_remote(repo, args.remote, args.source_branch),
                "deploy": ls_remote(repo, args.remote, args.deploy_branch),
            },
            "active": active_state(repo, branch, head),
            "manager": manager_files(manager),
            "central_facts": central,
            "local_work": local_work,
            "heartbeat": heartbeat_state(manager / "HEARTBEAT.md"),
        }
    )

    if any(v["returncode"] != 0 for v in [git_status, head_res, branch_res]):
        result["errors"].append("one or more required git commands failed")

    if result["active"]["status"] == "stale":
        result["warnings"].append(".devad/ACTIVE.md does not match current branch/HEAD")
    if result["active"]["status"] == "missing":
        result["warnings"].append(".devad/ACTIVE.md missing")

    manager_info = result["manager"]
    if not manager_info["exists"]:
        result["warnings"].append("missing .devad/manager directory")
    else:
        for name, exists in manager_info["required"].items():
            if not exists:
                result["warnings"].append(f"missing manager file: {name}")
        if not manager_info["workers_dir"]:
            result["warnings"].append("missing .devad/manager/workers directory")

    for key in ("source", "deploy"):
        if result["remote_refs"][key]["status"] != "ok":
            result["warnings"].append(f"remote {key} SHA unavailable")

    for warning in result["heartbeat"].get("warnings", []):
        result["warnings"].append(warning)
    for warning in result["central_facts"].get("warnings", []):
        result["warnings"].append(warning)
    for warning in result["local_work"].get("warnings", []):
        result["warnings"].append(warning)
    if result["local_work"].get("exists") and result["local_work"].get("active_lane_local_work", "").upper() == "YES":
        result["warnings"].append("LOCAL_ONLY_WORK: active-lane local work exists")

    if result["errors"]:
        result["status"] = "BLOCKED"
    elif result["warnings"]:
        result["status"] = "PARTIAL"
    else:
        result["status"] = "PASS"

    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
