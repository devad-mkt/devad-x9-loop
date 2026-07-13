#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

RULES = [
    ("openai_key", re.compile(r"\bsk-(?:proj|svcacct|admin|live|test)?-?[A-Za-z0-9_\-]{24,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b|github_pat_[A-Za-z0-9_]{20,}_[A-Za-z0-9_]{20,}")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{24,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
]

SKIP_DIRS = {".git", "node_modules", ".cache", "cache", "tmp", ".tmp", "__pycache__"}


def hash_match(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def scan_file(path: Path, rel: str, findings: list, max_findings: int) -> None:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_no, line in enumerate(handle, 1):
                for rule_name, pattern in RULES:
                    for match in pattern.finditer(line):
                        findings.append({
                            "path": rel,
                            "line": line_no,
                            "rule": rule_name,
                            "match_sha256": hash_match(match.group(0)),
                        })
                        if len(findings) >= max_findings:
                            return
    except OSError as exc:
        findings.append({"path": rel, "line": 0, "rule": "read_error", "error": exc.__class__.__name__})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-findings", type=int, default=50)
    args = parser.parse_args()

    root = Path(args.root)
    output = Path(args.output)
    findings = []
    scanned = 0
    skipped = 0

    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        current_path = Path(current)
        for name in files:
            path = current_path / name
            rel = path.relative_to(root).as_posix()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".exe", ".dll", ".node", ".zip", ".gz", ".pyc"}:
                skipped += 1
                continue
            scanned += 1
            scan_file(path, rel, findings, args.max_findings)
            if len(findings) >= args.max_findings:
                break
        if len(findings) >= args.max_findings:
            break

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "scanned_files": scanned,
        "skipped_binary_like_files": skipped,
        "finding_count": len(findings),
        "findings": findings,
        "raw_values_printed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if findings:
        print(f"BLOCKED: secret scan found {len(findings)} high-confidence match(es). Report: {output}")
        return 2
    print(f"PASS: secret scan found no high-confidence matches. Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
