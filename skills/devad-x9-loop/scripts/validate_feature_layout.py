#!/usr/bin/env python3
"""Validate managed X9 feature folders without touching legacy folders."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_feature_catalog import collect, parse_manifest, render_index, render_readme


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RELEASE_STATES = {
    "PLANNED_ONLY",
    "UNCOMMITTED",
    "SOURCE_ONLY",
    "V105_READY",
    "DEPLOYED",
    "LIVE_PROOF_PASS",
}
REQUIRED_FILES = {
    "README.md",
    "FEATURE.json",
    "spec/CONTRACT.md",
    "spec/PLAN.md",
    "spec/TASKS.md",
    "refs/ARTIFACTS.md",
}
LOCAL_LINK_RE = re.compile(r"(?:file://|[A-Za-z]:[\\/]|/Users/|/home/)", re.I)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate X9 feature layout.")
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    root = repo / ".devad" / "features"
    workers = repo / ".devad" / "manager" / "workers"
    errors: list[str] = []
    warnings: list[str] = []
    features = collect(repo)

    for item in features:
        feature_id = item["feature_id"]
        feature_root = repo / item["feature_root"]
        if not SLUG_RE.fullmatch(feature_id) or len(feature_id) > 24:
            errors.append(f"invalid feature id: {feature_id}")
        if feature_root.name != feature_id:
            errors.append(f"folder/id mismatch: {item['feature_root']}")
        if item["release_state"] not in RELEASE_STATES:
            errors.append(f"invalid release state: {feature_id}:{item['release_state']}")
        if item["implementation_branch"] in {"", "UNKNOWN"}:
            errors.append(f"missing implementation branch: {feature_id}")
        for required in REQUIRED_FILES:
            if not (feature_root / required).is_file():
                errors.append(f"missing {item['feature_root']}/{required}")

        for path in feature_root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(repo).as_posix()
            if len(relative) > 160:
                errors.append(f"path exceeds 160 characters: {relative}")
            depth = len(path.relative_to(root).parts)
            if depth > 6:
                errors.append(f"path exceeds six feature levels: {relative}")

        artifacts = feature_root / "refs" / "ARTIFACTS.md"
        if artifacts.is_file() and LOCAL_LINK_RE.search(
            artifacts.read_text(encoding="utf-8", errors="replace")
        ):
            errors.append(f"local-only artifact link: {artifacts.relative_to(repo)}")

        for lane in item["active_worker_lanes"]:
            manifest = workers / lane / "MANIFEST.md"
            if not manifest.is_file():
                errors.append(f"missing worker manifest: {lane}")
                continue
            fields = parse_manifest(manifest)
            required_fields = {
                "Packet schema": "X9-V2",
                "Feature ID": feature_id,
                "Feature root": item["feature_root"],
                "Artifact index": item["artifact_index"],
            }
            for field, expected in required_fields.items():
                actual = fields.get(field, "").strip("`")
                if actual != expected:
                    errors.append(f"{lane} {field}: expected {expected}, got {actual or 'MISSING'}")
            if not fields.get("Run ID"):
                errors.append(f"{lane} Run ID: MISSING")

    index_path = root / "features.index.json"
    readme_path = root / "README.md"
    expected_index = render_index(features)
    expected_readme = render_readme(features)
    if not index_path.is_file() or index_path.read_text(encoding="utf-8") != expected_index:
        errors.append("features.index.json is missing or stale")
    if not readme_path.is_file() or readme_path.read_text(encoding="utf-8") != expected_readme:
        errors.append("features/README.md is missing or stale")

    dockerignore = repo / ".dockerignore"
    if not dockerignore.is_file() or not any(
        line.strip().rstrip("/") == ".devad"
        for line in dockerignore.read_text(encoding="utf-8", errors="replace").splitlines()
    ):
        errors.append(".dockerignore does not exclude .devad")

    result = {
        "status": "PASS" if not errors else "BLOCKED",
        "managed_features": len(features),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
