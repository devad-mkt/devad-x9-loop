#!/usr/bin/env python3
"""Build the compact X9 feature index and human sitemap."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


BOLD_FIELD_RE = re.compile(r"^\*\*([^*]+?):\*\*\s*`?([^`\r\n]+)`?\s*$")
ITEM_FIELD_RE = re.compile(r"^-?\s*([^:*]+?):\s*`?([^`\r\n]+)`?\s*$")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_manifest(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not path.is_file():
        return fields
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        match = BOLD_FIELD_RE.match(line) or ITEM_FIELD_RE.match(line)
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def collect(repo: Path) -> list[dict[str, Any]]:
    features_root = repo / ".devad" / "features"
    workers_root = repo / ".devad" / "manager" / "workers"
    worker_links: dict[str, list[str]] = {}

    if workers_root.is_dir():
        for packet in sorted(p for p in workers_root.iterdir() if p.is_dir()):
            fields = parse_manifest(packet / "MANIFEST.md")
            feature_id = fields.get("Feature ID", "").strip("`")
            if feature_id and feature_id != "NONE":
                worker_links.setdefault(feature_id, []).append(packet.name)

    features: list[dict[str, Any]] = []
    if not features_root.is_dir():
        return features

    for feature_file in sorted(features_root.glob("*/FEATURE.json")):
        data = read_json(feature_file)
        feature_id = str(data.get("feature_id", feature_file.parent.name))
        declared = [str(v) for v in data.get("active_worker_lanes", [])]
        linked = worker_links.get(feature_id, [])
        lanes = sorted(set(declared + linked))
        features.append(
            {
                "feature_id": feature_id,
                "title": str(data.get("title", feature_id)),
                "release_state": str(data.get("release_state", "PLANNED_ONLY")),
                "feature_root": feature_file.parent.relative_to(repo).as_posix(),
                "implementation_branch": str(data.get("implementation_branch", "UNKNOWN")),
                "active_worker_lanes": lanes,
                "subfeatures": data.get("subfeatures", []),
                "artifact_index": str(
                    data.get(
                        "artifact_index",
                        f".devad/features/{feature_id}/refs/ARTIFACTS.md",
                    )
                ),
                "updated_at": str(data.get("updated_at", "UNKNOWN")),
            }
        )
    return sorted(features, key=lambda item: item["feature_id"])


def render_index(features: list[dict[str, Any]]) -> str:
    updated = max((str(item["updated_at"]) for item in features), default="UNKNOWN")
    payload = {
        "schema_version": 1,
        "generated_from": "managed FEATURE.json files and X9-V2 worker manifests",
        "updated_at": updated,
        "features": features,
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def render_readme(features: list[dict[str, Any]]) -> str:
    lines = [
        "# X9 Feature Map",
        "",
        "Generated from `FEATURE.json` files and X9-V2 Worker manifests.",
        "Do not hand-edit the table. Legacy folders remain valid but are not",
        "managed until they receive a `FEATURE.json` file.",
        "",
        "| Feature | State | Branch | Workers | Root |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in features:
        workers = ", ".join(item["active_worker_lanes"]) or "NONE"
        lines.append(
            f"| {item['feature_id']} | {item['release_state']} | "
            f"{item['implementation_branch']} | {workers} | "
            f"`{item['feature_root']}` |"
        )
    if not features:
        lines.append("| NONE | PLANNED_ONLY | UNKNOWN | NONE | NONE |")
    lines.extend(
        [
            "",
            "## Rules",
            "",
            "- Feature folders are stable; Worker folders are temporary.",
            "- Worker packets link to features. They are not copied here.",
            "- Important Markdown and JSON stay in private Git.",
            "- Large evidence uses an immutable URL or Git LFS plus SHA-256.",
            "- Local-only artifact links are forbidden.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_if_changed(path: Path, content: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.is_file() else None
    if current == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the X9 feature catalog.")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    features = collect(repo)
    index_path = repo / ".devad" / "features" / "features.index.json"
    readme_path = repo / ".devad" / "features" / "README.md"
    index = render_index(features)
    readme = render_readme(features)
    changes = {
        index_path.relative_to(repo).as_posix(): not index_path.is_file()
        or index_path.read_text(encoding="utf-8") != index,
        readme_path.relative_to(repo).as_posix(): not readme_path.is_file()
        or readme_path.read_text(encoding="utf-8") != readme,
    }

    if args.write:
        write_if_changed(index_path, index)
        write_if_changed(readme_path, readme)

    print(
        json.dumps(
            {
                "status": "PASS",
                "mode": "write" if args.write else "dry-run",
                "feature_count": len(features),
                "changes": changes,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
