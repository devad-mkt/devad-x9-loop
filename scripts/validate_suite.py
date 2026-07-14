from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "devad-x9",
    "devad-x9-loop",
    "devad-x9-manager",
    "codex-x9-backup",
    "codex-token-budget",
    "devad-memory",
)
CAP_NAMES = {"STATUS.md", "HANDOFFS.md"}
LOOP_FILES = {
    "ROLE_REGISTRY.json",
    "PASS_CAPSULE.json",
    "WORKTREE_INDEX.json",
    "TASK_GRAPH.json",
    "RESOURCE_CLAIMS.json",
    "EVENT_CURSOR.json",
    "DISPATCH_LEDGER.jsonl",
    "DECISION_GATES.json",
}
LOOP_LITE_FILES = {".gitignore", "README.md", "SNAPSHOT.json", "contracts"}
OWNER_PACKET_FILES = {".gitignore", "README.md"}
LOOP_LITE_CONTRACTS = {"OWNER_PACKET.json", "TASK.json", "ACTION.json", "RESULT.json"}
LOOP_LITE_TABLES = {
    "actors", "worktrees", "tasks", "claims", "resources", "dispatches",
    "deliveries", "events", "gates", "outbox", "metrics",
}
LOOP_LITE_IGNORES = {"loop.db", "loop.db-shm", "loop.db-wal", "runtime/", "*.corrupt-*", "*.failed-*", "*.rebuild-*"}
LOOP_LITE_CONTROLLER = "skills/devad-x9-loop/scripts/loopctl.py"
ALLOWED_STATUS = {"RETAINED", "MOVED", "ADAPTED", "NEW", "RETIRED"}


def validate_manifest(errors: list[str]) -> None:
    manifest = ROOT / "SOURCE_MANIFEST.sha256"
    if not manifest.is_file():
        errors.append("missing SOURCE_MANIFEST.sha256")
        return
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            digest, relative = line.split("  ", 1)
        except ValueError:
            errors.append("invalid source manifest line")
            continue
        if relative == ".git" or relative.startswith(".git/"):
            errors.append(f"manifest includes Git metadata: {relative}")
            continue
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"manifest missing file: {relative}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"manifest mismatch: {relative}")


def validate_skills(errors: list[str]) -> None:
    actual = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
    if actual != set(SKILLS):
        errors.append(f"skill set mismatch: {sorted(actual)}")
    for name in SKILLS:
        path = ROOT / "skills" / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing skill: {name}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        if not text.startswith("---\n") or f"name: {name}" not in text:
            errors.append(f"invalid skill frontmatter: {name}")
        if len(text.splitlines()) > 300:
            errors.append(f"skill entrypoint over 300 lines: {name}")
    shim = ROOT / "skills" / "devad-x9-manager" / "SKILL.md"
    if shim.is_file():
        text = shim.read_text(encoding="utf-8-sig")
        if "devad-x9-loop" not in text or len(text.splitlines()) > 40:
            errors.append("compatibility shim is not a small redirect")


def validate_registry(errors: list[str]) -> None:
    try:
        legacy = json.loads((ROOT / "legacy.inventory.json").read_text(encoding="utf-8-sig"))
        registry = json.loads((ROOT / "features.registry.json").read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        errors.append(f"registry load failed: {exc}")
        return
    old_ids = {item["id"] for item in legacy.get("items", [])}
    features = registry.get("features", [])
    covered = [item.get("legacy_id") for item in features if item.get("legacy_id")]
    if len(covered) != len(set(covered)):
        errors.append("duplicate legacy feature classifications")
    missing = sorted(old_ids - set(covered))
    if missing:
        errors.append(f"unclassified legacy features: {len(missing)}")
    for feature in features:
        for field in ("id", "owner", "source", "status", "purpose", "required_test"):
            if not feature.get(field):
                errors.append(f"feature missing {field}: {feature.get('id')}")
        status = feature.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"invalid feature status: {feature.get('id')}:{status}")
        if status in {"MOVED", "ADAPTED", "RETIRED"}:
            if not feature.get("replacement") or not feature.get("reason"):
                errors.append(f"feature missing replacement/reason: {feature.get('id')}")


def validate_template(errors: list[str]) -> None:
    template = ROOT / "templates" / "x9-project" / ".devad"
    router = template / "ROUTER.md"
    if not router.is_file() or "Read this file first" not in router.read_text(encoding="utf-8-sig"):
        errors.append("missing manifest-first project router")
    loop = template / "manager" / "loop"
    actual_loop = {path.name for path in loop.iterdir() if path.is_file()} if loop.is_dir() else set()
    if actual_loop != LOOP_FILES:
        errors.append(f"loop template mismatch: {sorted(actual_loop)}")
    capsule = loop / "PASS_CAPSULE.json"
    if capsule.is_file() and capsule.stat().st_size >= 8192:
        errors.append("template PASS_CAPSULE is not below 8 KB")

    for path in template.rglob("*"):
        if path.is_dir():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            errors.append(f"generated cache included: {path.relative_to(ROOT)}")
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
        if path.name in CAP_NAMES:
            text = path.read_text(encoding="utf-8-sig")
            if len(text.splitlines()) > 120 or len(path.read_bytes()) > 12_000:
                errors.append(f"active file over compact cap: {path.relative_to(ROOT)}")

    link_re = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for path in template.rglob("*.md"):
        for target in link_re.findall(path.read_text(encoding="utf-8-sig")):
            if target.startswith(("http://", "https://", "#", "/")) or "<" in target or ">" in target:
                continue
            clean = target.split("#", 1)[0]
            if clean and not (path.parent / clean).resolve().exists():
                errors.append(f"broken template link: {path.relative_to(ROOT)} -> {target}")


def validate_loop_lite(errors: list[str]) -> None:
    loop_lite = ROOT / "templates" / "x9-project" / ".devad" / "manager" / "loop-lite"
    if not loop_lite.is_dir():
        errors.append("missing loop-lite template")
        return
    missing = sorted(name for name in LOOP_LITE_FILES if not (loop_lite / name).exists())
    if missing:
        if "SNAPSHOT.json" in missing:
            errors.append("missing loop-lite recovery snapshot")
        errors.extend(f"missing loop-lite artifact: {name}" for name in missing if name != "SNAPSHOT.json")
        return
    controller = ROOT / LOOP_LITE_CONTROLLER
    if not controller.is_file():
        errors.append("missing loop-lite controller")
    owner_store = loop_lite.parent / "owner-packets"
    owner_files = (
        {path.name for path in owner_store.iterdir() if path.is_file()}
        if owner_store.is_dir()
        else set()
    )
    if owner_files != OWNER_PACKET_FILES:
        errors.append(f"owner-packet template mismatch: {sorted(owner_files)}")
    else:
        owner_ignores = set(
            (owner_store / ".gitignore")
            .read_text(encoding="utf-8-sig")
            .splitlines()
        )
        if not {"*", "!.gitignore", "!README.md"}.issubset(owner_ignores):
            errors.append("owner-packet local-only ignore is incomplete")
        owner_readme = (owner_store / "README.md").read_text(
            encoding="utf-8-sig"
        )
        if "local sensitive state" not in owner_readme:
            errors.append("owner-packet privacy policy is missing")
    ignored = set((loop_lite / ".gitignore").read_text(encoding="utf-8-sig").splitlines())
    missing_ignores = sorted(LOOP_LITE_IGNORES - ignored)
    if missing_ignores:
        errors.append(f"loop-lite gitignore incomplete: {missing_ignores}")
    snapshot = loop_lite / "SNAPSHOT.json"
    if snapshot.stat().st_size >= 8192:
        errors.append("loop-lite recovery snapshot is not below 8 KB")
    try:
        payload = json.loads(snapshot.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return
    tables = payload.get("tables")
    if not isinstance(tables, dict) or set(tables) != LOOP_LITE_TABLES:
        errors.append("loop-lite snapshot tables do not match controller contract")
    contracts = loop_lite / "contracts"
    actual_contracts = {path.name for path in contracts.glob("*.json")}
    if actual_contracts != LOOP_LITE_CONTRACTS:
        errors.append(f"loop-lite contract mismatch: {sorted(actual_contracts)}")
    for path in contracts.glob("*.json"):
        if path.stat().st_size >= 4096:
            errors.append(f"loop-lite contract over compact cap: {path.relative_to(ROOT)}")
    try:
        action_payload = json.loads((contracts / "ACTION.json").read_text(encoding="utf-8-sig"))
        task_payload = json.loads((contracts / "TASK.json").read_text(encoding="utf-8-sig"))
        owner_payload = json.loads((contracts / "OWNER_PACKET.json").read_text(encoding="utf-8-sig"))
        result_payload = json.loads((contracts / "RESULT.json").read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return
    packet = action_payload.get("packet")
    required_packet_fields = {
        "schema", "task_id", "sender_id", "target_actor_id", "worktree_id",
        "worktree_path", "base_sha", "owner_packet_path", "owner_packet_sha256",
        "local_work", "dependencies", "claims", "resources", "gates", "finish_line",
    }
    if "packet_path" in action_payload or not isinstance(packet, dict) or not required_packet_fields.issubset(packet) or packet.get("owner_packet_path") != ".devad/manager/owner-packets/<packet_sha256>.json":
        errors.append("loop-lite action contract missing immutable packet fields")
    if not {"owner_packet_path", "owner_packet_sha256"}.issubset(task_payload) or task_payload.get("owner_packet_path") != ".devad/manager/owner-packets/<packet_sha256>.json":
        errors.append("loop-lite task contract missing content-addressed owner packet")
    attachments = owner_payload.get("attachments")
    if owner_payload.get("schema") != "x9-owner-packet-v1" or "packet_sha256" in owner_payload or not isinstance(attachments, list) or not attachments or attachments[0].get("path") != ".devad/manager/owner-packets/artifacts/<attachment_sha256>.txt":
        errors.append("loop-lite owner packet contract is not controller-compatible")
    proof = result_payload.get("proof")
    expected_proof_paths = {
        "security": ".devad/workers/<worker_id>/proof/<event_id>/security.json",
        "tests": ".devad/workers/<worker_id>/proof/<event_id>/tests.json",
    }
    proof_is_structured = isinstance(proof, list) and bool(proof) and all(
        isinstance(item, dict) and {"kind", "path", "sha256"}.issubset(item)
        for item in proof
    ) and {item["kind"] for item in proof} == {"security", "tests"} and {item["kind"]: item["path"] for item in proof} == expected_proof_paths
    if result_payload.get("outcome") != "COMPLETE" or not proof_is_structured or not isinstance(result_payload.get("c1"), str) or not isinstance(result_payload.get("c2"), str):
        errors.append("loop-lite result contract missing security/tests C1/C2 proof")


def validate_metadata(errors: list[str]) -> None:
    try:
        kit = json.loads((ROOT / "kit.manifest.json").read_text(encoding="utf-8-sig"))
        index = json.loads((ROOT / "skills.index.json").read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        errors.append(f"package metadata load failed: {exc}")
        return
    if kit.get("version") != 6 or kit.get("runtime_truth_root") != ".devad/manager/loop-lite":
        errors.append("kit manifest does not name Loop Lite v6 runtime truth")
    if kit.get("schema") != "devad-x9-loop-codex-kit-v6" or index.get("schema") != "devad-x9-loop-kit-v6":
        errors.append("package metadata schema is not v6")


def validate_no_generated_cache(errors: list[str]) -> None:
    for root_name in ("skills", "scripts", "templates"):
        for path in (ROOT / root_name).rglob("*"):
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                errors.append(f"generated cache included: {path.relative_to(ROOT)}")
            if path.is_file() and "loop-lite" in path.parts and (path.name in {"loop.db", "loop.db-shm", "loop.db-wal"} or "runtime" in path.parts):
                errors.append(f"generated loop-lite runtime included: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    validate_manifest(errors)
    validate_skills(errors)
    validate_registry(errors)
    validate_template(errors)
    validate_loop_lite(errors)
    validate_metadata(errors)
    validate_no_generated_cache(errors)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("PASS: X9 Loop Lite v6 skills, registry, manifest, compact template, JSON, and links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
