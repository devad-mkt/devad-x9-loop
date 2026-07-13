#!/usr/bin/env python3
"""Validate a Devad X9 worker packet, read-only."""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from pathlib import Path
from typing import Any

REQUIRED = ["MANIFEST.md", "STATUS.md", "TASK.md", "LEDGER.md", "HANDOFFS.md"]
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".ps1", ".py", ".php", ".ts", ".tsx"}
PROOF_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".json", ".html", ".txt", ".md", ".log"}
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b"),
    re.compile(
        r"\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|password|oauth[_-]?code)\b\s*(?:=|:|=>)\s*['\"]?(?!REDACTED|redacted|xxxxx|placeholder|null|none)[A-Za-z0-9_./+=:-]{8,}",
        re.I,
    ),
]
PASS_RE = re.compile(r"\b(PASS|DONE|COMPLETE|COMPLETED|READY TO MERGE|PRODUCTION PARITY|VERIFIED_PASS|CLAIMED_PASS)\b", re.I)
STATUS_RE = re.compile(r"\b(PASS|PARTIAL|BLOCKED|CLAIMED_PASS|VERIFIED_PASS|FAILED|REJECTED|UNVERIFIED)\b", re.I)
CURRENT_STATUS_RE = re.compile(r"(?m)^CURRENT_STATUS:\s*$")
ITEM_FIELD_RE = re.compile(r"^\s*[-*]\s*([^:]+):\s*(.*?)\s*$")
BOLD_FIELD_RE = re.compile(r"^\s*\*\*(.+?):\*\*\s*(.*?)\s*$")
OUTBOUND_RE = re.compile(
    r"\b(SSRF|DNS rebinding|server-side URL|outbound fetch|scrap(?:e|ing|er)|crawler|webhook|RSS|YouTube import|fetch URL|URL ingestion|n8n callback|provider fetch)\b",
    re.I,
)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def iter_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def run_git(worktree: Path, args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(worktree), *args],
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


def parse_section(text: str, title: str) -> list[str]:
    lines = text.splitlines()
    found = False
    values: list[str] = []
    heading = re.compile(r"^#{1,6}\s+(.+?)\s*$")
    for line in lines:
        match = heading.match(line)
        if match:
            current = match.group(1).strip().lower()
            if found and current != title.lower():
                break
            found = current == title.lower()
            continue
        if not found:
            continue
        item = line.strip()
        if not item.startswith(("-", "*")):
            continue
        item = item.lstrip("-* ").strip().strip("`").strip()
        if item and not item.lower().startswith(("none", "n/a")):
            values.append(item.replace("\\", "/"))
    return values


def extract_current_status(text: str) -> tuple[dict[str, str], int]:
    match = CURRENT_STATUS_RE.search(text)
    if not match:
        return {}, 0
    line_number = text[: match.start()].count("\n") + 1
    block = text[match.end() :]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or (not stripped and fields):
            break
        field = ITEM_FIELD_RE.match(line)
        if field:
            key = field.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            fields[key] = field.group(2).strip().strip("`")
            continue
        if fields and stripped and not stripped.startswith(("-", "*")):
            break
    return fields, line_number


def extract_manifest_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = BOLD_FIELD_RE.match(line) or ITEM_FIELD_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
        fields[key] = match.group(2).strip().strip("`")
    return fields


def norm(value: str) -> str:
    return value.strip().upper().replace(" ", "_").replace("-", "_")


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path
    return None


def path_matches(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        p = pattern.strip().strip("`").replace("\\", "/")
        if not p:
            continue
        if p.endswith("/**") and normalized.startswith(p[:-3].rstrip("/") + "/"):
            return True
        if p.endswith("/") and normalized.startswith(p):
            return True
        if fnmatch.fnmatch(normalized, p):
            return True
        if normalized == p or normalized.startswith(p.rstrip("/") + "/"):
            return True
    return False


def changed_files(worktree: Path, base_sha: str, max_files: int) -> dict[str, Any]:
    files: set[str] = set()
    if base_sha:
        res = run_git(worktree, ["diff", "--name-only", f"{base_sha}...HEAD"])
        if res["returncode"] == 0:
            files.update(line.replace("\\", "/") for line in res["stdout"].splitlines() if line.strip())
    status = run_git(worktree, ["status", "--porcelain"])
    for line in status["stdout"].splitlines():
        if len(line) >= 4:
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ")[-1]
            files.add(path.replace("\\", "/"))
    return {
        "files": sorted(files),
        "top": sorted(files)[:max_files],
        "count": len(files),
        "status_returncode": status["returncode"],
        "status_error": status["stderr"],
    }


def infer_repo_root(packet_root: Path) -> Path | None:
    """Infer repo root from .devad/manager/workers/<lane>."""
    parts = [part.lower() for part in packet_root.parts]
    if ".devad" not in parts:
        return None
    idx = parts.index(".devad")
    if idx == 0:
        return None
    return Path(*packet_root.parts[:idx])


def find_commit_doc(repo_root: Path | None, sha: str) -> dict[str, Any]:
    if not repo_root or not sha:
        return {"found": False, "path": "", "reason": "missing repo root or sha"}
    docs = repo_root / ".devad" / "docs"
    if not docs.is_dir():
        return {"found": False, "path": str(docs), "reason": ".devad/docs missing"}

    short = sha[:8]
    candidates = [p for p in docs.rglob("*.md") if short.lower() in p.name.lower()]
    if not candidates:
        candidates = list(docs.rglob("*.md"))

    for path in candidates:
        text = read(path)
        if sha in text or short in text:
            return {"found": True, "path": str(path), "reason": ""}
    return {"found": False, "path": str(docs), "reason": f"no commit doc mentions {sha}"}


def extract_base_sha(text: str) -> str:
    for pattern in (r"\*\*Base SHA:\*\*\s*`?([0-9a-f]{7,40})", r"Base SHA:\s*`?([0-9a-f]{7,40})"):
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Devad X9 worker packet.")
    parser.add_argument("--packet", required=True, help="Path to .devad/manager/workers/<lane>")
    parser.add_argument("--worktree", help="Optional worker worktree to validate against the packet")
    parser.add_argument("--max-files", type=int, default=50)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero unless PASS")
    args = parser.parse_args()

    root = Path(args.packet).expanduser().resolve()
    result: dict[str, Any] = {
        "status": "UNKNOWN",
        "packet": str(root),
        "errors": [],
        "warnings": [],
        "summary": {},
    }

    if not root.is_dir():
        result["status"] = "BLOCKED"
        result["errors"].append(f"packet folder not found: {root}")
        print(json.dumps(result, indent=2))
        return 2

    files = iter_files(root)
    text_files = [p for p in files if p.suffix.lower() in TEXT_EXTENSIONS]
    proof_files = [p for p in files if "proof" in [part.lower() for part in p.parts] and p.suffix.lower() in PROOF_EXTENSIONS]

    for name in REQUIRED:
        if not (root / name).is_file():
            result["errors"].append(f"missing required file: {name}")

    manifest = read(root / "MANIFEST.md")
    status_doc = read(root / "STATUS.md")
    task = read(root / "TASK.md")
    handoffs = read(root / "HANDOFFS.md")
    combined_packet = "\n".join([manifest, status_doc, task])
    combined_all = "\n".join(read(p) for p in text_files)
    status_fields, status_line = extract_current_status(status_doc)
    handoff_status_fields, handoff_status_line = extract_current_status(handoffs)
    manifest_fields = extract_manifest_fields(manifest)
    packet_schema = norm(manifest_fields.get("packet_schema", ""))

    allowed = parse_section(combined_packet, "Allowed Files")
    forbidden = parse_section(combined_packet, "Forbidden Files")
    stop_conditions = parse_section(combined_packet, "Stop Conditions")
    proof_required = "Proof Required" in combined_packet or "## Proof" in combined_packet

    if not allowed:
        result["warnings"].append("missing or empty Allowed Files section")
    if not forbidden:
        result["warnings"].append("missing or empty Forbidden Files section")
    if not stop_conditions:
        result["warnings"].append("missing or empty Stop Conditions section")
    if not proof_required:
        result["warnings"].append("missing Proof Required section")

    if not status_fields:
        result["errors"].append("STATUS.md lacks CURRENT_STATUS block")
    if status_line > 8:
        result["errors"].append("STATUS.md CURRENT_STATUS is not at the top")
    if not handoff_status_fields:
        result["errors"].append("HANDOFFS.md lacks top CURRENT_STATUS block")
    if handoff_status_line > 8:
        result["errors"].append("HANDOFFS.md CURRENT_STATUS is not at the top")

    lane_status = norm(status_fields.get("lane_status") or status_fields.get("status", ""))
    security_review = norm(status_fields.get("security_review", ""))
    security_precommit = norm(status_fields.get("security_precommit", ""))
    post_commit_docs = norm(status_fields.get("post_commit_docs", ""))
    source_push = norm(status_fields.get("source_push", ""))
    deploy_readiness = norm(status_fields.get("deploy_readiness", ""))
    live_deploy = norm(status_fields.get("live_deploy", ""))
    live_proof = norm(status_fields.get("live_proof", ""))
    latest_commit = status_fields.get("latest_commit", "").strip()
    attestation_commit = status_fields.get("attestation_commit", "").strip()
    if latest_commit.lower() in {"none", "n/a", "unknown", "<sha or none>"}:
        latest_commit = ""
    if attestation_commit.lower() in {"none", "n/a", "unknown", "<sha or none>"}:
        attestation_commit = ""
    inferred_repo = infer_repo_root(root)

    if packet_schema == "X9_V2":
        for field in ("feature_id", "feature_root", "run_id", "artifact_index"):
            if not manifest_fields.get(field):
                result["errors"].append(f"X9-V2 MANIFEST lacks {field.replace('_', ' ').title()}")
        if inferred_repo and manifest_fields.get("feature_root"):
            feature_root = inferred_repo / manifest_fields["feature_root"]
            if not (feature_root / "FEATURE.json").is_file():
                result["errors"].append("X9-V2 Feature root lacks FEATURE.json")
        if inferred_repo and manifest_fields.get("artifact_index"):
            if not (inferred_repo / manifest_fields["artifact_index"]).is_file():
                result["errors"].append("X9-V2 Artifact index does not exist")

    if status_fields and not lane_status:
        result["errors"].append("CURRENT_STATUS lacks Lane status")
    if status_fields and "mission_lock" not in status_fields:
        result["errors"].append("CURRENT_STATUS lacks Mission lock")
    if status_fields and "central_facts" not in status_fields:
        result["errors"].append("CURRENT_STATUS lacks Central facts")
    if status_fields and "local_work" not in status_fields:
        result["errors"].append("CURRENT_STATUS lacks Local work")
    if status_fields and "security_precommit" not in status_fields:
        result["errors"].append("CURRENT_STATUS lacks Security precommit")
    if status_fields and "post_commit_docs" not in status_fields:
        result["errors"].append("CURRENT_STATUS lacks Post-commit docs")
    central_facts_status = norm(status_fields.get("central_facts", ""))
    mission_lock_status = norm(status_fields.get("mission_lock", ""))
    if central_facts_status == "PASS" and inferred_repo and not (inferred_repo / ".devad" / "manager" / "CENTRAL_FACTS.md").is_file():
        result["errors"].append("Central facts PASS requires .devad/manager/CENTRAL_FACTS.md")
    if mission_lock_status == "PASS" and inferred_repo and not (inferred_repo / ".devad" / "manager" / "MISSION_LOCK.md").is_file():
        result["errors"].append("Mission lock PASS requires .devad/manager/MISSION_LOCK.md")
    local_work_status = norm(status_fields.get("local_work", ""))
    local_work_path = inferred_repo / ".devad" / "manager" / "LOCAL_WORK_LEDGER.md" if inferred_repo else None
    if status_fields and local_work_status not in {"PASS", "PARTIAL", "BLOCKED"}:
        result["errors"].append("CURRENT_STATUS Local work must be PASS, PARTIAL, or BLOCKED")
    if local_work_status == "PASS" and local_work_path and not local_work_path.is_file():
        result["errors"].append("Local work PASS requires .devad/manager/LOCAL_WORK_LEDGER.md")
    if local_work_status == "PASS" and ".devad/manager/LOCAL_WORK_LEDGER.md" not in combined_all.replace("\\", "/"):
        result["warnings"].append("Local work PASS should cite .devad/manager/LOCAL_WORK_LEDGER.md")
    if handoff_status_fields and status_fields:
        for key in (
            "lane_status",
            "mission_lock",
            "central_facts",
            "local_work",
            "security_review",
            "security_precommit",
            "post_commit_docs",
            "source_push",
            "deploy_readiness",
            "live_deploy",
            "live_proof",
            "latest_commit",
            "attestation_commit",
        ):
            left = norm(status_fields.get(key, ""))
            right = norm(handoff_status_fields.get(key, ""))
            if left and right and left != right:
                result["errors"].append(f"STATUS.md and HANDOFFS.md disagree on {key}")

    commit_doc_claimed = bool(latest_commit)
    if post_commit_docs == "PASS" and not latest_commit:
        result["errors"].append("Post-commit docs PASS requires Latest commit")
    if packet_schema == "X9_V2" and post_commit_docs == "PASS" and not attestation_commit:
        result["errors"].append("X9-V2 Post-commit docs PASS requires Attestation commit")
    if commit_doc_claimed and security_precommit not in {"PASS", "NOT_REQUIRED"}:
        result["errors"].append("Latest commit requires Security precommit PASS or NOT_REQUIRED")
    if commit_doc_claimed and post_commit_docs != "PASS":
        result["errors"].append("Latest commit requires Post-commit docs PASS")
    if post_commit_docs == "PASS" and ".devad/docs" not in combined_all.replace("\\", "/"):
        result["errors"].append("Post-commit docs PASS requires a .devad/docs path in packet evidence")
    commit_doc_result: dict[str, Any] = {"found": False, "path": "", "reason": "not checked"}
    if commit_doc_claimed and post_commit_docs == "PASS":
        repo_for_docs = Path(args.worktree).expanduser().resolve() if args.worktree else inferred_repo
        commit_doc_result = find_commit_doc(repo_for_docs, latest_commit)
        if not commit_doc_result["found"]:
            result["errors"].append(f"Post-commit docs PASS requires real .devad/docs commit record: {commit_doc_result['reason']}")

    if source_push == "PASS" and not latest_commit:
        result["errors"].append("Source push PASS requires Latest commit")
    if source_push == "PASS" and local_work_status != "PASS":
        result["errors"].append("Source push PASS requires Local work PASS")
    if deploy_readiness == "PASS" and source_push != "PASS":
        result["errors"].append("Deploy readiness PASS requires Source push PASS")
    if deploy_readiness == "PASS" and local_work_status != "PASS":
        result["errors"].append("Deploy readiness PASS requires Local work PASS")
    if deploy_readiness == "PASS" and security_review not in {"PASS", "NOT_REQUIRED"}:
        result["errors"].append("Deploy readiness PASS requires Security review PASS or NOT_REQUIRED")
    if live_deploy == "PASS" and deploy_readiness != "PASS":
        result["errors"].append("Live deploy PASS requires Deploy readiness PASS")

    deploy_gate = first_existing([root / "DEPLOY_GATE.md", root.parent.parent / "DEPLOY_GATE.md"])
    deploy_claimed = deploy_readiness in {"PASS", "WAIVED_BY_OWNER"} or live_deploy == "PASS"
    if deploy_claimed and deploy_gate is None:
        result["errors"].append("deploy/live claim requires DEPLOY_GATE.md")
    if deploy_claimed and deploy_gate is not None:
        gate_text = read(deploy_gate)
        if not latest_commit:
            result["errors"].append("deploy/live claim requires Latest commit")
        if latest_commit and f"DEPLOY_APPROVED:{latest_commit}" not in gate_text:
            result["errors"].append("DEPLOY_GATE.md lacks DEPLOY_APPROVED for Latest commit")
        if "Security review for exact commit range | PASS" not in gate_text and security_review != "NOT_REQUIRED":
            result["errors"].append("DEPLOY_GATE.md lacks security PASS")
        if "Dokploy branch policy verified | PASS" not in gate_text and deploy_readiness == "PASS":
            result["errors"].append("DEPLOY_GATE.md lacks Dokploy branch policy PASS")

    outbound_claimed = bool(OUTBOUND_RE.search(combined_all))
    if outbound_claimed and security_review != "PASS":
        result["errors"].append("outbound fetch/URL-style work requires Security review PASS")

    for path in text_files:
        for idx, line in enumerate(read(path).splitlines(), 1):
            for pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    result["errors"].append(f"{rel(path, root)}:{idx}: secret-like string")
                    break

    pass_claims: list[str] = []
    for path in text_files:
        for idx, line in enumerate(read(path).splitlines(), 1):
            if PASS_RE.search(line):
                pass_claims.append(f"{rel(path, root)}:{idx}")

    has_browser_proof = any(
        token in p.name.lower()
        for p in proof_files
        for token in ("screenshot", "dom", "aria", "browser", "console", "playwright")
    )
    has_test_proof = any(token in p.name.lower() for p in proof_files for token in ("test", "pest", "phpunit", "dusk", "proof", "log"))
    ui_claimed = bool(re.search(r"\b(ui|browser|screenshot|dom|inertia|react|page|route|tab|modal)\b", combined_packet + handoffs, re.I))

    if pass_claims and not proof_files:
        result["errors"].append("PASS/DONE-style claim exists but proof/ contains no files")
    elif pass_claims and not (has_browser_proof or has_test_proof):
        result["warnings"].append("PASS/DONE-style claim exists but proof files do not look like browser/test proof")
    if ui_claimed and pass_claims and not has_browser_proof:
        result["warnings"].append("UI/browser claim has PASS-style wording but no browser-like proof file")
    if not lane_status and "Status" not in handoffs and not STATUS_RE.search(handoffs):
        result["warnings"].append("HANDOFFS.md lacks explicit status")

    worktree_summary: dict[str, Any] = {}
    if args.worktree:
        worktree = Path(args.worktree).expanduser().resolve()
        if not worktree.is_dir():
            result["errors"].append(f"worktree not found: {worktree}")
        else:
            base_sha = extract_base_sha(manifest + "\n" + handoffs)
            changed = changed_files(worktree, base_sha, args.max_files)
            diff_check = run_git(worktree, ["diff", "--check"])
            markers = run_git(worktree, ["grep", "-nE", r"^(<<<<<<<|>>>>>>>)", "--", "."])
            ahead = run_git(worktree, ["rev-list", "--count", "@{u}..HEAD"], timeout=10)
            changed_list = changed["files"]
            out_of_allowed = [p for p in changed_list if allowed and not path_matches(p, allowed)]
            forbidden_hits = [p for p in changed_list if path_matches(p, forbidden)]

            if diff_check["returncode"] != 0:
                result["errors"].append("git diff --check failed")
            if markers["returncode"] == 0 and markers["stdout"]:
                result["errors"].append("conflict markers found in worktree")
            if forbidden_hits:
                result["errors"].append("changed files match Forbidden Files")
            if out_of_allowed:
                result["errors"].append("changed files outside Allowed Files")
            try:
                ahead_count = int(ahead["stdout"]) if ahead["returncode"] == 0 and ahead["stdout"] else 0
            except ValueError:
                ahead_count = 0
            approval_text = combined_all + "\n" + (read(deploy_gate) if deploy_gate else "")
            if source_push == "PASS" and ahead_count > 1 and not re.search(r"\b(PUSH_APPROVED_BY_OWNER|PUSH_REVIEWED_BY_MANAGER):", approval_text):
                result["errors"].append("Source push PASS on branch ahead by >1 commit requires owner or manager push approval")

            worktree_summary = {
                "path": str(worktree),
                "base_sha": base_sha,
                "changed_count": changed["count"],
                "changed_top": changed["top"],
                "out_of_allowed_top": out_of_allowed[: args.max_files],
                "forbidden_hits_top": forbidden_hits[: args.max_files],
                "diff_check": "pass" if diff_check["returncode"] == 0 else "fail",
                "conflict_markers": len(markers["stdout"].splitlines()) if markers["returncode"] == 0 and markers["stdout"] else 0,
                "ahead_count": ahead_count,
            }

    result["summary"] = {
        "files": len(files),
        "text_files": len(text_files),
        "proof_files": [rel(p, root) for p in proof_files[: args.max_files]],
        "pass_claims": pass_claims[: args.max_files],
        "has_browser_like_proof": has_browser_proof,
        "has_test_like_proof": has_test_proof,
        "allowed_files": allowed,
        "forbidden_files": forbidden,
        "current_status": status_fields,
        "commit_doc": commit_doc_result,
        "deploy_gate": str(deploy_gate) if deploy_gate else "",
        "worktree": worktree_summary,
    }

    if result["errors"]:
        result["status"] = "BLOCKED"
    elif result["warnings"]:
        result["status"] = "PARTIAL"
    else:
        result["status"] = "PASS"

    print(json.dumps(result, indent=2))
    return 1 if args.strict and result["status"] != "PASS" else (1 if result["status"] == "BLOCKED" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
