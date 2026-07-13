from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
from uuid import uuid4


ROLES = {"LINX", "THINX", "WORKER", "READER", "CHUNK", "SIDE"}
POOL_LIMITS = {"CODING": 2, "READ_ONLY": 2, "RUNTIME_PROOF": 1, "DEPLOY": 1}
TITLE_ROLES = {
    "linx": "LINX",
    "sub manager": "LINX",
    "thinX".lower(): "THINX",
    "top manager": "THINX",
    "worker": "WORKER",
    "reader": "READER",
    "chunk": "CHUNK",
    "side": "SIDE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_role_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tasks = registry.get("tasks")
    if not isinstance(tasks, dict):
        return ["ROLE_REGISTRY_INVALID:tasks"]

    for task_id, entry in tasks.items():
        if not task_id or not isinstance(entry, dict):
            errors.append(f"ROLE_REGISTRY_INVALID:{task_id}")
            continue
        role = str(entry.get("role", "")).upper()
        title = str(entry.get("title", ""))
        if role not in ROLES:
            errors.append(f"ROLE_INVALID:{task_id}:{role}")
            continue
        if entry.get("immutable") is not True:
            errors.append(f"ROLE_NOT_IMMUTABLE:{task_id}")
        lowered = title.lower()
        named_roles = {
            named
            for label, named in TITLE_ROLES.items()
            if re.search(r"(?<![a-z0-9])" + re.escape(label) + r"(?![a-z0-9])", lowered)
        }
        for named in sorted(named_roles):
            if named != role:
                errors.append(f"TITLE_ROLE_MISMATCH:{task_id}:{role}:{title}")
                break
    return errors


def _find_dispatch(ledger: list[dict[str, Any]], dispatch_id: str) -> dict[str, Any]:
    for record in reversed(ledger):
        if record.get("dispatch_id") == dispatch_id and record.get("event") == "DISPATCH_CREATED":
            return record
    raise KeyError(f"DISPATCH_NOT_FOUND:{dispatch_id}")


def create_dispatch(
    ledger: list[dict[str, Any]],
    sender_task_id: str,
    target_task_id: str,
    target_role: str,
    packet_sha256: str,
    *,
    supersedes: str | None = None,
) -> str:
    role = target_role.upper()
    if role not in ROLES:
        raise ValueError(f"ROLE_INVALID:{role}")
    if len(packet_sha256) != 64:
        raise ValueError("PACKET_SHA256_INVALID")
    dispatch_id = f"dsp-{uuid4()}"
    ledger.append(
        {
            "event": "DISPATCH_CREATED",
            "dispatch_id": dispatch_id,
            "sender_task_id": sender_task_id,
            "target_task_id": target_task_id,
            "target_role": role,
            "packet_sha256": packet_sha256.lower(),
            "created_at": utc_now(),
            "supersedes": supersedes,
            "attempts": [],
            "acknowledgement": None,
            "circuit_state": "OPEN",
        }
    )
    return dispatch_id


def record_attempt(
    ledger: list[dict[str, Any]],
    dispatch_id: str,
    method: str,
    transport_result: str,
    *,
    attempted_at: str | None = None,
) -> int:
    record = _find_dispatch(ledger, dispatch_id)
    attempts = record.setdefault("attempts", [])
    attempts.append(
        {
            "attempt": len(attempts) + 1,
            "time": attempted_at or utc_now(),
            "method": method,
            "transport_result": transport_result,
        }
    )
    if len(attempts) >= 3 and not record.get("acknowledgement"):
        record["circuit_state"] = "PAUSED_FOR_THINX"
    return len(attempts)


def acknowledge(
    ledger: list[dict[str, Any]],
    dispatch_id: str,
    worker_task_id: str,
    packet_sha256: str,
    receipt_path: str,
    receipt_sha256: str,
) -> None:
    record = _find_dispatch(ledger, dispatch_id)
    if worker_task_id != record["target_task_id"]:
        raise ValueError("ACK_TASK_MISMATCH")
    if record["target_role"] != "WORKER":
        raise ValueError("ACK_ROLE_MISMATCH")
    if packet_sha256.lower() != record["packet_sha256"]:
        raise ValueError("ACK_PACKET_MISMATCH")
    record["acknowledgement"] = {
        "worker_task_id": worker_task_id,
        "packet_sha256": packet_sha256.lower(),
        "receipt_path": receipt_path,
        "receipt_sha256": receipt_sha256,
        "acknowledged_at": utc_now(),
    }
    record["circuit_state"] = "CLOSED"


def delivery_report(ledger: list[dict[str, Any]], dispatch_id: str) -> dict[str, Any]:
    record = _find_dispatch(ledger, dispatch_id)
    attempts = len(record.get("attempts", []))
    ack = record.get("acknowledgement")
    exact_ack = bool(
        ack
        and ack.get("worker_task_id") == record["target_task_id"]
        and ack.get("packet_sha256") == record["packet_sha256"]
    )
    return {
        "dispatch_id": dispatch_id,
        "status": "ACKNOWLEDGED" if exact_ack else "DELIVERY_UNCONFIRMED",
        "attempts": attempts,
        "sent_once": attempts == 1 and exact_ack,
        "circuit_state": record.get("circuit_state", "OPEN"),
    }


def retry_decision(ledger: list[dict[str, Any]], dispatch_id: str) -> str:
    record = _find_dispatch(ledger, dispatch_id)
    report = delivery_report(ledger, dispatch_id)
    if report["status"] == "ACKNOWLEDGED":
        return "SKIP_ALREADY_DELIVERED"
    if report["attempts"] >= 3:
        return "PAUSE_FOR_THINX"
    attempts = record.get("attempts", [])
    if attempts and attempts[-1].get("transport_result") == "accepted":
        return "CHECK_RECEIPT_ONCE"
    return "RETRY_SAME_DISPATCH"


def validate_completion(expected: dict[str, str], receipt: dict[str, str]) -> str:
    for key in ("task_id", "dispatch_id", "role", "packet_sha256"):
        if receipt.get(key) != expected.get(key):
            return f"STALE_COMPLETION:{key}"
    if receipt.get("role") != "WORKER":
        return "STALE_COMPLETION:role"
    owner = receipt.get("receipt_owner_task_id", receipt.get("task_id"))
    if owner != expected.get("task_id"):
        return "STALE_COMPLETION:receipt_owner_task_id"
    if "receipt_path" in expected and receipt.get("receipt_path") != expected.get("receipt_path"):
        return "STALE_COMPLETION:receipt_path"
    if "receipt_sha256" in expected and receipt.get("receipt_sha256") != expected.get("receipt_sha256"):
        return "STALE_COMPLETION:receipt_sha256"
    return "PASS"


def _conflicts(candidate: list[str], selected: set[str]) -> bool:
    return any(claim in selected for claim in candidate)


def select_ready_tasks(
    tasks: list[dict[str, Any]],
    claims: dict[str, list[str]],
    *,
    pool_limits: dict[str, int] | None = None,
) -> dict[str, list[str]]:
    limits = dict(POOL_LIMITS)
    if pool_limits:
        limits.update(pool_limits)
    completed = {task["id"] for task in tasks if task.get("status") == "COMPLETE"}
    selected: dict[str, list[str]] = {pool: [] for pool in limits}
    claimed: set[str] = set()

    for task in tasks:
        if task.get("status") != "READY":
            continue
        if any(dep not in completed for dep in task.get("dependencies", [])):
            continue
        pool = task.get("pool", "CODING")
        if pool not in limits or len(selected[pool]) >= limits[pool]:
            continue
        task_claims = claims.get(task["id"], [])
        if _conflicts(task_claims, claimed):
            continue
        selected[pool].append(task["id"])
        claimed.update(task_claims)
    return selected


def can_promote_coding_pool(metrics: dict[str, int]) -> bool:
    return (
        metrics.get("calendar_days", 0) >= 3
        and metrics.get("dispatches", 0) >= 10
        and metrics.get("lost_work", 1) == 0
        and metrics.get("identity_errors", 1) == 0
        and metrics.get("resource_conflicts", 1) == 0
        and metrics.get("critical_errors", 1) == 0
        and metrics.get("orchestration_retries", 2) <= 1
    )
