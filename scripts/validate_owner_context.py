from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ALLOWED_MODES = {
    "BINARY_VIEWED",
    "VISUAL_READER_SPOTCHECK",
    "TEXT_DOCUMENT_READ",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_bundle(bundle: Path, receipt: Path) -> list[str]:
    errors: list[str] = []
    request = bundle / "OWNER_REQUEST.md"
    attachments_path = bundle / "ATTACHMENTS.json"
    if not request.is_file():
        errors.append("MISSING_OWNER_REQUEST")
        return errors
    if not attachments_path.is_file():
        errors.append("MISSING_ATTACHMENT_MANIFEST")
        return errors
    if not receipt.is_file():
        errors.append("MISSING_OWNER_CONTEXT_RECEIPT")
        return errors

    receipt_text = receipt.read_text(encoding="utf-8")
    request_hash = sha256(request)
    if "OWNER_CONTEXT_RECEIPT: PASS" not in receipt_text:
        errors.append("OWNER_CONTEXT_RECEIPT: BLOCKED")
    if f"OWNER_REQUEST_SHA256: {request_hash}" not in receipt_text:
        errors.append("OWNER_REQUEST_HASH_MISMATCH")

    data = json.loads(attachments_path.read_text(encoding="utf-8"))
    for attachment in data.get("attachments", []):
        if not attachment.get("required", False):
            continue
        attachment_id = str(attachment.get("id") or "")
        stable_path = Path(str(attachment.get("stable_path") or ""))
        if not stable_path.is_absolute():
            stable_path = bundle / stable_path
        if not stable_path.is_file():
            errors.append(f"MISSING_ATTACHMENT:{attachment_id}")
            continue
        actual_hash = sha256(stable_path)
        expected_hash = str(attachment.get("sha256") or "")
        if actual_hash != expected_hash:
            errors.append(f"ATTACHMENT_HASH_MISMATCH:{attachment_id}")
            continue
        matching_lines = [
            line
            for line in receipt_text.splitlines()
            if attachment_id in line and actual_hash in line
        ]
        if not matching_lines:
            errors.append(f"ATTACHMENT_RECEIPT_MISSING:{attachment_id}")
            continue
        if not any(any(mode in line for mode in ALLOWED_MODES) for line in matching_lines):
            errors.append(f"ATTACHMENT_NOT_VIEWED:{attachment_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    errors = validate_bundle(args.bundle.resolve(), args.receipt.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: owner message and required attachments were received")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
