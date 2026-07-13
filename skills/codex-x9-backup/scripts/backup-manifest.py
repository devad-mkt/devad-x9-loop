#!/usr/bin/env python3
import argparse
import fnmatch
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

EXCLUDE_DIR_NAMES = {
    ".git",
    "node_modules",
    "cache",
    ".cache",
    "tmp",
    ".tmp",
    ".sandbox",
    ".sandbox-bin",
    ".sandbox-secrets",
    "packages",
    ".plugin-appserver",
    "__pycache__",
}

EXCLUDE_FILE_GLOBS = [
    "auth.json",
    "cap_sid",
    "*.sqlite-wal",
    "*.sqlite-shm",
    "logs_*.sqlite",
    "*.log",
    ".env",
    ".env.*",
    "*cookie*",
    "*cookies*",
    "*.pyc",
]

INCLUDE_DIRS = [
    (".codex/sessions", "snapshot/dot-codex/sessions"),
    (".codex/archived_sessions", "snapshot/dot-codex/archived_sessions"),
    (".codex/skills", "snapshot/dot-codex/skills"),
    (".codex/skills-disabled", "snapshot/dot-codex/skills-disabled"),
    (".codex/memories", "snapshot/dot-codex/memories"),
    (".codex/rules", "snapshot/dot-codex/rules"),
    (".codex/automations", "snapshot/dot-codex/automations"),
    (".codex/state", "snapshot/dot-codex/state"),
    (".codex/tooling", "snapshot/dot-codex/tooling"),
    (".codex/attachments", "snapshot/dot-codex/attachments"),
    (".codex/generated_images", "snapshot/dot-codex/generated_images"),
    (".codex/recovered_project_chats", "snapshot/dot-codex/recovered_project_chats"),
    (".agents", "snapshot/dot-agents"),
    (".config/opencode", "snapshot/dot-config-opencode"),
]

INCLUDE_FILES = [
    (".codex/session_index.jsonl", "snapshot/dot-codex/session_index.jsonl"),
    (".codex/state_5.sqlite", "snapshot/dot-codex/state_5.sqlite"),
    (".codex/.codex-global-state.json", "snapshot/dot-codex/.codex-global-state.json"),
    (".codex/.codex-global-state.json.bak", "snapshot/dot-codex/.codex-global-state.json.bak"),
    (".codex/config.toml", "snapshot/dot-codex/config.toml"),
    (".codex/version.json", "snapshot/dot-codex/version.json"),
    (".codex/models_cache.json", "snapshot/dot-codex/models_cache.json"),
    (".codex/installation_id", "snapshot/dot-codex/installation_id"),
    (".codex/chrome-native-hosts.json", "snapshot/dot-codex/chrome-native-hosts.json"),
    (".codex/chrome-native-hosts-v2.json", "snapshot/dot-codex/chrome-native-hosts-v2.json"),
    (".codex/goals_1.sqlite", "snapshot/dot-codex/goals_1.sqlite"),
    (".codex/memories_1.sqlite", "snapshot/dot-codex/memories_1.sqlite"),
]


def posix_rel(path: Path) -> str:
    return path.as_posix()


def file_excluded(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & EXCLUDE_DIR_NAMES:
        return True
    name = path.name.lower()
    return any(fnmatch.fnmatch(name, pat.lower()) for pat in EXCLUDE_FILE_GLOBS)


def sha256_file(path: Path, limit_bytes: int = 64 * 1024 * 1024) -> str | None:
    try:
        if path.stat().st_size > limit_bytes:
            return None
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def file_info(path: Path, rel: str) -> dict:
    stat = path.stat()
    return {
        "path": rel,
        "bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256_file(path),
    }


def scan_tree(source_root: Path, dest_prefix: Path) -> dict:
    result = {
        "source": str(source_root),
        "dest": posix_rel(dest_prefix),
        "exists": source_root.exists(),
        "files": 0,
        "bytes": 0,
        "excluded_files": 0,
        "lfs_candidates": [],
    }
    if not source_root.exists():
        return result

    for root, dirs, files in os.walk(source_root):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIR_NAMES]
        for name in files:
            file_path = root_path / name
            rel_from_source = file_path.relative_to(source_root)
            dest_rel = dest_prefix / rel_from_source
            if file_excluded(rel_from_source):
                result["excluded_files"] += 1
                continue
            try:
                size = file_path.stat().st_size
            except OSError:
                result["excluded_files"] += 1
                continue
            result["files"] += 1
            result["bytes"] += size
            if size >= 90 * 1024 * 1024:
                result["lfs_candidates"].append({"path": posix_rel(dest_rel), "bytes": size})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-root", required=True)
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scan-source", action="store_true")
    parser.add_argument("--scan-snapshot", action="store_true")
    args = parser.parse_args()

    profile_root = Path(args.profile_root)
    repo_path = Path(args.repo_path)
    output = Path(args.output)

    if args.scan_snapshot:
        base = repo_path
        dir_pairs = [(repo_path / dest, Path(dest)) for _, dest in INCLUDE_DIRS]
        file_pairs = [(repo_path / dest, Path(dest)) for _, dest in INCLUDE_FILES]
    else:
        base = profile_root
        dir_pairs = [(profile_root / src, Path(dest)) for src, dest in INCLUDE_DIRS]
        file_pairs = [(profile_root / src, Path(dest)) for src, dest in INCLUDE_FILES]

    dirs = [scan_tree(src, dest) for src, dest in dir_pairs]
    important_files = []
    for src, dest in file_pairs:
        exists = src.exists() and not file_excluded(src.relative_to(base) if src.is_relative_to(base) else src)
        item = {"source": str(src), "path": posix_rel(dest), "exists": exists}
        if exists:
            item.update(file_info(src, posix_rel(dest)))
        important_files.append(item)

    excluded_probe = []
    for rel in [
        ".codex/auth.json",
        ".codex/cap_sid",
        ".codex/logs_2.sqlite",
        ".codex/state_5.sqlite-wal",
        ".codex/state_5.sqlite-shm",
        ".codex/.sandbox-secrets",
        ".config/opencode/node_modules",
    ]:
        excluded_probe.append({"source": str(profile_root / rel), "source_exists": (profile_root / rel).exists()})

    total_files = sum(d["files"] for d in dirs) + sum(1 for f in important_files if f["exists"])
    total_bytes = sum(d["bytes"] for d in dirs) + sum(f.get("bytes", 0) for f in important_files)
    lfs_candidates = []
    for d in dirs:
        lfs_candidates.extend(d["lfs_candidates"])
    for f in important_files:
        if f.get("bytes", 0) >= 90 * 1024 * 1024:
            lfs_candidates.append({"path": f["path"], "bytes": f["bytes"]})

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "profile_root": str(profile_root),
        "repo_path": str(repo_path),
        "scan_base": str(base),
        "summary": {
            "files": total_files,
            "bytes": total_bytes,
            "lfs_candidate_count": len(lfs_candidates),
        },
        "directories": dirs,
        "important_files": important_files,
        "lfs_candidates": lfs_candidates,
        "excluded_probe": excluded_probe,
        "exclude_dir_names": sorted(EXCLUDE_DIR_NAMES),
        "exclude_file_globs": EXCLUDE_FILE_GLOBS,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest={output}")
    print(f"files={total_files} bytes={total_bytes} lfs_candidates={len(lfs_candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
