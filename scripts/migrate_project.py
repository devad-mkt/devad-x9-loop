from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "x9-project" / ".devad"
ACTIVATION_NAME = "2026-07-13-x9-loop-lite-v6-activation.md"
OLD_REPORT_NAME = "2026-07-13-x9-loop-lite-v6-old-migration-report.md"
TASK_ID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
ROLES = ("LINX", "THINX", "WORKER", "READER", "CHUNK", "SIDE")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def run_git(repo: Path, *args: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return False, ""
    return result.returncode == 0, result.stdout.strip()


def git_fact(repo: Path) -> dict[str, Any]:
    branch_ok, branch = run_git(repo, "branch", "--show-current")
    head_ok, head = run_git(repo, "rev-parse", "HEAD")
    status_ok, status = run_git(repo, "status", "--short")
    return {
        "path": str(repo),
        "branch": branch if branch_ok and branch else "UNKNOWN",
        "head": head if head_ok else None,
        "git_status": "KNOWN" if status_ok else "UNKNOWN",
        "dirty": bool(status) if status_ok else None,
        "local_change_count": len(status.splitlines()) if status_ok and status else 0,
        "preservation": "PRESERVE",
    }


def _role_from_label(label: str) -> str | None:
    upper = label.upper()
    for role in ROLES:
        if re.search(rf"(?<![A-Z0-9]){role}(?![A-Z0-9])", upper):
            return role
    return None


def parse_current_roles(repo: Path) -> dict[str, dict[str, str]]:
    """Read current task identity from durable v5 files without trusting titles."""
    manager = repo / ".devad" / "manager"
    roles: dict[str, dict[str, str]] = {}

    registry = manager / "loop" / "ROLE_REGISTRY.json"
    if registry.is_file():
        try:
            payload = json.loads(registry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        tasks = payload.get("tasks", {}) if isinstance(payload, dict) else {}
        if isinstance(tasks, dict):
            for task_id, row in tasks.items():
                if not TASK_ID_RE.fullmatch(str(task_id)) or not isinstance(row, dict):
                    continue
                role = str(row.get("role", "")).upper()
                if role not in ROLES:
                    continue
                roles[str(task_id)] = {
                    "role": role,
                    "title": str(row.get("title", "")),
                    "lane_label": str(row.get("lane_label", "")),
                }

    workers = manager / "WORKERS.md"
    if workers.is_file():
        for line in workers.read_text(encoding="utf-8", errors="replace").splitlines():
            match = TASK_ID_RE.search(line)
            if not match:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            label = next((cell for cell in cells if cell and not TASK_ID_RE.search(cell)), "")
            role = _role_from_label(label)
            if role:
                roles.setdefault(
                    match.group(0),
                    {"role": role, "title": "", "lane_label": label},
                )

    lock = manager / "MANAGER_PASS_LOCK.md"
    if lock.is_file():
        for line in lock.read_text(encoding="utf-8", errors="replace").splitlines():
            match = TASK_ID_RE.search(line)
            if not match:
                continue
            label = line[: match.start()].strip().lstrip("-*").strip().rstrip(":").strip()
            role = _role_from_label(label)
            if not role:
                continue
            previous = roles.get(match.group(0), {})
            roles[match.group(0)] = {
                "role": role,
                "title": previous.get("title", ""),
                "lane_label": label,
            }

    return roles


def discovered_worktrees(repositories: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for repository in repositories:
        ok, output = run_git(repository, "worktree", "list", "--porcelain")
        paths: list[Path] = []
        if ok:
            for line in output.splitlines():
                if line.startswith("worktree "):
                    paths.append(Path(line.removeprefix("worktree ")).resolve())
        if not paths:
            paths.append(repository.resolve())
        for path in paths:
            key = str(path).replace("\\", "/").casefold()
            if key in seen:
                continue
            seen.add(key)
            fact = git_fact(path)
            fact["classification"] = "UNKNOWN"
            fact["reason"] = "Migration preserves checkout; age alone is not authority"
            records.append(fact)
    return records


def template_files() -> list[tuple[Path, Path]]:
    sources = [TEMPLATE / "ROUTER.md"]
    for state_name in ("loop-lite", "owner-packets"):
        state_root = TEMPLATE / "manager" / state_name
        sources.extend(
            path for path in state_root.rglob("*") if path.is_file()
        )
    pairs: list[tuple[Path, Path]] = []
    for source in sources:
        pairs.append((source, source.relative_to(TEMPLATE)))
    return sorted(pairs, key=lambda pair: pair[1].as_posix())


def activation_packet(repo: Path) -> str:
    return f"""# X9 Loop Lite v6 Activation Packet

Generated: {now()}
Repository: {repo}

Do not send automatically. Do not message the current Linx during shadow
validation.

1. Run read-only shadow reconciliation and verify all existing local work is
   preserved and classified.
2. Always reuse the existing Thinx task; do not create a replacement merely to change
   model effort.
3. Create one fresh Linx v6 only after package, snapshot, identity, ownership,
   callback, and recovery tests pass.
4. Fresh Linx v6 runs `loopctl.py reconcile`, reads only
   `manager/loop-lite/runtime/ACTION.json`, performs one transport action, and
   records the real delivery result.
5. Retire old Linx only after the new Linx acknowledges the exact snapshot.

No product code, worktree move, cleanup, reset, stash, deploy, or recurring
heartbeat is authorized by this packet.
"""


def old_report(repositories: list[Path]) -> str:
    rows = []
    for item in discovered_worktrees(repositories):
        dirty = "UNKNOWN" if item["dirty"] is None else ("DIRTY" if item["dirty"] else "CLEAN")
        rows.append(
            f"| {item['path']} | {item['branch']} | {dirty} | UNKNOWN | PRESERVE |"
        )
    return """# X9 Loop Lite v6 OLD Migration Report

Planning evidence only. No checkout was moved, deleted, cleaned, reset, or
stashed. Age was not used.

| Checkout | Branch | Local | Classification | Action |
| --- | --- | --- | --- | --- |
""" + "\n".join(rows) + "\n"


def planned(repo: Path) -> list[Path]:
    paths = [repo / ".devad" / relative for _, relative in template_files()]
    passes = repo / ".devad" / "manager" / "passes"
    paths.extend((passes / ACTIVATION_NAME, passes / OLD_REPORT_NAME))
    return paths


class UnsafeMigrationPathError(RuntimeError):
    pass


def canonical_lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(path))


def is_reparse_point(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise UnsafeMigrationPathError(f"cannot inspect {path}: {exc}") from exc

    attributes = getattr(metadata, "st_file_attributes", 0)
    if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
        return True
    is_junction = getattr(os.path, "isjunction", None)
    return path.is_symlink() or bool(is_junction and is_junction(path))


def safe_destination(repo: Path, path: Path) -> Path:
    root = canonical_lexical_path(repo)
    destination = canonical_lexical_path(path)
    try:
        relative = destination.relative_to(root)
    except ValueError as exc:
        raise UnsafeMigrationPathError(f"outside repository: {destination}") from exc

    current = root
    for component in relative.parts:
        current /= component
        if is_reparse_point(current):
            raise UnsafeMigrationPathError(f"linked component: {current}")
    return destination


def create_safe_parents(repo: Path, destination: Path) -> None:
    root = canonical_lexical_path(repo)
    relative_parent = destination.parent.relative_to(root)
    current = root
    for component in relative_parent.parts:
        current /= component
        if is_reparse_point(current):
            raise UnsafeMigrationPathError(f"linked component: {current}")
        if current.exists():
            if not current.is_dir():
                raise UnsafeMigrationPathError(f"non-directory parent: {current}")
            continue
        current.mkdir()
        if is_reparse_point(current):
            raise UnsafeMigrationPathError(f"linked component: {current}")

def write_new(repo: Path, path: Path, content: bytes) -> str:
    destination = safe_destination(repo, path)
    if destination.exists():
        return f"PRESERVE_EXISTING:{destination}"
    create_safe_parents(repo, destination)

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(destination, flags, 0o666)
    except FileExistsError:
        return f"PRESERVE_EXISTING:{destination}"
    except OSError as exc:
        raise UnsafeMigrationPathError(f"cannot create {destination}: {exc}") from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(content)
    return f"CREATED:{destination}"


def apply_overlay(repo: Path, extra_repos: list[Path]) -> list[str]:
    targets = planned(repo)
    for target in targets:
        safe_destination(repo, target)

    results: list[str] = []
    for source, relative in template_files():
        results.append(write_new(repo, repo / ".devad" / relative, source.read_bytes()))
    passes = repo / ".devad" / "manager" / "passes"
    results.append(
        write_new(repo, passes / ACTIVATION_NAME, activation_packet(repo).encode("utf-8"))
    )
    results.append(
        write_new(
            repo,
            passes / OLD_REPORT_NAME,
            old_report([repo, *extra_repos]).encode("utf-8"),
        )
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-destructive X9 Loop Lite v6 overlay")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--extra-repo", action="append", default=[], type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    extras = [path.resolve() for path in args.extra_repo]
    if not (repo / ".devad").is_dir():
        print(f"ERROR: missing .devad: {repo}", file=sys.stderr)
        return 2

    if not args.apply:
        print("DRY_RUN: no files changed")
        for path in planned(repo):
            action = "PRESERVE_EXISTING" if path.exists() else "WOULD_CREATE"
            print(f"{action}:{path}")
        return 0

    try:
        results = apply_overlay(repo, extras)
    except UnsafeMigrationPathError as exc:
        print(f"ERROR: unsafe migration path: {exc}", file=sys.stderr)
        return 2
    for result in results:
        print(result)
    print("ACTIVATION_NOT_SENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
