#!/usr/bin/env python3
"""Collect Devad X9 worker handoffs into a compact manager pickup queue."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FIELD_RE = re.compile(r"^\s*\*\*(.+?):\*\*\s*(.*?)\s*$")
ITEM_FIELD_RE = re.compile(r"^\s*[-*]\s*([^:]+):\s*(.*?)\s*$")
STATUS_RE = re.compile(
    r"\b(PLANNED|ACTIVE|CLAIMED_PASS|VERIFIED_PASS|PARTIAL|BLOCKED|FAILED|REJECTED|ABANDONED|UNVERIFIED|PASS)\b",
    re.I,
)
CURRENT_STATUS_RE = re.compile(r"(?m)^CURRENT_STATUS:\s*$")


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def extract_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            fields[key] = match.group(2).strip().strip("`")
            continue
        match = ITEM_FIELD_RE.match(line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            fields[key] = match.group(2).strip().strip("`")
    return fields


def extract_current_status(text: str) -> dict[str, str]:
    match = CURRENT_STATUS_RE.search(text)
    if not match:
        return {}
    block = text[match.end() :]
    lines: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or (not stripped and lines):
            break
        if ITEM_FIELD_RE.match(line):
            lines.append(line)
            continue
        if lines and stripped and not stripped.startswith(("-", "*")):
            break
    return extract_fields("\n".join(lines))


def infer_status(text: str, fields: dict[str, str]) -> str:
    status = fields.get("lane_status") or fields.get("status", "")
    match = STATUS_RE.search(status)
    if not match:
        return "MISSING_CURRENT_STATUS" if fields else "UNVERIFIED"
    value = match.group(1).upper()
    return "CLAIMED_PASS" if value == "PASS" else value


def norm(value: str) -> str:
    return value.strip().upper().replace(" ", "_").replace("-", "_")


def proof_count(packet: Path) -> int:
    proof = packet / "proof"
    if not proof.is_dir():
        return 0
    return sum(1 for p in proof.rglob("*") if p.is_file())


def packet_complete(packet: Path) -> bool:
    return all((packet / name).is_file() for name in ["MANIFEST.md", "STATUS.md", "TASK.md", "LEDGER.md", "HANDOFFS.md"])


def collect(repo: Path) -> list[dict[str, Any]]:
    workers = repo / ".devad" / "manager" / "workers"
    rows: list[dict[str, Any]] = []
    if not workers.is_dir():
        return rows

    for packet in sorted(p for p in workers.iterdir() if p.is_dir()):
        manifest_fields = extract_fields(read(packet / "MANIFEST.md"))
        status_file = packet / "STATUS.md"
        handoff = packet / "HANDOFFS.md"
        status_text = read(status_file)
        text = read(handoff)
        status_fields = extract_current_status(status_text)
        handoff_fields = extract_current_status(text)
        if status_fields:
            fields = status_fields
            status_source = str(status_file)
        elif handoff_fields:
            fields = handoff_fields
            status_source = str(handoff)
        else:
            fields = {}
            status_source = ""
        status = infer_status(status_text or text, fields) if fields else "MISSING_CURRENT_STATUS"
        if not handoff.is_file() and not status_file.is_file():
            status = "MISSING_HANDOFF"
        try:
            mtime_path = status_file if status_file.is_file() else handoff
            mtime = datetime.fromtimestamp(mtime_path.stat().st_mtime).isoformat(timespec="seconds")
        except OSError:
            mtime = ""
        rows.append(
            {
                "lane": packet.name,
                "packet": str(packet),
                "status_file": str(status_file),
                "status_file_exists": status_file.is_file(),
                "current_status_exists": bool(status_fields or handoff_fields),
                "status_source": status_source,
                "handoff": str(handoff),
                "handoff_exists": handoff.is_file(),
                "mtime": mtime,
                "status": status,
                "mission_lock": norm(fields.get("mission_lock", "")),
                "central_facts": norm(fields.get("central_facts", "")),
                "local_work": norm(fields.get("local_work", "")),
                "security_review": norm(fields.get("security_review", "")),
                "security_precommit": norm(fields.get("security_precommit", "")),
                "post_commit_docs": norm(fields.get("post_commit_docs", "")),
                "source_push": norm(fields.get("source_push", "")),
                "deploy_readiness": norm(fields.get("deploy_readiness", "")),
                "live_deploy": norm(fields.get("live_deploy", "")),
                "live_proof": norm(fields.get("live_proof", "")),
                "latest_commit": fields.get("latest_commit", ""),
                "attestation_commit": fields.get("attestation_commit", ""),
                "exact_next_action": fields.get("exact_next_action", ""),
                "must_not_do": fields.get("must_not_do", ""),
                "manager_action_requested": fields.get("manager_action_requested", "") or fields.get("exact_next_action", ""),
                "worktree": fields.get("worktree", "") or manifest_fields.get("worktree", ""),
                "branch": fields.get("branch", "") or manifest_fields.get("branch", ""),
                "head": fields.get("head", "") or fields.get("latest_commit", ""),
                "base_sha": fields.get("base_sha", ""),
                "summary": fields.get("summary", "") or fields.get("scope", ""),
                "packet_complete": packet_complete(packet),
                "proof_count": proof_count(packet),
                "packet_schema": norm(manifest_fields.get("packet_schema", "")),
                "feature_id": manifest_fields.get("feature_id", ""),
                "feature_root": manifest_fields.get("feature_root", ""),
                "run_id": manifest_fields.get("run_id", ""),
                "artifact_index": manifest_fields.get("artifact_index", ""),
            }
        )

    rows.sort(key=lambda row: row.get("mtime", ""), reverse=True)
    return rows


def write_index(repo: Path, rows: list[dict[str, Any]]) -> Path:
    manager = repo / ".devad" / "manager"
    manager.mkdir(parents=True, exist_ok=True)
    path = manager / "HANDOFF_INDEX.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Worker Handoff Index",
        "",
        f"**Updated:** {now} Europe/Istanbul",
        "",
        "| Lane | Feature | Status | Local | Security | Commit | Push | Deploy | Live | Next | Updated |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        head = (row.get("head") or "")[:12]
        lines.append(
            "| {lane} | {feature} | {status} | {local_work} | {security} | {commit} | {source_push} | {deploy_ready} | {live} | {action} | {mtime} |".format(
                lane=row.get("lane", ""),
                feature=row.get("feature_id", "") or "LEGACY",
                status=row.get("status", ""),
                local_work=row.get("local_work", ""),
                security=row.get("security_review", ""),
                commit=(row.get("latest_commit") or "NONE")[:12],
                source_push=row.get("source_push", ""),
                deploy_ready=row.get("deploy_readiness", ""),
                live=row.get("live_proof", "") or row.get("live_deploy", ""),
                action=row.get("manager_action_requested", ""),
                mtime=row.get("mtime", ""),
            )
        )
    if not rows:
        lines.append("| none | - | - | - | - | - | - | - | - | - | - |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def write_workers(repo: Path, rows: list[dict[str, Any]]) -> Path:
    manager = repo / ".devad" / "manager"
    manager.mkdir(parents=True, exist_ok=True)
    path = manager / "WORKERS.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Workers",
        "",
        f"**Updated:** {now} Europe/Istanbul",
        "",
        "Generated from Worker packets. Do not hand-edit this table.",
        "",
        "| Lane | Feature | Status | Packet | Worktree | Branch | Next |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {lane} | {feature} | {status} | {packet} | {worktree} | {branch} | {next} |".format(
                lane=row.get("lane", ""),
                feature=row.get("feature_id", "") or "LEGACY",
                status=row.get("status", ""),
                packet="complete" if row.get("packet_complete") else "incomplete",
                worktree=row.get("worktree", ""),
                branch=row.get("branch", ""),
                next=row.get("manager_action_requested", ""),
            )
        )
    if not rows:
        lines.append("| none | - | - | - | - | - | - |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect worker handoffs for Devad X9 manager pickup.")
    parser.add_argument("--repo", required=True, help="Path to core-x9 repo")
    parser.add_argument("--write-index", action="store_true", help="Write .devad/manager/HANDOFF_INDEX.md")
    parser.add_argument("--write-workers", action="store_true", help="Write .devad/manager/WORKERS.md")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    result: dict[str, Any] = {
        "status": "UNKNOWN",
        "repo": str(repo),
        "handoffs": [],
        "warnings": [],
        "errors": [],
    }

    if not repo.is_dir():
        result["status"] = "BLOCKED"
        result["errors"].append(f"repo not found: {repo}")
        print(json.dumps(result, indent=2))
        return 2

    rows = collect(repo)
    result["handoffs"] = rows
    if not rows:
        result["warnings"].append("no worker handoffs found")
    for row in rows:
        if not row["status_file_exists"]:
            result["warnings"].append(f"{row['lane']}: missing STATUS.md")
        if not row["current_status_exists"]:
            result["warnings"].append(f"{row['lane']}: missing CURRENT_STATUS block")
        if row["current_status_exists"] and not row["mission_lock"]:
            result["warnings"].append(f"{row['lane']}: missing Mission lock status")
        if row["current_status_exists"] and not row["central_facts"]:
            result["warnings"].append(f"{row['lane']}: missing Central facts status")
        if row["current_status_exists"] and not row["local_work"]:
            result["warnings"].append(f"{row['lane']}: missing Local work status")
        if not row["handoff_exists"]:
            result["warnings"].append(f"{row['lane']}: missing HANDOFFS.md")
        if not row["packet_complete"]:
            result["warnings"].append(f"{row['lane']}: incomplete worker packet")
        if row["packet_schema"] == "X9_V2":
            for field in ("feature_id", "feature_root", "run_id", "artifact_index"):
                if not row.get(field):
                    result["warnings"].append(f"{row['lane']}: X9-V2 packet missing {field}")
        if row["status"] in {"CLAIMED_PASS", "VERIFIED_PASS"} and row["proof_count"] == 0:
            result["warnings"].append(f"{row['lane']}: pass-style status without proof files")
        if row["deploy_readiness"] == "PASS" and row["latest_commit"] == "":
            result["warnings"].append(f"{row['lane']}: deploy readiness PASS without latest commit")
        if row["live_deploy"] == "PASS" and row["deploy_readiness"] != "PASS":
            result["warnings"].append(f"{row['lane']}: live deploy PASS without deploy readiness PASS")
        if row["source_push"] == "PASS" and row["local_work"] != "PASS":
            result["warnings"].append(f"{row['lane']}: source push PASS without Local work PASS")
        if row["deploy_readiness"] == "PASS" and row["local_work"] != "PASS":
            result["warnings"].append(f"{row['lane']}: deploy readiness PASS without Local work PASS")
        latest_commit = (row.get("latest_commit") or "").strip().lower()
        has_real_commit = latest_commit not in {"", "none", "n/a", "not_committed", "not committed"}
        if has_real_commit and row["security_precommit"] not in {"PASS", "NOT_REQUIRED"}:
            result["warnings"].append(f"{row['lane']}: latest commit without security precommit PASS")
        if has_real_commit and row["post_commit_docs"] != "PASS":
            result["warnings"].append(f"{row['lane']}: latest commit without post-commit docs PASS")

    if args.write_index:
        result["index_path"] = str(write_index(repo, rows))
    if args.write_workers:
        result["workers_path"] = str(write_workers(repo, rows))

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
