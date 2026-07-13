from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


FILES = {
    "ROLE_REGISTRY.json",
    "PASS_CAPSULE.json",
    "WORKTREE_INDEX.json",
    "TASK_GRAPH.json",
    "RESOURCE_CLAIMS.json",
    "EVENT_CURSOR.json",
    "DISPATCH_LEDGER.jsonl",
    "DECISION_GATES.json",
}


def load_contract():
    path = Path(__file__).with_name("loop_contract.py")
    spec = importlib.util.spec_from_file_location("x9_loop_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def validate(repo: Path) -> list[str]:
    errors: list[str] = []
    loop = repo / ".devad" / "manager" / "loop"
    if not loop.is_dir():
        return [f"MISSING_LOOP_ROOT:{loop}"]
    missing = sorted(FILES - {p.name for p in loop.iterdir() if p.is_file()})
    errors.extend(f"MISSING_LOOP_FILE:{name}" for name in missing)

    for name in sorted(FILES - {"DISPATCH_LEDGER.jsonl"}):
        path = loop / name
        if not path.is_file():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            errors.append(f"INVALID_JSON:{name}:{exc.lineno}")

    capsule = loop / "PASS_CAPSULE.json"
    if capsule.is_file() and capsule.stat().st_size >= 8192:
        errors.append(f"PASS_CAPSULE_TOO_LARGE:{capsule.stat().st_size}")

    registry = loop / "ROLE_REGISTRY.json"
    if registry.is_file():
        data = json.loads(registry.read_text(encoding="utf-8-sig"))
        errors.extend(load_contract().validate_role_registry(data))

    ledger = loop / "DISPATCH_LEDGER.jsonl"
    if ledger.is_file():
        for line_no, line in enumerate(ledger.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"INVALID_LEDGER_JSON:{line_no}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    errors = validate(args.repo.resolve())
    if errors:
        print("\n".join(errors))
        return 1
    print("PASS: X9 Loop state")
    return 0


if __name__ == "__main__":
    sys.exit(main())
