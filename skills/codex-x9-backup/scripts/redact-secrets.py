#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import sqlite3
import tempfile
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
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".exe", ".dll", ".node", ".zip", ".gz", ".pyc"}
SQLITE_SUFFIXES = {".sqlite", ".db"}


def match_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


def redact_text(text: str, events: list, location: dict) -> tuple[str, int]:
    replacements = 0
    for rule_name, pattern in RULES:
        def repl(match: re.Match) -> str:
            nonlocal replacements
            replacements += 1
            token_hash = match_hash(match.group(0))
            event = dict(location)
            event.update({"rule": rule_name, "match_sha256_prefix": token_hash})
            events.append(event)
            return f"[REDACTED:{rule_name}:{token_hash}]"
        text = pattern.sub(repl, text)
    return text, replacements


def redact_text_file(path: Path, root: Path, events: list) -> int:
    changed = 0
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as src, temp_path.open("w", encoding="utf-8", newline="") as dst:
            for line_no, line in enumerate(src, 1):
                redacted, count = redact_text(line, events, {"path": path.relative_to(root).as_posix(), "line": line_no})
                changed += count
                dst.write(redacted)
        if changed:
            temp_path.replace(path)
        else:
            temp_path.unlink(missing_ok=True)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return changed


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def redact_sqlite(path: Path, root: Path, events: list) -> int:
    rel = path.relative_to(root).as_posix()
    replacements = 0
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA secure_delete=ON")
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for table in tables:
            if table.startswith("sqlite_"):
                continue
            columns = conn.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall()
            text_cols = [col[1] for col in columns if "TEXT" in (col[2] or "").upper()]
            for col in text_cols:
                try:
                    rows = conn.execute(f"SELECT rowid, {quote_ident(col)} FROM {quote_ident(table)} WHERE {quote_ident(col)} IS NOT NULL").fetchall()
                except sqlite3.DatabaseError:
                    continue
                for rowid, value in rows:
                    if not isinstance(value, str):
                        continue
                    redacted, count = redact_text(value, events, {"path": rel, "table": table, "column": col, "rowid": rowid})
                    if count:
                        conn.execute(
                            f"UPDATE {quote_ident(table)} SET {quote_ident(col)} = ? WHERE rowid = ?",
                            (redacted, rowid),
                        )
                        replacements += count
        conn.commit()
        if replacements:
            conn.execute("VACUUM")
    finally:
        conn.close()
    return replacements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.root)
    output = Path(args.output)
    events = []
    files_scanned = 0
    files_changed = 0
    replacements = 0

    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        current_path = Path(current)
        for name in files:
            path = current_path / name
            suffix = path.suffix.lower()
            if suffix in BINARY_SUFFIXES:
                continue
            files_scanned += 1
            if suffix in SQLITE_SUFFIXES:
                count = redact_sqlite(path, root, events)
            else:
                count = redact_text_file(path, root, events)
            if count:
                files_changed += 1
                replacements += count

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files_scanned": files_scanned,
        "files_changed": files_changed,
        "replacement_count": replacements,
        "raw_values_printed": False,
        "events": events,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"redactions={replacements} files_changed={files_changed} report={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
