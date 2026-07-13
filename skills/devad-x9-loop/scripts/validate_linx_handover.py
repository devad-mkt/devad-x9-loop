from __future__ import annotations

import argparse
import re
from pathlib import Path


SHA256 = re.compile(r"^[0-9a-f]{64}$")


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        text,
        re.MULTILINE,
    )
    return match.group(1) if match else ""


def field(text: str, name: str) -> str:
    match = re.search(rf"^\*\*{re.escape(name)}:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if field(text, "Status") != "ACTIVATED":
        errors.append("status is not ACTIVATED")
    if field(text, "Execution authority") != "NEW_LINX":
        errors.append("execution authority is not NEW_LINX")
    if field(text, "One execution authority") != "PASS":
        errors.append("one execution authority is not PASS")

    inventory = section(text, "HANDOVER_INVENTORY_REQUEST")
    if field(inventory, "Mode") != "STATUS_ONLY":
        errors.append("inventory mode is not STATUS_ONLY")
    if field(inventory, "Coverage") != "PASS":
        errors.append("inventory coverage is not PASS")

    scope = section(text, "OWNER_SCOPE_MATRIX")
    if not any(value in scope for value in ("IMPLEMENT", "REJECTED", "PAUSED", "UNKNOWN")):
        errors.append("owner scope matrix has no classified requirement")

    plan = section(text, "NEW_LINX_PLAN")
    plan_path = field(plan, "Path")
    plan_sha = field(plan, "SHA-256")
    if not plan_path or plan_path == "NONE":
        errors.append("new Linx plan path is missing")
    if not SHA256.fullmatch(plan_sha):
        errors.append("new Linx plan SHA-256 is invalid")

    review = section(text, "OLD_LINX_FINAL_REVIEW")
    if field(review, "Result") != "PASS":
        errors.append("old Linx final review is not PASS")

    activation = section(text, "LINX_ACTIVATION_OK")
    new_thread = field(text, "New Linx thread")
    handover_sha = field(activation, "Handover SHA-256")
    activation_plan_sha = field(activation, "Plan SHA-256")
    expected = f"LINX_ACTIVATION_OK:{new_thread}:{handover_sha}:{activation_plan_sha}"
    if not SHA256.fullmatch(handover_sha):
        errors.append("handover SHA-256 is invalid")
    if activation_plan_sha != plan_sha:
        errors.append("activation plan SHA-256 does not match NEW_LINX_PLAN")
    if field(activation, "Token") != expected:
        errors.append("activation token does not match thread and hashes")
    if field(activation, "Old Linx retired") != "YES":
        errors.append("old Linx is not retired")

    heartbeat = section(text, "Heartbeat")
    if field(heartbeat, "Target") != new_thread:
        errors.append("heartbeat target is not the new Linx")
    if field(heartbeat, "Cadence") != "19 minutes":
        errors.append("heartbeat cadence is not 19 minutes")
    if field(heartbeat, "Pass lock") != "SKIP_ACTIVE_MANAGER_PASS":
        errors.append("heartbeat pass-lock rule is missing")
    try:
        max_wakes = int(field(heartbeat, "Max wakes"))
        if not 1 <= max_wakes <= 76:
            errors.append("heartbeat max wakes must be between 1 and 76")
    except ValueError:
        errors.append("heartbeat max wakes is invalid")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, type=Path)
    args = parser.parse_args()
    errors = validate(args.state)
    if errors:
        for error in errors:
            print(f"BLOCKED: {error}")
        return 1
    print("PASS: collaborative Linx handover activation is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
