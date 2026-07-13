#!/usr/bin/env python3
"""Build the Devad X9 local-only work ledger."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ITEM_FIELD_RE = re.compile(r"^\s*[-*]\s*([^:]+):\s*(.*?)\s*$")


def run_git(repo: Path, args: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"returncode": 127, "stdout": "", "stderr": "git not found"}
    except subprocess.TimeoutExpired:
        return {"returncode": 124, "stdout": "", "stderr": "git command timed out"}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_field(text: str, field: str) -> str:
    patterns = [
        rf"^\s*[-*]\s*{re.escape(field)}:\s*(.+?)\s*$",
        rf"^\s*{re.escape(field)}:\s*(.+?)\s*$",
        rf"^\s*\*\*{re.escape(field)}:\*\*\s*(.+?)\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.M)
        if match:
            return match.group(1).strip().strip("`")
    return ""


def parse_status(stdout: str) -> dict[str, Any]:
    header = ""
    tracked: list[str] = []
    untracked: list[str] = []
    for line in stdout.splitlines():
        if line.startswith("##"):
            header = line
            continue
        if not line:
            continue
        path = line[3:].strip() if len(line) >= 4 else line.strip()
        if " -> " in path:
            path = path.split(" -> ")[-1]
        path = path.strip('"').replace("\\", "/")
        if line.startswith("??"):
            untracked.append(path)
        else:
            tracked.append(path)
    return {"header": header, "tracked": tracked, "untracked": untracked}


def current_status_fields(path: Path) -> dict[str, str]:
    text = read(path)
    match = re.search(r"(?m)^CURRENT_STATUS:\s*$", text)
    if not match:
        return {}
    block = text[match.end() :]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or (not stripped and fields):
            break
        field = ITEM_FIELD_RE.match(line)
        if field:
            key = field.group(1).strip()
            fields[key] = field.group(2).strip().strip("`")
        elif fields and stripped and not stripped.startswith(("-", "*")):
            break
    return fields


def classify_path(path: str, active_lane: str) -> dict[str, str]:
    normalized = path.replace("\\", "/")
    if active_lane and normalized.startswith(f".devad/manager/workers/{active_lane}/"):
        return {"lane": active_lane, "bucket": "ACTIVE_LANE_DOCS", "action": "classify_with_lane"}
    if normalized.startswith(".devad/docs/"):
        return {"lane": "docs", "bucket": "COMMIT_DOCS", "action": "commit_exact_if_related"}
    if normalized.startswith(".devad/manager/"):
        return {"lane": "manager", "bucket": "MANAGER_STATE", "action": "commit_exact_if_related"}
    if normalized.startswith(".devad/"):
        return {"lane": "devad", "bucket": "DEVAD_REFERENCE", "action": "inventory_only_until_related"}
    if normalized.startswith("services/"):
        return {"lane": "sidecar", "bucket": "SIDECAR_SOURCE", "action": "separate_gate_no_pycache"}
    if normalized.startswith(("app/", "resources/", "routes/", "config/", "database/", "tests/", "composer.json", "package.json", "pnpm-lock.yaml")):
        return {"lane": active_lane or "app", "bucket": "APP_RUNTIME", "action": "review_exact_hunk"}
    return {"lane": "unknown", "bucket": "OTHER", "action": "classify_before_stage"}


def state_for(path: str, tracked: bool) -> str:
    if tracked:
        return "UNCOMMITTED"
    if path.startswith(".devad/"):
        return "PLANNED_ONLY"
    return "UNCOMMITTED"


def build(repo: Path, max_files: int) -> dict[str, Any]:
    manager = repo / ".devad" / "manager"
    facts = read(manager / "CENTRAL_FACTS.md")
    mission = read(manager / "MISSION_LOCK.md")
    lost_audit = manager / "LOST_CHANGE_AUDIT-2026-07-05.md"

    active_lane = parse_field(facts, "Active lane") or parse_field(mission, "Active lane")
    manager_state_branch = parse_field(facts, "Manager-state branch")
    manager_state_head = parse_field(facts, "Manager-state HEAD")
    implementation_branch = (
        parse_field(facts, "Implementation branch")
        or parse_field(mission, "Implementation branch")
        or parse_field(facts, "Source branch")
        or parse_field(mission, "Source branch")
    )
    implementation_head = parse_field(facts, "Implementation HEAD")
    deployment_branch = (
        parse_field(facts, "Deployment branch")
        or parse_field(mission, "Deployment branch")
        or parse_field(facts, "Deploy branch")
        or parse_field(mission, "Deploy branch")
    )
    deployment_head = parse_field(facts, "Deployment HEAD")
    target_sha = parse_field(facts, "Target v105 SHA") or parse_field(mission, "Target SHA")

    git_status = run_git(repo, ["status", "--short", "--branch"])
    branch = run_git(repo, ["branch", "--show-current"])["stdout"].splitlines()
    head = run_git(repo, ["rev-parse", "HEAD"])["stdout"].splitlines()
    status = parse_status(git_status["stdout"])
    current_branch = branch[0] if branch else ""
    current_head = head[0] if head else ""
    if current_branch and current_branch == manager_state_branch:
        checkout_role = "MANAGER_STATE"
    elif current_branch and current_branch == implementation_branch:
        checkout_role = "IMPLEMENTATION"
    elif current_branch and current_branch == deployment_branch:
        checkout_role = "DEPLOYMENT"
    else:
        checkout_role = "OTHER"

    rows: list[dict[str, str]] = []
    for tracked, files in ((True, status["tracked"]), (False, status["untracked"])):
        for path in files:
            info = classify_path(path, active_lane)
            rows.append(
                {
                    "path": path,
                    "git": "tracked_dirty" if tracked else "untracked",
                    "release_state": state_for(path, tracked),
                    **info,
                }
            )

    active_rows = [row for row in rows if row["lane"] == active_lane or row["bucket"] in {"APP_RUNTIME", "ACTIVE_LANE_DOCS"}]
    ledger_status = "PASS" if not rows else "PARTIAL"
    if any(row["bucket"] == "OTHER" for row in rows):
        ledger_status = "PARTIAL"
    if not git_status["stdout"] and git_status["returncode"] != 0:
        ledger_status = "BLOCKED"

    status_path = manager / "workers" / active_lane / "STATUS.md" if active_lane else Path()
    handoff_path = manager / "workers" / active_lane / "HANDOFFS.md" if active_lane else Path()
    worker_status = current_status_fields(status_path) if status_path else {}
    worker_handoff = current_status_fields(handoff_path) if handoff_path else {}

    return {
        "status": ledger_status,
        "repo": str(repo),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "active_lane": active_lane,
        "implementation_branch": implementation_branch,
        "implementation_head": implementation_head,
        "deployment_branch": deployment_branch,
        "deployment_head": deployment_head,
        "target_sha": target_sha,
        "current_branch": current_branch,
        "current_head": current_head,
        "checkout_role": checkout_role,
        "manager_state_branch": manager_state_branch,
        "manager_state_head": manager_state_head,
        "git_status_header": status["header"],
        "tracked_count": len(status["tracked"]),
        "untracked_count": len(status["untracked"]),
        "active_local_count": len(active_rows),
        "rows": rows,
        "top_rows": rows[:max_files],
        "active_top_rows": active_rows[:max_files],
        "worker_status": worker_status,
        "worker_handoff": worker_handoff,
        "lost_audit": str(lost_audit) if lost_audit.is_file() else "",
        "git_error": git_status["stderr"] if git_status["returncode"] != 0 else "",
    }


def markdown(data: dict[str, Any]) -> str:
    now = data["updated"]
    status = data["status"]
    active_lane = data["active_lane"] or "UNKNOWN"
    head = data["current_head"]
    short_head = head[:12] if head else "UNKNOWN"
    local_flag = "YES" if data["active_local_count"] else "NO"

    lines = [
        "# Local Work Ledger",
        "",
        f"Updated: {now} Europe/Istanbul",
        "",
        "CURRENT_LOCAL_WORK:",
        f"- Ledger status: {status}",
        f"- Active lane: {active_lane}",
        f"- Repo root: {data['repo']}",
        f"- Checkout role: {data['checkout_role']}",
        f"- Checkout branch: {data['current_branch'] or 'UNKNOWN'}",
        f"- Checkout HEAD: {head or 'UNKNOWN'}",
        f"- Manager-state branch: {data['manager_state_branch'] or 'UNKNOWN'}",
        f"- Manager-state HEAD: {data['manager_state_head'] or 'UNKNOWN'}",
        f"- Implementation branch: {data['implementation_branch'] or 'UNKNOWN'}",
        f"- Implementation HEAD: {data['implementation_head'] or 'UNKNOWN'}",
        f"- Deployment branch: {data['deployment_branch'] or 'UNKNOWN'}",
        f"- Deployment HEAD: {data['deployment_head'] or 'UNKNOWN'}",
        f"- Target SHA: {data['target_sha'] or 'UNKNOWN'}",
        f"- Tracked dirty files: {data['tracked_count']}",
        f"- Untracked files: {data['untracked_count']}",
        f"- Active-lane local work: {local_flag}",
        "- Exact next check: classify local work before source push, v105 bridge, deploy, or done claim",
        "",
        "## Release States",
        "",
        "| State | Meaning | Manager rule |",
        "| --- | --- | --- |",
        "| `PLANNED_ONLY` | Docs/plans/proof exist but not code-live. | Do not count as shipped. |",
        "| `UNCOMMITTED` | Local dirty or untracked implementation/docs exist. | Classify before push/deploy. |",
        "| `SOURCE_ONLY` | Source branch has it, live branch may not. | Bridge/deploy proof needed. |",
        "| `V105_READY` | Exact v105 branch has intended SHA. | Deploy gate still required. |",
        "| `DEPLOYED` | Dokploy/live target has exact SHA. | Browser/live proof still required. |",
        "| `LIVE_PROOF_PASS` | Live proof passed for exact SHA. | Only that SHA/scope is done. |",
        "",
        "## Current Local Summary",
        "",
        "| Bucket | Count | Status |",
        "| --- | ---: | --- |",
        f"| Tracked dirty | {data['tracked_count']} | {'UNCOMMITTED' if data['tracked_count'] else 'none'} |",
        f"| Untracked | {data['untracked_count']} | {'LOCAL_ONLY' if data['untracked_count'] else 'none'} |",
        f"| Active-lane local | {data['active_local_count']} | {'CLASSIFY_BEFORE_NEXT' if data['active_local_count'] else 'none'} |",
        "",
    ]

    if data["lost_audit"]:
        lines.extend(
            [
                "## Seed Evidence",
                "",
                f"- Lost change audit: `{data['lost_audit']}`",
                "- Git status: current run from this ledger build.",
                "- Worker status/handoff: active lane current files when present.",
                "",
            ]
        )

    lines.extend(
        [
            "## Active-Lane Local Work",
            "",
            "| Path | Git | Release state | Bucket | Action |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if data["active_top_rows"]:
        for row in data["active_top_rows"]:
            lines.append(
                f"| `{row['path']}` | {row['git']} | {row['release_state']} | {row['bucket']} | {row['action']} |"
            )
    else:
        lines.append("| none | - | - | - | - |")

    lines.extend(
        [
            "",
            "## Top Local Work",
            "",
            "| Path | Git | Release state | Bucket | Action |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if data["top_rows"]:
        for row in data["top_rows"]:
            lines.append(
                f"| `{row['path']}` | {row['git']} | {row['release_state']} | {row['bucket']} | {row['action']} |"
            )
    else:
        lines.append("| none | - | - | - | - |")

    lines.extend(
        [
            "",
            "## Manager Gate",
            "",
            "- `Local work: PASS` only when active-lane local work is absent or deliberately classified.",
            "- `Local work: PARTIAL` when useful local work exists but is not fully committed/pushed/deployed/proofed.",
            "- `Local work: BLOCKED` when classification cannot be done safely.",
            "- GitHub/remote is not complete truth while this ledger shows active-lane local work.",
            "- No broad stage. No delete. No cleanup. Stage exact files only after classification.",
            "",
            "## Worker Snapshot",
            "",
            f"- Worker status file Local work: {data['worker_status'].get('Local work', 'MISSING')}",
            f"- Worker handoff Local work: {data['worker_handoff'].get('Local work', 'MISSING')}",
            f"- Source HEAD short: `{short_head}`",
        ]
    )

    if data["git_error"]:
        lines.extend(["", f"Git error: `{data['git_error']}`"])

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build .devad/manager/LOCAL_WORK_LEDGER.md.")
    parser.add_argument("--repo", required=True, help="Path to core-x9 repo")
    parser.add_argument("--write", action="store_true", help="Write LOCAL_WORK_LEDGER.md")
    parser.add_argument("--max-files", type=int, default=80)
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        result = {"status": "BLOCKED", "error": f"repo not found: {repo}"}
        print(json.dumps(result, indent=2))
        return 2

    data = build(repo, args.max_files)
    if args.write:
        path = repo / ".devad" / "manager" / "LOCAL_WORK_LEDGER.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown(data), encoding="utf-8", newline="\n")
        data["path"] = str(path)

    print(json.dumps({k: v for k, v in data.items() if k not in {"rows", "top_rows", "active_top_rows"}}, indent=2))
    return 1 if data["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
