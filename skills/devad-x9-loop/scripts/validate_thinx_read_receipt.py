#!/usr/bin/env python3
"""Validate a Thinx request manifest against a decision read receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize(value: str) -> str:
    return value.strip().strip("`").strip()


def scalar(text: str, field: str) -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(field.lower() + ":"):
            return normalize(line.split(":", 1)[1])
    return ""


def table_after_marker(text: str, marker: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    marker_index = next(
        (index for index, line in enumerate(lines) if line.strip() == marker),
        None,
    )
    if marker_index is None:
        return []

    table_lines: list[str] = []
    for line in lines[marker_index + 1 :]:
        stripped = line.strip()
        if not stripped and not table_lines:
            continue
        if not stripped.startswith("|"):
            if table_lines:
                break
            continue
        table_lines.append(stripped)

    if len(table_lines) < 3:
        return []

    def cells(line: str) -> list[str]:
        return [normalize(cell) for cell in line.strip("|").split("|")]

    headers = [header.lower() for header in cells(table_lines[0])]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        values = cells(line)
        if len(values) != len(headers):
            continue
        rows.append(dict(zip(headers, values)))
    return rows


def validate(request_path: Path, decision_path: Path) -> dict[str, object]:
    errors: list[str] = []
    request_text = read_text(request_path)
    decision_text = read_text(decision_path)
    request_rows = table_after_marker(request_text, "INPUT_MANIFEST:")
    receipt_rows = table_after_marker(decision_text, "READ_RECEIPT: PASS")
    locked_thread = scalar(request_text, "THINX_THREAD_LOCK")
    decision_thread = scalar(decision_text, "THINX_THREAD_ID")

    if not locked_thread:
        errors.append("request is missing THINX_THREAD_LOCK")
    if not decision_thread:
        errors.append("decision is missing THINX_THREAD_ID")
    if locked_thread and decision_thread and locked_thread != decision_thread:
        errors.append("decision came from a different Thinx thread")
    if not request_rows:
        errors.append("request is missing INPUT_MANIFEST table")
    if "READ_RECEIPT: PASS" not in decision_text:
        errors.append("decision is missing READ_RECEIPT: PASS")
    if not receipt_rows:
        errors.append("decision is missing read receipt table")

    requests: dict[str, dict[str, str]] = {}
    for row in request_rows:
        item_id = row.get("id", "")
        identity = row.get("identity", "")
        read_rule = row.get("read rule", "").upper()
        if not item_id:
            errors.append("request input has no ID")
            continue
        if item_id in requests:
            errors.append(f"duplicate request input ID: {item_id}")
            continue
        if not identity or identity.upper() in {"UNKNOWN", "PENDING", "NONE"}:
            errors.append(f"request input {item_id} has no stable identity")
        if read_rule not in {"DIRECT", "READER_OK"}:
            errors.append(f"request input {item_id} has invalid read rule: {read_rule}")
        requests[item_id] = row

    receipts = {row.get("id", ""): row for row in receipt_rows if row.get("id", "")}
    for item_id, request in requests.items():
        receipt = receipts.get(item_id)
        if receipt is None:
            errors.append(f"missing receipt for input: {item_id}")
            continue
        expected_identity = normalize(request.get("identity", ""))
        actual_identity = normalize(receipt.get("identity read", ""))
        if expected_identity != actual_identity:
            errors.append(f"identity mismatch for input: {item_id}")
        mode = receipt.get("mode", "").upper()
        read_rule = request.get("read rule", "").upper()
        if read_rule == "DIRECT" and mode != "DIRECT":
            errors.append(f"DIRECT input was not read directly: {item_id}")
        if read_rule == "READER_OK" and mode not in {"DIRECT", "DIGEST_SPOTCHECK"}:
            errors.append(f"invalid receipt mode for input: {item_id}")
        if receipt.get("result", "").upper() != "PASS":
            errors.append(f"receipt result is not PASS for input: {item_id}")

    return {
        "status": "PASS" if not errors else "BLOCKED",
        "request": str(request_path),
        "decision": str(decision_path),
        "request_inputs": len(requests),
        "receipt_inputs": len(receipts),
        "thinx_thread_lock": locked_thread,
        "decision_thread_id": decision_thread,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--decision", required=True, type=Path)
    args = parser.parse_args()

    missing = [str(path) for path in (args.request, args.decision) if not path.is_file()]
    if missing:
        result = {"status": "BLOCKED", "errors": [f"missing file: {path}" for path in missing]}
    else:
        result = validate(args.request, args.decision)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
