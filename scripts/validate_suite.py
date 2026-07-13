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


def validate_no_generated_cache(errors: list[str]) -> None:
    manifest = ROOT / "SOURCE_MANIFEST.sha256"
    if not manifest.is_file():
        return
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or "  " not in line:
            continue
        relative = line.split("  ", 1)[1]
        parts = Path(relative).parts
        if "__pycache__" in parts or Path(relative).suffix == ".pyc":
            errors.append(f"generated cache included in source manifest: {relative}")

def main() -> int:
    errors: list[str] = []
    validate_manifest(errors)
    validate_skills(errors)
    validate_registry(errors)
    validate_template(errors)
    validate_no_generated_cache(errors)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("PASS: X9 Loop v5 skills, registry, manifest, compact template, JSON, and links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
