from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("skills", "scripts", "templates")
STATUSES = {"RETAINED", "MOVED", "ADAPTED", "NEW", "RETIRED"}
INVARIANTS = [
    "truth-and-mission-locks",
    "manager-pass-mutex",
    "local-work-ledger-and-release-states",
    "worktree-preservation-and-exact-scope",
    "security-before-commit",
    "c1-source-plus-c2-attestation",
    "separate-push-deploy-live-proof-gates",
    "destructive-action-guard",
    "owner-message-and-attachment-hashes",
    "thinx-verified-read-receipts",
    "answered-decisions-and-tool-lessons",
    "compact-status-handoffs-detailed-runs",
    "feature-catalog-and-manifest-routing",
    "linx-collaborative-handover",
    "glm-kimi-bounded-reader-challenge",
    "model-benchmark-and-ultra-return",
    "backup-secret-scan-memory-token-diagnostics",
]
NEW_FEATURES = [
    ("loop-history-free-linx", "devad-x9-loop", "History-free Linx durable routing"),
    ("loop-role-registry", "devad-x9-loop", "Immutable task-ID role authority"),
    ("loop-title-role-mismatch", "devad-x9-loop", "Detect misleading task titles"),
    ("loop-dispatch-id", "devad-x9-loop", "Unique packet dispatch identity"),
    ("loop-delivery-ledger", "devad-x9-loop", "Append-only attempts and acknowledgements"),
    ("loop-honest-delivery-report", "devad-x9-loop", "Evidence-backed sent-once claims"),
    ("loop-pass-capsule", "devad-x9-loop", "Verified compact pass truth below 8 KB"),
    ("loop-global-worktree-index", "devad-x9-loop", "Cross-clone local work and preservation"),
    ("loop-task-graph", "devad-x9-loop", "Dependency-ready task state"),
    ("loop-resource-claims", "devad-x9-loop", "Conflict-free parallel scheduling"),
    ("loop-event-cursor", "devad-x9-loop", "Process immutable Worker events once"),
    ("loop-decision-gates", "devad-x9-loop", "Task-scoped owner and Thinx decisions"),
    ("loop-scoped-completion", "devad-x9-loop", "Reject stale and wrong-task handoffs"),
    ("loop-three-failure-breaker", "devad-x9-loop", "Pause one dispatch for Thinx review"),
    ("loop-two-worker-promotion", "devad-x9-loop", "Measured concurrency promotion"),
    ("loop-manager-compat-shim", "devad-x9-manager", "Temporary v3 prompt redirect"),
]
V6_FEATURES = [
    ("loop-lite-controller", "devad-x9-loop", "skills/devad-x9-loop/scripts/loopctl.py", "Transactional Loop Lite v6 controller and one-action reconciliation boundary", "tests/test_loop_lite_v6.py"),
    ("loop-lite-recovery-snapshot", "devad-x9-loop", "templates/x9-project/.devad/manager/loop-lite/SNAPSHOT.json", "Tracked compact recovery truth independent of disposable SQLite runtime state", "tests/test_loop_lite_package.py::LoopLitePackageTests"),
    ("loop-lite-machine-contracts", "devad-x9-loop", "templates/x9-project/.devad/manager/loop-lite/contracts", "Versioned JSON contracts for owner packets, tasks, actions, and results", "tests/test_loop_lite_package.py::LoopLitePackageTests"),
    ("loop-lite-scope-claims", "devad-x9-loop", "skills/devad-x9-loop/references/loop-lite-v6-contract.md", "Claim-bound completion and scope-breach rejection across all Git surfaces", "tests/test_loop_lite_v6.py"),
    ("loop-lite-direct-callback", "devad-x9-loop", "skills/devad-x9-loop/references/loop-lite-v6-contract.md", "Identity-checked direct callback without a recurring manager heartbeat", "tests/test_loop_lite_v6.py"),
    ("loop-lite-sidecar-doctor", "devad-x9-loop", "skills/devad-x9-loop/scripts/opencode_doctor.py", "Secret-safe bounded OpenCode doctor and advisory request gate", "tests/test_loop_lite_package.py::OpenCodeDoctorTests"),
    ("loop-lite-generated-human-views", "devad-x9-loop", "skills/devad-x9-loop/references/loop-lite-v6-contract.md", "Bounded generated status and handoff views that are never parser authority", "tests/test_loop_lite_v6.py"),
]
RETIRED_FEATURES = [
    ("retired-x7-broad-polling", "X7 broad polling"),
    ("retired-title-role-routing", "Role inference from task title"),
    ("retired-blind-resend", "Blind resend after accepted transport"),
    ("retired-orca-runtime", "Orca runtime integration"),
    ("retired-runtime-db-truth", "Runtime database as truth"),
    ("retired-four-worker-default", "Four coding Workers by default"),
    ("retired-two-second-model-poll", "Two-second model polling"),
    ("retired-auto-worker-kill", "Automatic stale Worker kill"),
    ("retired-age-only-worktree-move", "Age-only worktree move or deletion"),
]


ADAPTED_PATHS = {
    "skills/devad-x9/SKILL.md": "Worker entrypoint updated for v5 task and dispatch identity.",
    "skills/devad-x9/references/x9-shared-contract.md": "Shared authority names the real v5 loop and compatibility shim.",
    "skills/codex-x9-backup/SKILL.md": "Backup scope expanded from five v3 skills to six v5 skills.",
    "skills/codex-token-budget/SKILL.md": "Token audit adds event, dispatch, and no-change pass metrics.",
    "skills/devad-memory/SKILL.md": "Memory boundary now names loop state as active truth.",
    "skills/codex-x9-backup/scripts/restore-codex-x9-backup.ps1": "Invalid DryRun foreach pipeline fixed without changing restore scope.",
    "scripts/build_source_manifest.py": "Manifest now covers the complete v5 package except itself and generated cache.",
    "scripts/install-suite.ps1": "Installer now stages, validates, backs up, atomically swaps, and rolls back six skills.",
    "scripts/validate_suite.py": "Validator now enforces six skills, loop state, and migration coverage.",
    "templates/x9-project/.devad/ROUTER.md": "Router adds compact v5 loop state.",
    "templates/x9-project/.devad/manager/workers/_template/MANIFEST.json": "Worker manifest adds task, dispatch, packet, resource, and receipt identity.",
    "templates/x9-project/.devad/manager/workers/_template/STATUS.md": "Status adds v5 completion identity while keeping compact caps.",
    "templates/x9-project/.devad/manager/workers/_template/HANDOFFS.md": "Handoff adds v5 completion receipt identity.",
}


def stable_id(kind: str, source: str) -> str:
    digest = hashlib.sha256(f"{kind}:{source}".encode()).hexdigest()[:12]
    stem = re.sub(r"[^a-z0-9]+", "-", Path(source).stem.lower()).strip("-")[:36]
    return f"v3-{kind}-{stem}-{digest}"


def owner_for(relative: str) -> str:
    parts = Path(relative).parts
    if len(parts) >= 2 and parts[0] == "skills":
        return "devad-x9-loop" if parts[1] == "devad-x9-manager" else parts[1]
    if parts and parts[0] == "scripts":
        return "kit"
    if parts and parts[0] == "templates":
        return "devad-x9"
    return "kit"


def kind_for(relative: str) -> str:
    parts = Path(relative).parts
    if parts and parts[0] == "scripts":
        return "script"
    if parts and parts[0] == "templates":
        return "template"
    if Path(relative).suffix.lower() in {".py", ".ps1", ".js", ".mjs"}:
        return "script"
    return "file"


def inventory(source: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for root_name in SCAN_ROOTS:
        root = source / root_name
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            relative = path.relative_to(source).as_posix()
            kind = kind_for(relative)
            items.append({"id": stable_id(kind, relative), "kind": kind, "source": relative})
            if path.suffix.lower() == ".md":
                text = path.read_text(encoding="utf-8-sig", errors="replace")
                for line_no, line in enumerate(text.splitlines(), 1):
                    if not re.match(r"^#{1,6}\s+\S", line):
                        continue
                    heading = re.sub(r"^#{1,6}\s+", "", line).strip()
                    key = f"{relative}#L{line_no}:{heading}"
                    items.append(
                        {
                            "id": stable_id("heading", key),
                            "kind": "heading",
                            "source": relative,
                            "anchor": heading,
                        }
                    )
    for name in INVARIANTS:
        items.append(
            {
                "id": f"v3-invariant-{name}",
                "kind": "invariant",
                "source": f"v3-invariant:{name}",
            }
        )
    return items


def classify(item: dict[str, str]) -> dict[str, Any]:
    source = item["source"]
    owner = owner_for(source)
    result: dict[str, Any] = {
        "id": item["id"],
        "legacy_id": item["id"],
        "kind": item["kind"],
        "owner": owner,
        "source": f"devad-skills-set/{source}" if not source.startswith("v3-invariant:") else source,
        "purpose": f"Preserve v3 {item['kind']}: {item.get('anchor', source)}",
        "required_test": "tests/test_registry_coverage.py::RegistryCoverageTests",
    }
    if source.startswith("skills/devad-x9-manager"):
        replacement = source.replace("skills/devad-x9-manager", "skills/devad-x9-loop", 1)
        result.update(
            status="MOVED",
            replacement=replacement,
            reason="Real manager skill renamed to devad-x9-loop; detailed behavior retained.",
        )
    elif source in ADAPTED_PATHS:
        result.update(
            status="ADAPTED",
            replacement=source,
            reason=ADAPTED_PATHS[source],
        )
    elif source.startswith("v3-invariant:"):
        result.update(
            status="ADAPTED",
            replacement="features.registry.json plus v5 executable gates",
            reason="Invariant retained and strengthened with deterministic validation.",
        )
    else:
        result["status"] = "RETAINED"
    return result


def build(source: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    old = inventory(source)
    features = [classify(item) for item in old]
    for feature_id, owner, purpose in NEW_FEATURES:
        features.append(
            {
                "id": feature_id,
                "kind": "feature",
                "owner": owner,
                "source": "v5-plan",
                "status": "NEW",
                "purpose": purpose,
                "required_test": "tests/test_v5_contract.py",
            }
        )
    for feature_id, owner, source, purpose, required_test in V6_FEATURES:
        features.append(
            {
                "id": feature_id,
                "kind": "feature",
                "owner": owner,
                "source": source,
                "status": "NEW",
                "purpose": purpose,
                "required_test": required_test,
            }
        )
    for feature_id, purpose in RETIRED_FEATURES:
        features.append(
            {
                "id": feature_id,
                "kind": "mechanism",
                "owner": "devad-x9-loop",
                "source": "v3-and-research-history",
                "status": "RETIRED",
                "purpose": purpose,
                "required_test": "tests/test_registry_coverage.py::RegistryCoverageTests",
                "replacement": "Deterministic file/event loop",
                "reason": "Rejected for token burn, ambiguity, unsafe authority, or lost-work risk.",
            }
        )
    legacy = {
        "schema": "devad-x9-v3-inventory-v1",
        "source": "devad-skills-set",
        "items": old,
    }
    registry = {
        "schema": "devad-x9-loop-feature-registry-v1",
        "allowed_statuses": sorted(STATUSES),
        "features": features,
    }
    return legacy, registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    legacy, registry = build(args.source.resolve())
    print(f"legacy_items={len(legacy['items'])}")
    print(f"registry_features={len(registry['features'])}")
    if args.write:
        (ROOT / "legacy.inventory.json").write_text(
            json.dumps(legacy, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n"
        )
        (ROOT / "features.registry.json").write_text(
            json.dumps(registry, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
