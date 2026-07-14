#!/usr/bin/env python3
"""Deterministic, local controller for the bounded X9 Loop Lite v6 state."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Callable


class LoopError(RuntimeError):
    pass


class SnapshotExportError(LoopError):
    pass


class StateNotDurableError(LoopError):
    pass


class IdentityError(LoopError):
    pass


class ClaimConflictError(LoopError):
    pass


class ResourceConflictError(LoopError):
    pass


class TaskNotReadyError(LoopError):
    pass


class DeliveryError(LoopError):
    pass


class StaleCompletionError(LoopError):
    pass


class ScopeBreachError(LoopError):
    pass


class GitStateError(LoopError):
    pass

SCHEMA = "x9-loop-lite-snapshot-v1"
SNAPSHOT_TABLES = (
    "actors", "worktrees", "tasks", "claims", "resources", "dispatches",
    "deliveries", "events", "gates", "outbox", "metrics",
)


SNAPSHOT_COLUMNS = {
    "actors": ("actor_id", "role", "title", "model"),
    "worktrees": ("worktree_id", "path", "repository_id"),
    "tasks": ("task_id", "worker_id", "worktree_id", "base_sha", "owner_packet_path", "owner_packet_sha256", "dependencies", "finish_line", "status"),
    "claims": ("task_id", "path", "kind"), "resources": ("task_id", "resource"),
    "dispatches": ("dispatch_id", "task_id", "sender_id", "target_id", "packet_sha256", "packet", "supersedes", "status", "created_at"),
    "deliveries": ("id", "dispatch_id", "phase", "method", "result", "created_at"),
    "events": ("event_id", "task_id", "dispatch_id", "event_sha256", "created_at"),
    "gates": ("task_id", "name", "status", "note"), "outbox": ("dispatch_id", "payload"), "metrics": ("key", "value"),
}
COMPLETED_TASK_ID_CAP = 16
GIT_TIMEOUT_SECONDS = 10
def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def coding_limit(successful_dispatches: int, metrics: dict[str, Any]) -> int:
    failure_keys = (
        "lost_work", "duplicate_delivery", "stale_completion", "scope_breach",
        "parser_failure", "orphan_lock", "false_pass", "context_compaction",
    )
    if any(int(metrics.get(key, 0) or 0) for key in failure_keys):
        return 1
    if successful_dispatches >= 10:
        return 3
    if successful_dispatches >= 3:
        return 2
    return 1


class Controller:
    def __init__(self, repo: Path | str, now_fn: Callable[[], str] | None = None):
        self.repo = Path(repo).resolve()
        self.root = self.repo / ".devad" / "manager" / "loop-lite"
        self.db_path = self.root / "loop.db"
        self.snapshot_path = self.root / "SNAPSHOT.json"
        self.action_path = self.root / "runtime" / "ACTION.json"
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"))

    @staticmethod
    def _resolve_under(root: Path, path: Path) -> Path:
        resolved_root = root.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
        resolved_path.relative_to(resolved_root)
        return resolved_path

    @staticmethod
    def _is_reparse(path: Path) -> bool:
        metadata = path.lstat()
        attributes = int(getattr(metadata, "st_file_attributes", 0) or 0)
        reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        return stat.S_ISLNK(metadata.st_mode) or bool(attributes & reparse_flag)

    def _safe_state_path(
        self, path: Path, *, create_parents: bool = False, directory: bool = False
    ) -> Path:
        candidate = Path(os.path.abspath(path))
        try:
            relative = candidate.relative_to(self.repo)
        except ValueError as exc:
            raise LoopError("STATE_PATH_UNSAFE") from exc
        parent_parts = relative.parts if directory else relative.parts[:-1]
        current = self.repo
        for part in parent_parts:
            current = current / part
            if os.path.lexists(current):
                if self._is_reparse(current) or not current.is_dir():
                    raise LoopError("STATE_PATH_UNSAFE")
            elif create_parents:
                try:
                    current.mkdir()
                except FileExistsError:
                    pass
                if not os.path.lexists(current) or self._is_reparse(current) or not current.is_dir():
                    raise LoopError("STATE_PATH_UNSAFE")
            else:
                break
            try:
                current.resolve(strict=True).relative_to(self.repo)
            except (OSError, ValueError, RuntimeError) as exc:
                raise LoopError("STATE_PATH_UNSAFE") from exc
        if os.path.lexists(candidate):
            if self._is_reparse(candidate):
                raise LoopError("STATE_PATH_UNSAFE")
            try:
                candidate.resolve(strict=True).relative_to(self.repo)
            except (OSError, ValueError, RuntimeError) as exc:
                raise LoopError("STATE_PATH_UNSAFE") from exc
        return candidate

    def _atomic_state_write(self, path: Path, data: bytes) -> None:
        target = self._safe_state_path(path, create_parents=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        self._safe_state_path(temporary, create_parents=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= int(getattr(os, "O_NOFOLLOW", 0) or 0)
        descriptor = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            self._safe_state_path(temporary)
            os.replace(temporary, target)
            self._safe_state_path(target)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if os.path.lexists(temporary):
                try:
                    temporary.unlink()
                except OSError:
                    pass

    def _connect(self) -> sqlite3.Connection:
        self._safe_state_path(self.db_path, create_parents=True)
        connection = sqlite3.connect(self.db_path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    @staticmethod
    def _schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS actors (
              actor_id TEXT PRIMARY KEY, role TEXT NOT NULL, title TEXT NOT NULL, model TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS worktrees (
              worktree_id TEXT PRIMARY KEY, path TEXT NOT NULL, repository_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
              task_id TEXT PRIMARY KEY, worker_id TEXT NOT NULL REFERENCES actors(actor_id),
              worktree_id TEXT NOT NULL REFERENCES worktrees(worktree_id), base_sha TEXT NOT NULL, owner_packet_path TEXT NOT NULL, owner_packet_sha256 TEXT NOT NULL,
               dependencies TEXT NOT NULL, finish_line TEXT NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claims (
              task_id TEXT NOT NULL REFERENCES tasks(task_id), path TEXT NOT NULL, kind TEXT NOT NULL,
              PRIMARY KEY(task_id, path)
            );
            CREATE TABLE IF NOT EXISTS resources (
              task_id TEXT NOT NULL REFERENCES tasks(task_id), resource TEXT NOT NULL,
              PRIMARY KEY(task_id, resource)
            );
            CREATE TABLE IF NOT EXISTS dispatches (
              dispatch_id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(task_id),
              sender_id TEXT NOT NULL REFERENCES actors(actor_id), target_id TEXT NOT NULL REFERENCES actors(actor_id),
              packet_sha256 TEXT NOT NULL, packet TEXT NOT NULL, supersedes TEXT, status TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS deliveries (
              id INTEGER PRIMARY KEY AUTOINCREMENT, dispatch_id TEXT NOT NULL REFERENCES dispatches(dispatch_id),
              phase TEXT NOT NULL, method TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(task_id),
              dispatch_id TEXT NOT NULL REFERENCES dispatches(dispatch_id), event_sha256 TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS gates (
              task_id TEXT NOT NULL REFERENCES tasks(task_id), name TEXT NOT NULL, status TEXT NOT NULL,
              note TEXT NOT NULL, PRIMARY KEY(task_id, name)
            );
            CREATE TABLE IF NOT EXISTS outbox (
              dispatch_id TEXT PRIMARY KEY REFERENCES dispatches(dispatch_id), payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS metrics (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """
        )
        connection.execute("INSERT OR IGNORE INTO meta(key, value) VALUES('generation', '0')")

    def _generation(self, connection: sqlite3.Connection) -> int:
        return int(connection.execute("SELECT value FROM meta WHERE key='generation'").fetchone()[0])

    @staticmethod
    def _metric_json_list(connection: sqlite3.Connection, key: str) -> list[str]:
        row = connection.execute("SELECT value FROM metrics WHERE key=?", (key,)).fetchone()
        if not row:
            return []
        try:
            value = json.loads(row[0])
        except (TypeError, json.JSONDecodeError) as exc:
            raise StateNotDurableError("METRIC_STATE_INVALID") from exc
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise StateNotDurableError("METRIC_STATE_INVALID")
        return value

    def _completed_task_ids(self, connection: sqlite3.Connection) -> list[str]:
        return self._metric_json_list(connection, "completed_task_ids")

    def _remember_completed_task(self, connection: sqlite3.Connection, task_id: str) -> None:
        values = [task_id, *(item for item in self._completed_task_ids(connection) if item != task_id)]
        connection.execute(
            "INSERT INTO metrics(key,value) VALUES('completed_task_ids',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (_json(values[:COMPLETED_TASK_ID_CAP]),),
        )

    def _mutate(self, operation: Callable[[sqlite3.Connection], Any]) -> Any:
        connection = self._connect()
        try:
            self._schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            result = operation(connection)
            generation = self._generation(connection) + 1
            connection.execute("UPDATE meta SET value=? WHERE key='generation'", (str(generation),))
            preview = _json(self._snapshot_data(connection)).encode("utf-8")
            if len(preview) >= 8192:
                raise SnapshotExportError("SNAPSHOT_TOO_LARGE")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        try:
            self._write_snapshot()
        except Exception as exc:
            raise SnapshotExportError("SNAPSHOT_EXPORT_FAILED") from exc
        return result

    def _rows(self, connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")]

    def _snapshot_data(self, connection: sqlite3.Connection | None = None) -> dict[str, Any]:
        owns_connection = connection is None
        connection = connection or self._connect()
        try:
            if owns_connection:
                self._schema(connection)
            active_tasks = [dict(row) for row in connection.execute("SELECT * FROM tasks WHERE status != 'COMPLETE' ORDER BY task_id")]
            active_ids = [row["task_id"] for row in active_tasks]
            active_dispatches = [
                dict(row)
                for row in connection.execute(
                    "SELECT d.* FROM dispatches d JOIN tasks t ON t.task_id=d.task_id "
                    "WHERE t.status != 'COMPLETE' AND (d.status IN ('PREPARED','DISPATCHED') "
                    "OR (t.status='THINX_REVIEW_REQUIRED' AND d.rowid=("
                    "SELECT MAX(d2.rowid) FROM dispatches d2 WHERE d2.task_id=d.task_id))) "
                    "ORDER BY d.dispatch_id"
                )
            ]
            actor_ids = {row["worker_id"] for row in active_tasks}
            actor_ids.update(row[0] for row in connection.execute("SELECT actor_id FROM actors WHERE role IN ('LINX','THINX')"))
            actor_ids.update(row["sender_id"] for row in active_dispatches)
            actor_ids.update(row["target_id"] for row in active_dispatches)
            worktree_ids = {row["worktree_id"] for row in active_tasks}
            def selected(table: str, column: str, values: set[str]) -> list[dict[str, Any]]:
                if not values:
                    return []
                placeholders = ",".join("?" for _ in values)
                return [dict(row) for row in connection.execute(f"SELECT * FROM {table} WHERE {column} IN ({placeholders}) ORDER BY 1", tuple(sorted(values)))]
            active_dispatch_ids = {row["dispatch_id"] for row in active_dispatches}
            prepared_ids = {row["dispatch_id"] for row in active_dispatches if row["status"] == "PREPARED"}
            dispatch_attempts = {}
            for row in selected("outbox", "dispatch_id", prepared_ids):
                try:
                    dispatch_attempts[row["dispatch_id"]] = int(json.loads(row["payload"]).get("attempt", 1))
                except (TypeError, ValueError, json.JSONDecodeError):
                    dispatch_attempts[row["dispatch_id"]] = 1
            referenced_complete: list[str] = []
            for task in active_tasks:
                for dependency in json.loads(task["dependencies"]):
                    row = connection.execute("SELECT status FROM tasks WHERE task_id=?", (dependency,)).fetchone()
                    if row and row[0] == "COMPLETE" and dependency not in referenced_complete:
                        referenced_complete.append(dependency)
            if len(referenced_complete) > COMPLETED_TASK_ID_CAP:
                raise SnapshotExportError("COMPLETED_DEPENDENCY_CAP")
            recent_complete = [row[0] for row in connection.execute("SELECT task_id FROM tasks WHERE status='COMPLETE' ORDER BY rowid DESC LIMIT ?", (COMPLETED_TASK_ID_CAP,))]
            completed_task_ids: list[str] = []
            for item in [*referenced_complete, *recent_complete, *self._completed_task_ids(connection)]:
                if item not in completed_task_ids:
                    completed_task_ids.append(item)
            completed_task_ids = completed_task_ids[:COMPLETED_TASK_ID_CAP]
            recovery_worktrees = [dict(row) for row in connection.execute("SELECT worktree_id,path FROM worktrees ORDER BY worktree_id")]
            active_metric_keys = {f"blocked:{task_id}" for task_id in active_ids}
            metrics = [
                dict(row) for row in connection.execute("SELECT * FROM metrics WHERE key != 'completed_task_ids' ORDER BY key")
                if not row["key"].startswith("blocked:") or row["key"] in active_metric_keys
            ]
            return {
                "schema": SCHEMA, "generation": self._generation(connection), "recovery_worktrees": recovery_worktrees,
                "dispatch_attempts": dispatch_attempts,
                "completed_task_ids": completed_task_ids,
                "tables": {
                    "actors": selected("actors", "actor_id", actor_ids), "worktrees": selected("worktrees", "worktree_id", worktree_ids),
                    "tasks": active_tasks, "claims": selected("claims", "task_id", set(active_ids)),
                    "resources": selected("resources", "task_id", set(active_ids)), "dispatches": active_dispatches,
                    "deliveries": selected("deliveries", "dispatch_id", active_dispatch_ids), "events": [],
                    "gates": selected("gates", "task_id", set(active_ids)),
                    "outbox": [], "metrics": metrics,
                },
            }
        finally:
            if owns_connection:
                connection.close()
    def _recovery_evidence(self, worktrees: list[dict[str, str]], strict: bool) -> dict[str, Any]:
        evidence: dict[str, Any] = {"worktrees": 0, "receipts": 0, "git_paths": 0, "receipt_sha256": "", "issues": []}
        receipt_hashes: list[str] = []
        for row in worktrees:
            root = Path(row["path"])
            if not root.is_dir():
                if strict:
                    raise SnapshotExportError("RECOVERY_WORKTREE_MISSING")
                evidence["issues"].append(f"WORKTREE_MISSING:{row['worktree_id']}")
                continue
            evidence["worktrees"] += 1
            receipts = root / ".devad" / "workers"
            if receipts.is_dir():
                for receipt_path in receipts.glob("*/receipts/*.json"):
                    try:
                        resolved_receipt = self._resolve_under(root, receipt_path)
                        data = resolved_receipt.read_bytes()
                        receipt = json.loads(data.decode("utf-8"))
                        relative = self._normal_path(resolved_receipt.relative_to(root.resolve()).as_posix())
                        parts = PurePosixPath(relative).parts
                        if (len(parts) != 5 or parts[0:2] != (".devad", "workers")
                                or parts[3] != "receipts" or resolved_receipt.stem != receipt.get("event_id")
                                or receipt.get("schema") not in {"x9-loop-lite-result-v1", "x9-loop-lite-thinx-decision-v1"}):
                            raise ValueError("receipt shape")
                        receipt_hashes.append(hashlib.sha256(data).hexdigest())
                        evidence["receipts"] += 1
                    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, ScopeBreachError, AttributeError):
                        if strict:
                            raise SnapshotExportError("RECOVERY_RECEIPT_INVALID")
                        evidence["issues"].append(f"RECEIPT_INVALID:{receipt_path}")
            try:
                for arguments in (["diff", "--cached", "--name-only"], ["diff", "--name-only"], ["ls-files", "--others", "--exclude-standard"]):
                    evidence["git_paths"] += len(self._git_paths(arguments, root))
            except GitStateError:
                if strict:
                    raise SnapshotExportError("RECOVERY_GIT_STATE_UNKNOWN")
                evidence["issues"].append(f"GIT_STATE_UNKNOWN:{row['worktree_id']}")
        evidence["receipt_sha256"] = _sha(sorted(receipt_hashes))
        return evidence
    def _write_snapshot(self) -> None:
        data = _json(self._snapshot_data()).encode("utf-8")
        if len(data) >= 8192:
            raise OSError("SNAPSHOT_TOO_LARGE")
        self._atomic_state_write(self.snapshot_path, data)

    def _controller_snapshot_evidence(
        self, worktree_root: Path, connection: sqlite3.Connection | None = None
    ) -> set[str]:
        try:
            if worktree_root.resolve(strict=True) != self.repo:
                return set()
        except (OSError, RuntimeError):
            return set()
        self._safe_state_path(self.snapshot_path)
        if not self.snapshot_path.is_file():
            return set()
        expected = _json(self._snapshot_data(connection)).encode("utf-8")
        if self.snapshot_path.read_bytes() != expected:
            return set()
        return {self._normal_path(self.snapshot_path.relative_to(self.repo).as_posix())}

    def _controller_snapshot_tamper(self, worktree_root: Path) -> set[str]:
        try:
            same_repo = worktree_root.resolve(strict=True) == self.repo
        except (OSError, RuntimeError):
            return set()
        if not same_repo or not os.path.lexists(self.snapshot_path):
            return set()
        relative = self._normal_path(self.snapshot_path.relative_to(self.repo).as_posix())
        return set() if self._controller_snapshot_evidence(worktree_root) else {relative}

    def _assert_durable(self) -> None:
        self._safe_state_path(self.snapshot_path)
        if not self.snapshot_path.is_file():
            raise StateNotDurableError("SNAPSHOT_STALE")
        snapshot = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        connection = self._connect()
        try:
            if snapshot.get("generation") != self._generation(connection):
                raise StateNotDurableError("SNAPSHOT_STALE")
        finally:
            connection.close()

    def init(self, import_v5: bool = False) -> dict[str, Any]:
        self._safe_state_path(self.root, create_parents=True, directory=True)
        self._safe_state_path(self.action_path, create_parents=True)
        connection = self._connect()
        try:
            self._schema(connection)
        finally:
            connection.close()
        imported = {"actors": 0, "worktrees": 0, "tasks": 0, "claims": 0, "gates": 0}
        skipped = 0
        if import_v5:
            legacy = self.repo / ".devad" / "manager" / "loop"
            def load(name: str) -> dict[str, Any]:
                try:
                    value = json.loads((legacy / name).read_text(encoding="utf-8"))
                    return value if isinstance(value, dict) else {}
                except (OSError, json.JSONDecodeError):
                    return {}
            registry = load("ROLE_REGISTRY.json").get("tasks", {})
            worktrees = load("WORKTREE_INDEX.json").get("worktrees", {})
            graph = load("TASK_GRAPH.json").get("tasks", {})
            claims = load("RESOURCE_CLAIMS.json").get("tasks", {})
            gates = load("DECISION_GATES.json").get("tasks", {})
            def migrate(connection: sqlite3.Connection) -> dict[str, Any]:
                nonlocal skipped
                for actor_id, row in registry.items() if isinstance(registry, dict) else ():
                    role = row.get("role") if isinstance(row, dict) else None
                    if not isinstance(role, str) or role.upper() not in {"LINX", "THINX", "WORKER", "READER", "CHUNK", "SIDE"}:
                        skipped += 1
                        continue
                    cursor = connection.execute("INSERT OR IGNORE INTO actors(actor_id,role,title,model) VALUES(?,?,?,?)", (actor_id, role.upper(), str(row.get("title", "")), str(row.get("model", "Unknown"))))
                    imported["actors"] += cursor.rowcount
                for worktree_id, row in worktrees.items() if isinstance(worktrees, dict) else ():
                    if not isinstance(row, dict) or not row.get("path") or not row.get("repository_id"):
                        skipped += 1
                        continue
                    normalized_worktree = str(Path(row["path"]).resolve())
                    cursor = connection.execute("INSERT OR IGNORE INTO worktrees(worktree_id,path,repository_id) VALUES(?,?,?)", (worktree_id, normalized_worktree, str(row["repository_id"])))
                    imported["worktrees"] += cursor.rowcount
                    count_key, root_key = self._receipt_metric_keys(normalized_worktree)
                    connection.execute("INSERT OR IGNORE INTO metrics(key,value) VALUES(?,'0')", (count_key,))
                    connection.execute("INSERT OR IGNORE INTO metrics(key,value) VALUES(?,?)", (root_key, _sha([])))
                for task_id, row in graph.items() if isinstance(graph, dict) else ():
                    if not isinstance(row, dict):
                        skipped += 1
                        continue
                    worker_id, worktree_id, base_sha = row.get("worker_id"), row.get("worktree_id"), row.get("base_sha")
                    actor = connection.execute("SELECT role FROM actors WHERE actor_id=?", (worker_id,)).fetchone()
                    worktree = connection.execute("SELECT 1 FROM worktrees WHERE worktree_id=?", (worktree_id,)).fetchone()
                    if not isinstance(base_sha, str) or not actor or actor[0] != "WORKER" or not worktree:
                        skipped += 1
                        continue
                    cursor = connection.execute("INSERT OR IGNORE INTO tasks(task_id,worker_id,worktree_id,base_sha,owner_packet_path,owner_packet_sha256,dependencies,finish_line,status) VALUES(?,?,?,?,?,?,?,?,?)", (task_id, worker_id, worktree_id, base_sha, "", "", _json(row.get("dependencies", [])), str(row.get("finish_line", "")), "REGISTERED"))
                    if not cursor.rowcount:
                        continue
                    imported["tasks"] += 1
                    connection.execute("INSERT OR REPLACE INTO gates(task_id,name,status,note) VALUES(?,?,?,?)", (task_id, "OWNER_PACKET_MISSING", "BLOCKED", "legacy task requires owner packet"))
                    claim_row = claims.get(task_id, {}) if isinstance(claims, dict) else {}
                    for item in claim_row.get("claims", []) if isinstance(claim_row, dict) else []:
                        try:
                            connection.execute("INSERT INTO claims(task_id,path,kind) VALUES(?,?,?)", (task_id, self._normal_path(item["path"]), str(item.get("kind", "file")).casefold()))
                            imported["claims"] += 1
                        except (KeyError, ScopeBreachError):
                            skipped += 1
                    for resource in claim_row.get("resources", []) if isinstance(claim_row, dict) else []:
                        connection.execute("INSERT OR IGNORE INTO resources(task_id,resource) VALUES(?,?)", (task_id, str(resource).casefold()))
                    gate_row = gates.get(task_id, {}) if isinstance(gates, dict) else {}
                    for name, gate in gate_row.get("gates", {}).items() if isinstance(gate_row, dict) else []:
                        if isinstance(gate, dict) and isinstance(gate.get("status"), str):
                            connection.execute("INSERT OR REPLACE INTO gates(task_id,name,status,note) VALUES(?,?,?,?)", (task_id, name, gate["status"].upper(), str(gate.get("note", ""))))
                            imported["gates"] += 1
                return imported
            self._mutate(migrate)
        else:
            self._write_snapshot()
        self._write_views()
        return {"status": "PASS", "imported": imported, "skipped": skipped}

    def _normal_path(self, value: str) -> str:
        if not isinstance(value, str):
            raise ScopeBreachError("INVALID_PATH")
        raw = value.strip().replace("\\", "/")
        if (not raw or raw in {".", ".."} or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw)
                or any(character in raw for character in "*?[]{}")):
            raise ScopeBreachError(f"INVALID_PATH:{value}")
        path = PurePosixPath(raw)
        if any(part in {"", ".", ".."} for part in path.parts):
            raise ScopeBreachError(f"INVALID_PATH:{value}")
        canonical = str(path)
        if canonical in {"", "."}:
            raise ScopeBreachError(f"INVALID_PATH:{value}")
        return canonical.casefold()

    @staticmethod
    def _claim_kind(value: Any) -> str:
        kind = str(value).casefold()
        if kind not in {"file", "dir"}:
            raise ScopeBreachError(f"INVALID_CLAIM_KIND:{value}")
        return kind
    @staticmethod
    def _overlap(path_a: str, kind_a: str, path_b: str, kind_b: str) -> bool:
        if path_a == path_b:
            return True
        return (kind_a == "dir" and path_b.startswith(path_a + "/")) or (
            kind_b == "dir" and path_a.startswith(path_b + "/")
        )

    @staticmethod
    def _receipt_metric_keys(worktree_path: str | Path) -> tuple[str, str]:
        canonical = str(Path(worktree_path).resolve()).replace("\\", "/").casefold()
        scope = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
        return f"receipt-count:{scope}", f"receipt-root:{scope}"

    def _receipt_state(self, connection: sqlite3.Connection, worktree_path: str | Path) -> tuple[int, str]:
        count_key, root_key = self._receipt_metric_keys(worktree_path)
        count_row = connection.execute("SELECT value FROM metrics WHERE key=?", (count_key,)).fetchone()
        root_row = connection.execute("SELECT value FROM metrics WHERE key=?", (root_key,)).fetchone()
        if not count_row and not root_row:
            return 0, _sha([])
        try:
            count = int(count_row[0]) if count_row else -1
            root = str(root_row[0]) if root_row else ""
        except (TypeError, ValueError) as exc:
            raise StateNotDurableError("RECEIPT_SET_INVALID") from exc
        if count < 0 or not re.fullmatch(r"[0-9a-f]{64}", root):
            raise StateNotDurableError("RECEIPT_SET_INVALID")
        return count, root

    def _set_receipt_state(
        self, connection: sqlite3.Connection, worktree_id: str, hashes: list[str]
    ) -> None:
        worktree = connection.execute(
            "SELECT path FROM worktrees WHERE worktree_id=?", (worktree_id,)
        ).fetchone()
        if not worktree:
            raise StateNotDurableError("RECEIPT_WORKTREE_UNKNOWN")
        count_key, root_key = self._receipt_metric_keys(worktree["path"])
        values = sorted(hashes)
        connection.execute(
            "INSERT INTO metrics(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (count_key, str(len(values))),
        )
        connection.execute(
            "INSERT INTO metrics(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (root_key, _sha(values)),
        )

    def _validated_receipt_entries(
        self, worktree_root: Path, connection: sqlite3.Connection | None = None,
        exclude_paths: set[str] | None = None,
    ) -> dict[str, str]:
        owns_connection = connection is None
        connection = connection or self._connect()
        try:
            resolved_root = worktree_root.resolve(strict=True)
            registered = False
            for row in connection.execute("SELECT worktree_id,path FROM worktrees"):
                try:
                    if Path(row["path"]).resolve(strict=True) == resolved_root:
                        registered = True
                        break
                except (OSError, RuntimeError):
                    continue
            if not registered:
                raise StateNotDurableError("RECEIPT_WORKTREE_UNKNOWN")
            expected_count, expected_root = self._receipt_state(connection, resolved_root)
            excluded = {self._normal_path(path) for path in (exclude_paths or set())}
            entries: dict[str, str] = {}
            receipts = resolved_root / ".devad" / "workers"
            for candidate in receipts.glob("*/receipts/*.json") if receipts.is_dir() else ():
                try:
                    resolved = self._resolve_under(resolved_root, candidate)
                    relative = self._normal_path(resolved.relative_to(resolved_root).as_posix())
                    if relative in excluded:
                        continue
                    data = resolved.read_bytes()
                    receipt = json.loads(data.decode("utf-8"))
                    parts = PurePosixPath(relative).parts
                    actor = receipt.get("worker_id") or receipt.get("actor_id")
                    if (len(parts) != 5 or parts[0:2] != (".devad", "workers")
                            or parts[3] != "receipts" or parts[2] != actor
                            or resolved.stem != receipt.get("event_id")
                            or receipt.get("schema") not in {"x9-loop-lite-result-v1", "x9-loop-lite-thinx-decision-v1"}):
                        raise ValueError("receipt shape")
                    entries[relative] = hashlib.sha256(data).hexdigest()
                except (OSError, ValueError, RuntimeError, json.JSONDecodeError, ScopeBreachError, AttributeError) as exc:
                    raise StateNotDurableError("RECEIPT_SET_MISMATCH") from exc
            hashes = sorted(entries.values())
            if len(hashes) != expected_count or _sha(hashes) != expected_root:
                raise StateNotDurableError("RECEIPT_SET_MISMATCH")
            return entries
        finally:
            if owns_connection:
                connection.close()

    def register_actor(self, actor_id: str, role: str, title: str, model: str) -> dict[str, Any]:
        role = role.upper()
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            old = connection.execute("SELECT role FROM actors WHERE actor_id=?", (actor_id,)).fetchone()
            if old and old[0] != role:
                raise IdentityError("ROLE_IMMUTABLE")
            connection.execute(
                "INSERT OR IGNORE INTO actors(actor_id,role,title,model) VALUES(?,?,?,?)",
                (actor_id, role, title, model),
            )
            warnings = []
            for known in ("LINX", "THINX", "WORKER", "READER", "CHUNK", "SIDE"):
                if known != role and re.search(rf"(?<![A-Za-z0-9]){re.escape(known)}(?![A-Za-z0-9])", title, re.IGNORECASE):
                    warnings.append(f"TITLE_ROLE_MISMATCH:{actor_id}:{role}:{title}")
                    break
            return {"status": "REGISTERED", "warnings": warnings}
        return self._mutate(operation)

    def register_worktree(self, worktree_id: str, path: Path | str, repository_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", worktree_id):
            raise IdentityError("WORKTREE_ID_INVALID")
        normalized = str(Path(path).resolve())
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            old = connection.execute("SELECT path,repository_id FROM worktrees WHERE worktree_id=?", (worktree_id,)).fetchone()
            if old and (str(Path(old["path"]).resolve()) != normalized or old["repository_id"] != repository_id):
                raise IdentityError("WORKTREE_IMMUTABLE")
            connection.execute(
                "INSERT OR IGNORE INTO worktrees(worktree_id,path,repository_id) VALUES(?,?,?)",
                (worktree_id, normalized, repository_id),
            )
            count_key, root_key = self._receipt_metric_keys(normalized)
            connection.execute("INSERT OR IGNORE INTO metrics(key,value) VALUES(?,'0')", (count_key,))
            connection.execute("INSERT OR IGNORE INTO metrics(key,value) VALUES(?,?)", (root_key, _sha([])))
            return {"status": "REGISTERED", "worktree_id": worktree_id}
        return self._mutate(operation)

    def register_task(self, task_id: str, worker_id: str, worktree_id: str, base_sha: str,
                      claims: list[dict[str, str]], resources: list[str], dependencies: list[str],
                      finish_line: str, owner_packet_path: str | None = None, owner_packet_sha256: str | None = None) -> dict[str, Any]:
        if not isinstance(owner_packet_path, str) or not isinstance(owner_packet_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", owner_packet_sha256):
            raise IdentityError("OWNER_PACKET_REQUIRED")
        owner_packet_path = self._normal_path(owner_packet_path)
        normalized_claims = [(self._normal_path(item["path"]), self._claim_kind(item.get("kind", "file"))) for item in claims]
        normalized_resources = [item.casefold() for item in resources]
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            existing_task = connection.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if existing_task or task_id in self._completed_task_ids(connection):
                raise IdentityError("TASK_ID_RETIRED" if (not existing_task or existing_task["status"] == "COMPLETE") else "TASK_ID_EXISTS")
            actor = connection.execute("SELECT role FROM actors WHERE actor_id=?", (worker_id,)).fetchone()
            if not actor or actor[0] != "WORKER":
                raise IdentityError("WORKER_IDENTITY_INVALID")
            if not connection.execute("SELECT 1 FROM worktrees WHERE worktree_id=?", (worktree_id,)).fetchone():
                raise IdentityError("WORKTREE_UNKNOWN")
            for existing in connection.execute("SELECT c.task_id,c.path,c.kind FROM claims c JOIN tasks t ON t.task_id=c.task_id WHERE t.status != 'COMPLETE'"):
                for path, kind in normalized_claims:
                    if existing["task_id"] != task_id and self._overlap(path, kind, existing["path"], existing["kind"]):
                        raise ClaimConflictError(f"CLAIM_CONFLICT:{path}:{existing['task_id']}")
            for resource in normalized_resources:
                old = connection.execute("SELECT r.task_id FROM resources r JOIN tasks t ON t.task_id=r.task_id WHERE r.resource=? AND t.status != 'COMPLETE'", (resource,)).fetchone()
                if old and old[0] != task_id:
                    raise ResourceConflictError(f"RESOURCE_CONFLICT:{resource}:{old[0]}")
            connection.execute("INSERT INTO tasks(task_id,worker_id,worktree_id,base_sha,owner_packet_path,owner_packet_sha256,dependencies,finish_line,status) VALUES(?,?,?,?,?,?,?,?,?)", (task_id, worker_id, worktree_id, base_sha, owner_packet_path, owner_packet_sha256, _json(sorted(dependencies)), finish_line, "REGISTERED"))
            connection.executemany("INSERT INTO claims(task_id,path,kind) VALUES(?,?,?)", [(task_id, path, kind) for path, kind in normalized_claims])
            connection.executemany("INSERT INTO resources(task_id,resource) VALUES(?,?)", [(task_id, item) for item in normalized_resources])
            return {"status": "REGISTERED", "task_id": task_id}
        return self._mutate(operation)
    def set_gate(self, task_id: str, name: str, status: str, note: str) -> dict[str, Any]:
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            connection.execute(
                "INSERT INTO gates(task_id,name,status,note) VALUES(?,?,?,?) "
                "ON CONFLICT(task_id,name) DO UPDATE SET status=excluded.status,note=excluded.note",
                (task_id, name, status.upper(), note),
            )
            return {"status": status.upper(), "gate": name}
        return self._mutate(operation)

    def _transition_task_state(self, task_id: str, status: str) -> dict[str, Any]:
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            row = connection.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not row:
                raise TaskNotReadyError("TASK_UNKNOWN")
            target = status.upper()
            connection.execute("UPDATE tasks SET status=? WHERE task_id=?", (target, task_id))
            if target == "COMPLETE" and row["status"] != "COMPLETE":
                self._remember_completed_task(connection, task_id)
                connection.execute("INSERT INTO metrics(key,value) VALUES(?,'0') ON CONFLICT(key) DO UPDATE SET value='0'", (f"blocked:{task_id}",))
                connection.execute("INSERT INTO metrics(key,value) VALUES('completed_clean_dispatches','1') ON CONFLICT(key) DO UPDATE SET value=CAST(value AS INTEGER)+1")
            return {"status": target, "task_id": task_id}
        return self._mutate(operation)

    def request_claim_expansion(self, task_id: str, path: str) -> dict[str, Any]:
        canonical = self._normal_path(path)
        result = self.set_gate(task_id, f"claim-expansion:{canonical}", "PENDING", "owner approval required")
        return {"status": "CLAIM_EXPANSION_REQUEST", "gate_status": result["status"], "path": canonical}

    def _verify_owner_packet(self, task: sqlite3.Row) -> set[str]:
        root = Path(task["worktree_path"])
        owner_path = self._normal_path(task["owner_packet_path"])
        if (not owner_path.startswith(".devad/manager/owner-packets/")
                or PurePosixPath(owner_path).stem != task["owner_packet_sha256"]):
            raise IdentityError("OWNER_PACKET_INVALID")
        try:
            packet_path = self._resolve_under(root, root / Path(*PurePosixPath(owner_path).parts))
            data = packet_path.read_bytes()
            packet = json.loads(data.decode("utf-8"))
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            raise IdentityError("OWNER_PACKET_INVALID") from exc
        if hashlib.sha256(data).hexdigest() != task["owner_packet_sha256"] or not isinstance(packet, dict) or packet.get("schema") != "x9-owner-packet-v1" or not isinstance(packet.get("attachments"), list):
            raise IdentityError("OWNER_PACKET_INVALID")
        verified = {owner_path}
        for attachment in packet["attachments"]:
            if not isinstance(attachment, dict) or not isinstance(attachment.get("path"), str) or not isinstance(attachment.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", attachment["sha256"]):
                raise IdentityError("OWNER_PACKET_INVALID")
            try:
                attachment_path = self._normal_path(attachment["path"])
                if (not attachment_path.startswith(".devad/manager/owner-packets/artifacts/")
                        or PurePosixPath(attachment_path).stem != attachment["sha256"]):
                    raise IdentityError("OWNER_PACKET_INVALID")
                target = self._resolve_under(root, root / Path(*PurePosixPath(attachment_path).parts))
                if hashlib.sha256(target.read_bytes()).hexdigest() != attachment["sha256"]:
                    raise IdentityError("OWNER_PACKET_INVALID")
                verified.add(attachment_path)
            except (OSError, ValueError, RuntimeError, ScopeBreachError) as exc:
                raise IdentityError("OWNER_PACKET_INVALID") from exc
        for relative in sorted(verified):
            tracked = self._run_git(["ls-files", "--", relative], root)
            if tracked.returncode:
                raise GitStateError("GIT_STATE_UNKNOWN")
            if tracked.stdout.strip():
                raise IdentityError("OWNER_PACKET_TRACKED")
        return verified

    def _task_packet(self, connection: sqlite3.Connection, task_id: str, sender_id: str) -> dict[str, Any]:
        task = connection.execute("SELECT t.*,w.path AS worktree_path FROM tasks t JOIN worktrees w ON w.worktree_id=t.worktree_id WHERE t.task_id=?", (task_id,)).fetchone()
        if not task:
            raise TaskNotReadyError("TASK_UNKNOWN")
        if task["status"] not in {"REGISTERED", "RETRY_READY"}:
            raise TaskNotReadyError("TASK_STATE_NOT_DISPATCHABLE")
        owner_evidence = self._verify_owner_packet(task)
        controller_evidence = self._controller_snapshot_evidence(Path(task["worktree_path"]), connection)
        local_git = self._git_state(task["base_sha"], task["worktree_path"])
        validated_receipts = set(self._validated_receipt_entries(Path(task["worktree_path"]), connection))
        local_work = {key: [path for path in self._scope_paths(value) if path not in owner_evidence and path not in controller_evidence and path not in validated_receipts] for key, value in local_git.items()}
        claims_for_local = [(row["path"], row["kind"]) for row in connection.execute("SELECT path,kind FROM claims WHERE task_id=?", (task_id,))]
        for path in sorted({item for values in local_work.values() for item in values}):
            if not any(self._overlap(path, "file", claim, kind) for claim, kind in claims_for_local):
                raise ScopeBreachError(f"LOCAL_WORK_SCOPE_BREACH:{path}")
        if len(_json(local_work).encode("utf-8")) >= 1024:
            raise DeliveryError("LOCAL_WORK_TOO_LARGE")
        sender = connection.execute("SELECT role FROM actors WHERE actor_id=?", (sender_id,)).fetchone()
        if not sender or sender[0] != "LINX":
            raise IdentityError("SENDER_IDENTITY_INVALID")
        completed_ids = set(self._completed_task_ids(connection))
        for dependency in json.loads(task["dependencies"]):
            row = connection.execute("SELECT status FROM tasks WHERE task_id=?", (dependency,)).fetchone()
            if (not row or row[0] != "COMPLETE") and dependency not in completed_ids:
                raise TaskNotReadyError("DEPENDENCY_NOT_COMPLETE")
        for gate in connection.execute("SELECT status FROM gates WHERE task_id=?", (task_id,)):
            if gate["status"] != "PASS":
                raise TaskNotReadyError("GATE_NOT_PASS")
        return {
            "schema": "x9-loop-lite-dispatch-v1", "task_id": task_id, "sender_id": sender_id,
            "target_actor_id": task["worker_id"], "worktree_id": task["worktree_id"], "worktree_path": task["worktree_path"],
            "base_sha": task["base_sha"], "owner_packet_path": task["owner_packet_path"], "owner_packet_sha256": task["owner_packet_sha256"], "local_work": local_work, "dependencies": json.loads(task["dependencies"]), "finish_line": task["finish_line"],
            "claims": [dict(row) for row in connection.execute("SELECT path,kind FROM claims WHERE task_id=? ORDER BY path", (task_id,))],
            "resources": [row[0] for row in connection.execute("SELECT resource FROM resources WHERE task_id=? ORDER BY resource", (task_id,))],
            "gates": [dict(row) for row in connection.execute("SELECT name,status,note FROM gates WHERE task_id=? ORDER BY name", (task_id,))],
        }

    def _enforce_coding_limit(self, connection: sqlite3.Connection, worker_id: str) -> None:
        metric = connection.execute("SELECT value FROM metrics WHERE key='completed_clean_dispatches'").fetchone()
        successful = int(metric[0]) if metric else connection.execute("SELECT COUNT(DISTINCT d.task_id) FROM dispatches d JOIN tasks t ON t.task_id=d.task_id WHERE t.status='COMPLETE'").fetchone()[0]
        metrics = {row["key"]: int(row["value"]) for row in connection.execute("SELECT key,value FROM metrics") if str(row["value"]).isdigit()}
        active = {row[0] for row in connection.execute("SELECT DISTINCT t.worker_id FROM tasks t JOIN dispatches d ON d.task_id=t.task_id WHERE t.status != 'COMPLETE' AND d.status IN ('PREPARED','DISPATCHED')")}
        if worker_id not in active and len(active) >= coding_limit(successful, metrics):
            raise TaskNotReadyError("CODING_LIMIT")

    def _action(self, dispatch_id: str, packet: dict[str, Any], packet_sha256: str,
                action_id: str | None = None, attempt: int = 1) -> dict[str, Any]:
        return {"schema": "x9-loop-lite-action-v1", "action_id": action_id or "act-" + str(uuid.uuid4()),
                "action": "SEND_DISPATCH", "dispatch_id": dispatch_id, "task_id": packet["task_id"],
                "target_actor_id": packet["target_actor_id"], "target_role": "WORKER",
                "packet_sha256": packet_sha256, "attempt": attempt, "packet": packet}

    def _status_action(self, action: str, reason: str) -> dict[str, Any]:
        seed = {"action": action, "reason": reason}
        return {"schema": "x9-loop-lite-action-v1", "action_id": "act-" + _sha(seed)[:20],
                "action": action, "dispatch_id": None, "task_id": None, "target_actor_id": None,
                "target_role": None, "packet_sha256": None, "attempt": 0, "packet": None, "reason": reason}

    def _write_action(self, action: dict[str, Any]) -> None:
        encoded = _json(action).encode("utf-8")
        if len(encoded) >= 4096:
            raise DeliveryError("ACTION_TOO_LARGE")
        self._atomic_state_write(self.action_path, encoded)

    def _current_action(self) -> dict[str, Any]:
        connection = self._connect()
        try:
            row = connection.execute("SELECT o.payload FROM outbox o JOIN dispatches d ON d.dispatch_id=o.dispatch_id WHERE d.status='PREPARED' ORDER BY d.created_at,d.dispatch_id LIMIT 1").fetchone()
            if row:
                return json.loads(row["payload"])
            waiting = connection.execute("SELECT 1 FROM dispatches d JOIN tasks t ON t.task_id=d.task_id WHERE t.status != 'COMPLETE' AND d.status='DISPATCHED' LIMIT 1").fetchone()
            return self._status_action("WAIT" if waiting else "NOOP", "dispatch-active" if waiting else "no-outbox")
        finally:
            connection.close()

    def prepare_dispatch(self, task_id: str, sender_id: str) -> dict[str, Any]:
        self._assert_durable()
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            packet = self._task_packet(connection, task_id, sender_id)
            packet_sha256 = _sha(packet)
            old = connection.execute("SELECT * FROM dispatches WHERE task_id=? AND packet_sha256=? AND status IN ('PREPARED','DISPATCHED') ORDER BY rowid DESC LIMIT 1", (task_id, packet_sha256)).fetchone()
            if old:
                if old["status"] == "DISPATCHED":
                    action = self._status_action("WAIT", "delivery-acknowledged")
                    status = "SKIP_ALREADY_DELIVERED"
                else:
                    outbox = connection.execute("SELECT payload FROM outbox WHERE dispatch_id=?", (old["dispatch_id"],)).fetchone()
                    action = json.loads(outbox[0]) if outbox else self._action(old["dispatch_id"], packet, packet_sha256)
                    status = "PREPARED"
                return {"status": status, "dispatch_id": old["dispatch_id"], "packet_sha256": packet_sha256, "supersedes": old["supersedes"], "_action": action}
            self._enforce_coding_limit(connection, packet["target_actor_id"])
            dispatch_id = "dsp-" + str(uuid.uuid4())
            previous = connection.execute("SELECT dispatch_id FROM dispatches WHERE task_id=? ORDER BY rowid DESC LIMIT 1", (task_id,)).fetchone()
            connection.execute("UPDATE dispatches SET status='SUPERSEDED' WHERE task_id=? AND status IN ('PREPARED','DISPATCHED')", (task_id,))
            action = self._action(dispatch_id, packet, packet_sha256)
            if len(_json(action).encode("utf-8")) >= 4096:
                raise DeliveryError("ACTION_TOO_LARGE")
            connection.execute("INSERT INTO dispatches VALUES(?,?,?,?,?,?,?,?,?)", (dispatch_id, task_id, sender_id, packet["target_actor_id"], packet_sha256, _json(packet), previous[0] if previous else None, "PREPARED", self.now_fn()))
            connection.execute("INSERT INTO outbox(dispatch_id,payload) VALUES(?,?)", (dispatch_id, _json(action)))
            return {"dispatch_id": dispatch_id, "packet_sha256": packet_sha256, "supersedes": previous[0] if previous else None, "_action": action}
        result = self._mutate(operation)
        action = result.pop("_action")
        self._write_action(action)
        return result

    def record_delivery(self, dispatch_id: str, phase: str, method: str, result: str) -> dict[str, Any]:
        phase = phase.upper()
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            dispatch = connection.execute("SELECT * FROM dispatches WHERE dispatch_id=?", (dispatch_id,)).fetchone()
            if not dispatch:
                raise DeliveryError("DISPATCH_UNKNOWN")
            task_status = connection.execute("SELECT status FROM tasks WHERE task_id=?", (dispatch["task_id"],)).fetchone()
            if phase == "REVIEW":
                if (dispatch["status"] != "COMPLETE" or not task_status
                        or task_status["status"] != "THINX_REVIEW_REQUIRED"
                        or result.casefold() not in {"ack", "acknowledged"}):
                    raise DeliveryError("REVIEW_DELIVERY_INVALID")
            else:
                if dispatch["status"] not in {"PREPARED", "DISPATCHED"}:
                    raise DeliveryError("DISPATCH_INACTIVE")
                if phase == "DISPATCH" and dispatch["status"] != "PREPARED":
                    raise DeliveryError("DISPATCH_ALREADY_DELIVERED")
            callbacks = connection.execute("SELECT COUNT(*) FROM deliveries WHERE dispatch_id=? AND phase='CALLBACK'", (dispatch_id,)).fetchone()[0]
            if phase == "CALLBACK" and callbacks >= 2:
                raise DeliveryError("CALLBACK_RETRY_LIMIT")
            connection.execute("INSERT INTO deliveries(dispatch_id,phase,method,result,created_at) VALUES(?,?,?,?,?)", (dispatch_id, phase, method, result, self.now_fn()))
            attempts = connection.execute("SELECT COUNT(*) FROM deliveries WHERE dispatch_id=? AND phase='DISPATCH'", (dispatch_id,)).fetchone()[0]
            action = None
            if phase == "DISPATCH":
                if result.casefold() in {"ack", "acknowledged"}:
                    connection.execute("UPDATE dispatches SET status='DISPATCHED' WHERE dispatch_id=?", (dispatch_id,))
                    action = self._status_action("WAIT", "delivery-acknowledged")
                else:
                    row = connection.execute("SELECT payload FROM outbox WHERE dispatch_id=?", (dispatch_id,)).fetchone()
                    action = json.loads(row[0]) if row else self._action(dispatch_id, json.loads(dispatch["packet"]), dispatch["packet_sha256"])
                    action["attempt"] = attempts + 1
                    connection.execute("INSERT INTO outbox(dispatch_id,payload) VALUES(?,?) ON CONFLICT(dispatch_id) DO UPDATE SET payload=excluded.payload", (dispatch_id, _json(action)))
            if phase == "CALLBACK" and result.casefold() == "failed":
                response = ({"status": "CALLBACK_FAILED", "next": "MANUAL_ONE_SHOT_PICKUP", "attempts": attempts} if callbacks + 1 == 2 else {"status": "CALLBACK_RETRY", "next": "RETRY_SAME_EVENT_ONCE", "attempts": attempts})
            else:
                acknowledged = result.casefold() in {"ack", "acknowledged"}
                response = {"status": "DELIVERED" if acknowledged else "DELIVERY_UNCONFIRMED", "attempts": attempts, "sent_once": acknowledged and attempts == 1}
            response["_action"] = action
            return response
        response = self._mutate(operation)
        action = response.pop("_action")
        if action:
            self._write_action(action)
        return response

    def _run_git(self, arguments: list[str], worktree_path: str | Path | None = None) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(["git", "-C", str(worktree_path or self.repo), *arguments], capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT_SECONDS)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GitStateError("GIT_STATE_UNKNOWN") from exc

    def _git_paths(self, arguments: list[str], worktree_path: str | Path | None = None) -> list[str]:
        completed = self._run_git(arguments, worktree_path)
        if completed.returncode:
            raise GitStateError("GIT_STATE_UNKNOWN")
        return sorted({self._normal_path(path) for path in completed.stdout.splitlines() if path})

    def _git_history_paths(
        self, base_sha: str, end_sha: str, worktree_path: str | Path | None = None
    ) -> list[str]:
        return self._git_paths(
            ["log", "--format=", "--name-only", "--no-renames", f"{base_sha}..{end_sha}"],
            worktree_path,
        )

    def _git_state(self, base_sha: str, worktree_path: str | Path | None = None) -> dict[str, list[str]]:
        return {"staged": self._git_paths(["diff", "--cached", "--name-only"], worktree_path), "unstaged": self._git_paths(["diff", "--name-only"], worktree_path), "untracked": self._git_paths(["ls-files", "--others", "--exclude-standard"], worktree_path), "committed": self._git_history_paths(base_sha, "HEAD", worktree_path)}

    @staticmethod
    def _is_controller_runtime_path(path: str) -> bool:
        runtime = ".devad/manager/loop-lite/runtime/"
        database = ".devad/manager/loop-lite/loop.db"
        return (
            path.startswith(runtime)
            or path == database
            or path in {database + "-wal", database + "-shm"}
            or path.startswith(database + ".corrupt-")
            or path.startswith(database + ".rebuild-")
        )

    def _scope_paths(self, paths: list[str], receipt_path: str | None = None) -> list[str]:
        receipt = self._normal_path(receipt_path) if receipt_path else None
        return [path for path in paths if not self._is_controller_runtime_path(path) and path != receipt]

    def reconcile(self, task_id: str | None = None) -> dict[str, Any]:
        task = None
        claims: list[tuple[str, str]] = []
        tampered: set[str] = set()
        if task_id:
            connection = self._connect()
            try:
                task = connection.execute("SELECT t.*,w.path AS worktree_path FROM tasks t JOIN worktrees w ON w.worktree_id=t.worktree_id WHERE t.task_id=?", (task_id,)).fetchone()
                claims = [(row["path"], row["kind"]) for row in connection.execute("SELECT path,kind FROM claims WHERE task_id=?", (task_id,))]
            finally:
                connection.close()
            if not task:
                raise TaskNotReadyError("TASK_UNKNOWN")
            tampered = self._controller_snapshot_tamper(Path(task["worktree_path"]))
        self._write_snapshot()
        self._safe_state_path(self.snapshot_path)
        snapshot = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        result: dict[str, Any] = {"snapshot": "PASS", "recovery": self._recovery_evidence(snapshot["recovery_worktrees"], strict=False)}
        if task:
            owner_evidence = self._verify_owner_packet(task)
            controller_evidence = self._controller_snapshot_evidence(Path(task["worktree_path"])) - tampered
            git = self._git_state(task["base_sha"], task["worktree_path"])
            scoped_git = {key: [path for path in self._scope_paths(value) if path not in owner_evidence and path not in controller_evidence] for key, value in git.items()}
            changed = sorted(set(path for paths in scoped_git.values() for path in paths))
            scope_breach = [path for path in changed if not any(self._overlap(path, "file", claim, kind) for claim, kind in claims)]
            result.update({"git": scoped_git, "scope_breach": scope_breach, "controller_tamper": sorted(tampered)})
        self._write_action(self._current_action())
        self._write_views()
        return result
    def _claimed(self, connection: sqlite3.Connection, task_id: str, path: str) -> bool:
        return any(self._overlap(path, "file", row["path"], row["kind"]) for row in connection.execute("SELECT path,kind FROM claims WHERE task_id=?", (task_id,)))

    def _validated_receipt_paths(
        self, worktree_root: Path, connection: sqlite3.Connection | None = None,
        exclude_paths: set[str] | None = None,
    ) -> set[str]:
        return set(self._validated_receipt_entries(worktree_root, connection, exclude_paths))

    def _actual_git_paths(
        self, task_id: str, receipt_path: str, validated_receipts: set[str] | None = None
    ) -> list[str]:
        connection = self._connect()
        try:
            task = connection.execute("SELECT t.base_sha,w.path AS worktree_path FROM tasks t JOIN worktrees w ON w.worktree_id=t.worktree_id WHERE t.task_id=?", (task_id,)).fetchone()
        finally:
            connection.close()
        if not task:
            raise StaleCompletionError("STALE_COMPLETION")
        worktree_root = Path(task["worktree_path"])
        receipt = self._normal_path(receipt_path)
        if validated_receipts is None:
            validated_receipts = self._validated_receipt_paths(
                worktree_root, exclude_paths={receipt}
            )
        excluded = set(validated_receipts) | {receipt}
        state = self._git_state(task["base_sha"], task["worktree_path"])
        return sorted({path for paths in state.values() for path in self._scope_paths(paths) if path not in excluded})

    def _duplicate_event(self, event_id: str) -> bool:
        connection = self._connect()
        try:
            return bool(connection.execute("SELECT 1 FROM events WHERE event_id=?", (event_id,)).fetchone())
        finally:
            connection.close()

    def consume_event(self, event: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(event, dict) or not isinstance(event.get("event_id"), str) or not event["event_id"]:
            raise StaleCompletionError("EVENT_INVALID")
        if self._duplicate_event(event["event_id"]):
            return {"status": "DUPLICATE_EVENT"}
        required = ("event_type", "task_id", "dispatch_id", "actor_id", "role", "packet_sha256", "result_path", "result_sha256")
        if any(not isinstance(event.get(field), str) or not event[field] for field in required):
            raise StaleCompletionError("EVENT_INVALID")
        event_type = event["event_type"]
        expected_role = {"WORKER_RESULT": "WORKER", "THINX_DECISION": "THINX"}.get(event_type)
        if expected_role is None or event["role"] != expected_role or not re.fullmatch(r"[0-9a-f]{64}", event["result_sha256"]):
            raise StaleCompletionError("EVENT_INVALID")
        try:
            receipt_relative = self._normal_path(event["result_path"])
        except ScopeBreachError as exc:
            raise StaleCompletionError("EVENT_INVALID") from exc
        connection = self._connect()
        try:
            dispatch = connection.execute("SELECT * FROM dispatches WHERE dispatch_id=?", (event["dispatch_id"],)).fetchone()
            task = connection.execute("SELECT t.*,w.path AS worktree_path FROM tasks t JOIN worktrees w ON w.worktree_id=t.worktree_id WHERE t.task_id=?", (event["task_id"],)).fetchone()
            actor = connection.execute("SELECT role FROM actors WHERE actor_id=?", (event["actor_id"],)).fetchone()
            latest = connection.execute("SELECT dispatch_id,status FROM dispatches WHERE task_id=? ORDER BY rowid DESC LIMIT 1", (event["task_id"],)).fetchone()
            review_ack = connection.execute("SELECT 1 FROM deliveries WHERE dispatch_id=? AND phase='REVIEW' AND lower(result) IN ('ack','acknowledged') ORDER BY id DESC LIMIT 1", (event["dispatch_id"],)).fetchone()
        finally:
            connection.close()
        worker_ready = (
            expected_role == "WORKER" and dispatch and task
            and dispatch["status"] == "DISPATCHED"
            and task["status"] in {"REGISTERED", "RETRY_READY"}
            and latest and latest["dispatch_id"] == dispatch["dispatch_id"]
        )
        thinx_ready = (
            expected_role == "THINX" and dispatch and task
            and dispatch["status"] == "COMPLETE"
            and task["status"] == "THINX_REVIEW_REQUIRED"
            and latest and latest["dispatch_id"] == dispatch["dispatch_id"]
            and review_ack
        )
        if (not dispatch or not task or dispatch["task_id"] != task["task_id"]
                or not (worker_ready or thinx_ready)
                or not actor or actor["role"] != expected_role
                or event["packet_sha256"] != dispatch["packet_sha256"]):
            raise StaleCompletionError("STALE_COMPLETION")
        try:
            stored_packet = json.loads(dispatch["packet"])
            stored_worktree = Path(stored_packet["worktree_path"]).resolve(strict=True)
            current_worktree = Path(task["worktree_path"]).resolve(strict=True)
        except (KeyError, TypeError, ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
            raise StaleCompletionError("STALE_COMPLETION") from exc
        if (stored_packet.get("task_id") != task["task_id"]
                or stored_packet.get("worktree_id") != task["worktree_id"]
                or stored_worktree != current_worktree
                or stored_packet.get("base_sha") != task["base_sha"]
                or stored_packet.get("target_actor_id") != task["worker_id"]):
            raise StaleCompletionError("STALE_COMPLETION")
        if expected_role == "WORKER" and event["actor_id"] != task["worker_id"]:
            raise StaleCompletionError("STALE_COMPLETION")
        expected_receipt = self._normal_path(f".devad/workers/{event['actor_id']}/receipts/{event['event_id']}.json")
        if receipt_relative != expected_receipt:
            raise StaleCompletionError("STALE_COMPLETION")
        worktree_root = Path(task["worktree_path"])
        try:
            result_path = self._resolve_under(worktree_root, worktree_root / Path(*PurePosixPath(receipt_relative).parts))
            data = result_path.read_bytes()
            receipt = json.loads(data.decode("utf-8"))
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            raise StaleCompletionError("STALE_COMPLETION") from exc
        if not isinstance(receipt, dict) or hashlib.sha256(data).hexdigest() != event["result_sha256"]:
            raise StaleCompletionError("STALE_COMPLETION")
        prior_receipts = self._validated_receipt_entries(
            worktree_root, exclude_paths={receipt_relative}
        )
        allowed_system = {receipt_relative, *self._verify_owner_packet(task), *self._controller_snapshot_evidence(worktree_root)}
        if expected_role == "WORKER":
            expected = {"schema": "x9-loop-lite-result-v1", "event_id": event["event_id"], "task_id": task["task_id"], "dispatch_id": dispatch["dispatch_id"], "worker_id": task["worker_id"], "role": "WORKER", "packet_sha256": dispatch["packet_sha256"]}
            if any(receipt.get(field) != value for field, value in expected.items()):
                raise StaleCompletionError("RESULT_INVALID")
            changed_files = receipt.get("changed_files")
            proof = receipt.get("proof")
            outcome = receipt.get("outcome")
            if not isinstance(changed_files, list) or not all(isinstance(item, str) for item in changed_files) or not isinstance(proof, list) or outcome not in {"COMPLETE", "BLOCKED"}:
                raise StaleCompletionError("RESULT_INVALID")
            allowed_system = {receipt_relative, *self._verify_owner_packet(task), *self._controller_snapshot_evidence(worktree_root)}
            if outcome == "COMPLETE" and changed_files:
                if not isinstance(receipt.get("c1"), str) or not isinstance(receipt.get("c2"), str) or not re.fullmatch(r"[0-9a-f]{40}", receipt["c1"]) or not re.fullmatch(r"[0-9a-f]{40}", receipt["c2"]) or not isinstance(proof, list):
                    raise StaleCompletionError("RESULT_INVALID")
                proof_paths: set[str] = set()
                for item in proof:
                    if not isinstance(item, dict) or item.get("kind") not in {"security", "tests"} or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                        raise StaleCompletionError("RESULT_INVALID")
                    kind = item["kind"]
                    proof_path = self._normal_path(item["path"])
                    expected_proof = self._normal_path(f".devad/workers/{task['worker_id']}/proof/{event['event_id']}/{kind}.json")
                    if proof_path != expected_proof or proof_path in proof_paths:
                        raise StaleCompletionError("RESULT_INVALID")
                    try:
                        candidate = self._resolve_under(worktree_root, worktree_root / Path(*PurePosixPath(proof_path).parts))
                        proof_data = candidate.read_bytes()
                        proof_document = json.loads(proof_data.decode("utf-8"))
                    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
                        raise StaleCompletionError("RESULT_INVALID") from exc
                    expected_document = {
                        "schema": "x9-loop-lite-proof-v1", "event_id": event["event_id"],
                        "task_id": task["task_id"], "dispatch_id": dispatch["dispatch_id"],
                        "worker_id": task["worker_id"], "role": "WORKER", "kind": kind, "status": "PASS",
                    }
                    if hashlib.sha256(proof_data).hexdigest() != item["sha256"] or proof_document != expected_document:
                        raise StaleCompletionError("RESULT_INVALID")
                    proof_paths.add(proof_path)
                if proof_paths != {
                    self._normal_path(f".devad/workers/{task['worker_id']}/proof/{event['event_id']}/security.json"),
                    self._normal_path(f".devad/workers/{task['worker_id']}/proof/{event['event_id']}/tests.json"),
                }:
                    raise StaleCompletionError("RESULT_INVALID")
                allowed_system.update(proof_paths)
                c1_paths = set(self._git_history_paths(task["base_sha"], receipt["c1"], task["worktree_path"]))
                c2_paths = set(self._git_history_paths(receipt["c1"], receipt["c2"], task["worktree_path"]))
                changed_paths = {self._normal_path(path) for path in changed_files}
                attestation = self._normal_path(".devad/docs/commits/" + receipt["c1"] + ".md")
                c1_ancestor = self._run_git(["merge-base", "--is-ancestor", receipt["c1"], receipt["c2"]], task["worktree_path"])
                c2_ancestor = self._run_git(["merge-base", "--is-ancestor", receipt["c2"], "HEAD"], task["worktree_path"])
                current_head = self._run_git(["rev-parse", "HEAD"], task["worktree_path"])
                try:
                    attestation_path = self._resolve_under(worktree_root, worktree_root / Path(*PurePosixPath(attestation).parts))
                except (OSError, ValueError, RuntimeError) as exc:
                    raise StaleCompletionError("RESULT_INVALID") from exc
                shown = self._run_git(["show", f"{receipt['c2']}:{attestation}"], task["worktree_path"])
                c1_system = proof_paths | self._verify_owner_packet(task)
                c1_extra = sorted(c1_paths - c1_system - changed_paths)
                c2_extra = sorted(c2_paths - {attestation})
                if c1_extra or c2_extra:
                    raise ScopeBreachError(f"SCOPE_BREACH:{(c1_extra or c2_extra)[0]}")
                if (len(changed_paths) != len(changed_files) or c1_ancestor.returncode or c2_ancestor.returncode
                        or current_head.returncode or current_head.stdout.strip() != receipt["c2"]
                        or c1_paths - c1_system != changed_paths or c2_paths != {attestation}
                        or not attestation_path.is_file() or shown.returncode
                        or shown.stdout.encode("utf-8") != attestation_path.read_bytes()):
                    raise StaleCompletionError("RESULT_INVALID")
                allowed_system.add(attestation)
            if outcome == "BLOCKED" and (not isinstance(receipt.get("blocker"), str) or not receipt["blocker"]):
                raise StaleCompletionError("RESULT_INVALID")
            if outcome == "COMPLETE":
                expected_head = receipt["c2"] if changed_files else task["base_sha"]
                current_head = self._run_git(["rev-parse", "HEAD"], task["worktree_path"])
                working = {
                    key: self._scope_paths(value)
                    for key, value in self._git_state(task["base_sha"], task["worktree_path"]).items()
                    if key in {"staged", "unstaged", "untracked"}
                }
                permitted_dirty = allowed_system | set(prior_receipts) | {receipt_relative}
                unexpected_dirty = sorted({path for values in working.values() for path in values if path not in permitted_dirty})
                if current_head.returncode or current_head.stdout.strip() != expected_head:
                    raise StaleCompletionError("RESULT_INVALID")
                if unexpected_dirty:
                    raise ScopeBreachError(f"SCOPE_BREACH:{unexpected_dirty[0]}")
        else:
            expected = {"schema": "x9-loop-lite-thinx-decision-v1", "event_id": event["event_id"], "task_id": task["task_id"], "dispatch_id": dispatch["dispatch_id"], "actor_id": event["actor_id"], "role": "THINX", "packet_sha256": dispatch["packet_sha256"]}
            if any(receipt.get(field) != value for field, value in expected.items()) or receipt.get("decision") not in {"PASS", "BLOCKED", "FAIL"}:
                raise StaleCompletionError("RESULT_INVALID")
            changed_files = []
            outcome = None
        actual_paths = self._actual_git_paths(task["task_id"], receipt_relative, set(prior_receipts))
        if expected_role == "WORKER" and outcome == "COMPLETE" and not changed_files:
            if any(path not in allowed_system for path in actual_paths):
                raise StaleCompletionError("RESULT_INVALID")
        def operation(connection: sqlite3.Connection) -> dict[str, Any]:
            if connection.execute("SELECT 1 FROM events WHERE event_id=?", (event["event_id"],)).fetchone():
                return {"status": "DUPLICATE_EVENT"}
            latest = connection.execute("SELECT dispatch_id,status FROM dispatches WHERE task_id=? ORDER BY rowid DESC LIMIT 1", (task["task_id"],)).fetchone()
            current_task = connection.execute("SELECT status FROM tasks WHERE task_id=?", (task["task_id"],)).fetchone()
            current_dispatch = connection.execute("SELECT status FROM dispatches WHERE dispatch_id=?", (dispatch["dispatch_id"],)).fetchone()
            review_ack = connection.execute("SELECT 1 FROM deliveries WHERE dispatch_id=? AND phase='REVIEW' AND lower(result) IN ('ack','acknowledged') ORDER BY id DESC LIMIT 1", (dispatch["dispatch_id"],)).fetchone()
            worker_ready = expected_role == "WORKER" and current_dispatch and current_dispatch["status"] == "DISPATCHED" and current_task and current_task["status"] in {"REGISTERED", "RETRY_READY"}
            thinx_ready = expected_role == "THINX" and current_dispatch and current_dispatch["status"] == "COMPLETE" and current_task and current_task["status"] == "THINX_REVIEW_REQUIRED" and review_ack
            if (not latest or latest["dispatch_id"] != dispatch["dispatch_id"] or not (worker_ready or thinx_ready)):
                raise StaleCompletionError("STALE_COMPLETION")
            for changed in [*changed_files, *actual_paths]:
                try:
                    canonical = self._normal_path(changed)
                except ScopeBreachError as exc:
                    raise StaleCompletionError("RESULT_INVALID") from exc
                if canonical in allowed_system:
                    continue
                if not self._claimed(connection, task["task_id"], canonical):
                    raise ScopeBreachError(f"SCOPE_BREACH:{canonical}")
            connection.execute("INSERT INTO events(event_id,task_id,dispatch_id,event_sha256,created_at) VALUES(?,?,?,?,?)", (event["event_id"], task["task_id"], dispatch["dispatch_id"], event["result_sha256"], self.now_fn()))
            self._set_receipt_state(
                connection, task["worktree_id"],
                [*prior_receipts.values(), event["result_sha256"]],
            )
            if expected_role == "THINX":
                status = "PASS" if receipt["decision"] == "PASS" else "BLOCKED"
                connection.execute("INSERT INTO gates(task_id,name,status,note) VALUES(?,?,?,?) ON CONFLICT(task_id,name) DO UPDATE SET status=excluded.status,note=excluded.note", (task["task_id"], f"thinx:{event['actor_id']}", status, receipt["decision"]))
                if status == "PASS":
                    connection.execute("UPDATE tasks SET status='REGISTERED' WHERE task_id=?", (task["task_id"],))
                    connection.execute("INSERT INTO metrics(key,value) VALUES(?, '0') ON CONFLICT(key) DO UPDATE SET value='0'", (f"blocked:{task['task_id']}",))
                return {"status": "THINX_CONSUMED"}
            if outcome == "BLOCKED":
                metric_key = f"blocked:{task['task_id']}"
                old_count = connection.execute("SELECT value FROM metrics WHERE key=?", (metric_key,)).fetchone()
                count = int(old_count[0]) + 1 if old_count else 1
                connection.execute("INSERT INTO metrics(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (metric_key, str(count)))
                task_status = "THINX_REVIEW_REQUIRED" if count >= 3 else "RETRY_READY"
                connection.execute("UPDATE tasks SET status=? WHERE task_id=?", (task_status, task["task_id"]))
                connection.execute("UPDATE dispatches SET status='COMPLETE' WHERE dispatch_id=?", (dispatch["dispatch_id"],))
                return {"status": task_status}
            previous = connection.execute("SELECT status FROM tasks WHERE task_id=?", (task["task_id"],)).fetchone()
            connection.execute("UPDATE tasks SET status='COMPLETE' WHERE task_id=?", (task["task_id"],))
            connection.execute("UPDATE dispatches SET status='COMPLETE' WHERE dispatch_id=?", (dispatch["dispatch_id"],))
            if previous and previous[0] != "COMPLETE":
                self._remember_completed_task(connection, task["task_id"])
                connection.execute("INSERT INTO metrics(key,value) VALUES(?,'0') ON CONFLICT(key) DO UPDATE SET value='0'", (f"blocked:{task['task_id']}",))
                connection.execute("INSERT INTO metrics(key,value) VALUES('completed_clean_dispatches','1') ON CONFLICT(key) DO UPDATE SET value=CAST(value AS INTEGER)+1")
            return {"status": "CONSUMED"}
        result = self._mutate(operation)
        self._write_views()
        return result
    def _write_views(self) -> None:
        connection = self._connect()
        try:
            tasks = [dict(row) for row in connection.execute("SELECT task_id,worker_id,worktree_id,status FROM tasks ORDER BY task_id LIMIT 50")]
            dispatches = [dict(row) for row in connection.execute("SELECT dispatch_id,task_id,target_id,status FROM dispatches WHERE status IN ('PREPARED','DISPATCHED') ORDER BY dispatch_id LIMIT 30")]
            gates = [dict(row) for row in connection.execute("SELECT task_id,name,status FROM gates ORDER BY task_id,name LIMIT 30")]
        finally:
            connection.close()
        status_lines = ["# X9 Loop Lite Status (Generated)", "", "Generated convenience view; not parser authority.", "", "## Tasks"]
        status_lines.extend(f"- {row['task_id']}: {row['status']} worker={row['worker_id']} worktree={row['worktree_id']}" for row in tasks)
        handoff_lines = ["# X9 Loop Lite Handoffs (Generated)", "", "Generated convenience view; not parser authority.", "", "## Active Dispatches"]
        handoff_lines.extend(f"- {row['dispatch_id']}: task={row['task_id']} target={row['target_id']} status={row['status']}" for row in dispatches)
        handoff_lines.append("## Gates")
        handoff_lines.extend(f"- {row['task_id']}/{row['name']}: {row['status']}" for row in gates)
        for path, lines in ((self.root / "runtime" / "STATUS.md", status_lines), (self.root / "runtime" / "HANDOFFS.md", handoff_lines)):
            content = "\n".join(lines[:120]) + "\n"
            if len(content.encode("utf-8")) >= 12288:
                content = "\n".join(lines[:20]) + "\n"
            self._atomic_state_write(path, content.encode("utf-8"))

    def doctor(self) -> dict[str, Any]:
        checks: dict[str, Any] = {"integrity_check": "FAIL", "foreign_key_check": "FAIL", "snapshot": "FAIL", "action": "ABSENT", "worktrees": [], "receipts": [], "recovery": [], "conflicts": {"claims": [], "resources": []}}
        generation = None
        try:
            self._safe_state_path(self.db_path)
            self._safe_state_path(self.snapshot_path)
            self._safe_state_path(self.action_path)
            connection = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            try:
                checks["integrity_check"] = "PASS" if connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok" else "FAIL"
                checks["foreign_key_check"] = "PASS" if not connection.execute("PRAGMA foreign_key_check").fetchall() else "FAIL"
                row = connection.execute("SELECT value FROM meta WHERE key='generation'").fetchone()
                generation = int(row[0]) if row else None
                worktrees = [dict(row) for row in connection.execute("SELECT worktree_id,path FROM worktrees")]
                checks["worktrees"] = [row["worktree_id"] for row in worktrees if not Path(row["path"]).is_dir()]
                complete = [dict(row) for row in connection.execute("SELECT t.task_id,t.worker_id,w.path FROM tasks t JOIN worktrees w ON w.worktree_id=t.worktree_id WHERE t.status='COMPLETE'")]
                checks["receipts"] = [row["task_id"] for row in complete if not any((Path(row["path"]) / ".devad" / "workers" / row["worker_id"] / "receipts").glob("*.json"))]
                for worktree in worktrees:
                    try:
                        self._validated_receipt_entries(Path(worktree["path"]), connection)
                    except StateNotDurableError:
                        checks["receipts"].append(f"RECEIPT_SET_MISMATCH:{worktree['worktree_id']}")
                active_claims = [dict(row) for row in connection.execute("SELECT c.task_id,c.path,c.kind FROM claims c JOIN tasks t ON t.task_id=c.task_id WHERE t.status != 'COMPLETE'")]
                for index, left in enumerate(active_claims):
                    for right in active_claims[index + 1:]:
                        if left["task_id"] != right["task_id"] and self._overlap(left["path"], left["kind"], right["path"], right["kind"]):
                            checks["conflicts"]["claims"].append(f"{left['task_id']}:{right['task_id']}")
                for row in connection.execute("SELECT r.resource,group_concat(r.task_id) AS tasks FROM resources r JOIN tasks t ON t.task_id=r.task_id WHERE t.status != 'COMPLETE' GROUP BY r.resource HAVING COUNT(*) > 1"):
                    checks["conflicts"]["resources"].append(f"{row['resource']}:{row['tasks']}")
            finally:
                connection.close()
            snapshot = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
            checks["snapshot"] = "PASS" if self.snapshot_path.stat().st_size < 8192 and snapshot.get("schema") == SCHEMA and snapshot.get("generation") == generation else "FAIL"
            recovery_worktrees = snapshot.get("recovery_worktrees")
            if not isinstance(recovery_worktrees, list):
                checks["recovery"] = ["SNAPSHOT_RECOVERY_INVALID"]
            else:
                checks["recovery"] = self._recovery_evidence(recovery_worktrees, strict=False)["issues"]
            if self.action_path.exists():
                action = json.loads(self.action_path.read_text(encoding="utf-8"))
                valid = isinstance(action, dict) and action.get("schema") == "x9-loop-lite-action-v1" and action.get("action") in {"SEND_DISPATCH", "WAIT", "MANUAL", "NOOP"}
                if action.get("action") == "SEND_DISPATCH":
                    valid = valid and all(key in action for key in ("dispatch_id", "task_id", "target_actor_id", "target_role", "packet_sha256", "attempt", "packet"))
                checks["action"] = "PASS" if valid else "FAIL"
        except (LoopError, OSError, sqlite3.Error, json.JSONDecodeError, ValueError):
            pass
        durable = checks["snapshot"] == "PASS"
        healthy = durable and checks["integrity_check"] == "PASS" and checks["foreign_key_check"] == "PASS" and checks["action"] != "FAIL" and not checks["worktrees"] and not checks["receipts"] and not checks["recovery"] and not checks["conflicts"]["claims"] and not checks["conflicts"]["resources"]
        return {"status": "PASS" if healthy else "FAIL", "durable": durable, "checks": checks, "metrics": {"token_telemetry": "Unknown"}}

    def _is_durable_read_only(self) -> bool:
        try:
            self._safe_state_path(self.db_path)
            self._safe_state_path(self.snapshot_path)
            snapshot = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
            connection = sqlite3.connect(f"file:{self.db_path.as_posix()}?mode=ro", uri=True)
            try:
                row = connection.execute("SELECT value FROM meta WHERE key='generation'").fetchone()
                return bool(row and snapshot.get("schema") == SCHEMA and int(row[0]) == snapshot.get("generation") and self.snapshot_path.stat().st_size < 8192)
            finally:
                connection.close()
        except (LoopError, OSError, sqlite3.Error, json.JSONDecodeError, ValueError):
            return False
    def rebuild(self) -> dict[str, Any]:
        self._safe_state_path(self.root, directory=True)
        self._safe_state_path(self.snapshot_path)
        self._safe_state_path(self.db_path)
        if not self.snapshot_path.is_file():
            raise SnapshotExportError("SNAPSHOT_MISSING")
        try:
            snapshot = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SnapshotExportError("SNAPSHOT_INVALID") from exc
        tables = snapshot.get("tables")
        if snapshot.get("schema") != SCHEMA or not isinstance(snapshot.get("generation"), int) or not isinstance(tables, dict) or set(tables) != set(SNAPSHOT_TABLES):
            raise SnapshotExportError("SNAPSHOT_TABLE_UNKNOWN")
        completed = snapshot.get("completed_task_ids", [])
        if not isinstance(completed, list) or len(completed) > COMPLETED_TASK_ID_CAP or not all(isinstance(item, str) for item in completed):
            raise SnapshotExportError("SNAPSHOT_INVALID")
        attempts = snapshot.get("dispatch_attempts", {})
        if not isinstance(attempts, dict) or not all(isinstance(key, str) and isinstance(value, int) and value >= 1 for key, value in attempts.items()):
            raise SnapshotExportError("SNAPSHOT_INVALID")
        recovery_worktrees = snapshot.get("recovery_worktrees", [])
        if (not isinstance(recovery_worktrees, list) or any(not isinstance(row, dict) or set(row) != {"worktree_id", "path"} or not isinstance(row["worktree_id"], str) or not row["worktree_id"] or not isinstance(row["path"], str) or not row["path"] for row in recovery_worktrees) or len({row["worktree_id"] for row in recovery_worktrees}) != len(recovery_worktrees)):
            raise SnapshotExportError("SNAPSHOT_INVALID")
        for table in SNAPSHOT_TABLES:
            rows = tables.get(table, [])
            if not isinstance(rows, list):
                raise SnapshotExportError("SNAPSHOT_TABLE_INVALID")
            columns = set(SNAPSHOT_COLUMNS[table])
            for row in rows:
                if not isinstance(row, dict) or set(row) != columns:
                    raise SnapshotExportError("SNAPSHOT_COLUMN_UNKNOWN")
        recovery = self._recovery_evidence(recovery_worktrees, strict=True)
        temporary = self.db_path.with_name(f"loop.db.rebuild-{uuid.uuid4().hex}.tmp")
        self._safe_state_path(temporary, create_parents=True)
        connection: sqlite3.Connection | None = None
        built = False
        try:
            connection = sqlite3.connect(temporary, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            self._schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            for table in SNAPSHOT_TABLES:
                columns = SNAPSHOT_COLUMNS[table]
                statement = f"INSERT INTO {table}({','.join(columns)}) VALUES({','.join('?' for _ in columns)})"
                for row in tables.get(table, []):
                    connection.execute(statement, tuple(row[column] for column in columns))
            for worktree in recovery_worktrees:
                existing = connection.execute("SELECT path FROM worktrees WHERE worktree_id=?", (worktree["worktree_id"],)).fetchone()
                if existing and existing[0] != worktree["path"]:
                    raise SnapshotExportError("SNAPSHOT_INVALID")
                if not existing:
                    connection.execute("INSERT INTO worktrees(worktree_id,path,repository_id) VALUES(?,?,?)", (worktree["worktree_id"], worktree["path"], "recovery"))
            connection.execute(
                "INSERT INTO metrics(key,value) VALUES('completed_task_ids',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (_json(completed),),
            )
            try:
                for worktree in recovery_worktrees:
                    self._validated_receipt_entries(Path(worktree["path"]), connection)
            except StateNotDurableError as exc:
                raise SnapshotExportError("RECOVERY_RECEIPT_INVALID") from exc
            for key, value in (("recovery_worktrees", recovery["worktrees"]), ("recovery_receipts", recovery["receipts"]), ("recovery_git_paths", recovery["git_paths"]), ("recovery_receipt_sha256", recovery["receipt_sha256"])):
                connection.execute("INSERT INTO metrics(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
            if not tables.get("outbox"):
                for row in tables.get("dispatches", []):
                    if row["status"] != "PREPARED":
                        continue
                    try:
                        packet = json.loads(row["packet"])
                    except (TypeError, json.JSONDecodeError) as exc:
                        raise SnapshotExportError("SNAPSHOT_INVALID") from exc
                    action = self._action(row["dispatch_id"], packet, row["packet_sha256"], attempt=attempts.get(row["dispatch_id"], 1))
                    connection.execute("INSERT INTO outbox(dispatch_id,payload) VALUES(?,?)", (row["dispatch_id"], _json(action)))
            connection.execute("UPDATE meta SET value=? WHERE key='generation'", (str(snapshot["generation"]),))
            if connection.execute("PRAGMA foreign_key_check").fetchall() or connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise SnapshotExportError("SNAPSHOT_INVALID")
            connection.commit()
            built = True
        except SnapshotExportError:
            if connection:
                connection.rollback()
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            if connection:
                connection.rollback()
            raise SnapshotExportError("SNAPSHOT_INVALID") from exc
        finally:
            if connection:
                connection.close()
            if not built and temporary.exists():
                temporary.unlink()
        recovery_id = uuid.uuid4().hex
        originals = [self.db_path, Path(str(self.db_path) + "-wal"), Path(str(self.db_path) + "-shm")]
        backups: list[tuple[Path, Path]] = []
        installed = False
        try:
            for original in originals:
                self._safe_state_path(original)
                if original.exists():
                    backup = original.with_name(original.name + f".corrupt-{recovery_id}")
                    self._safe_state_path(backup, create_parents=True)
                    os.replace(original, backup)
                    backups.append((original, backup))
            os.replace(temporary, self.db_path)
            installed = True
            self._safe_state_path(self.db_path)
        except OSError as exc:
            if installed and self.db_path.exists():
                failed = self.db_path.with_name(f"loop.db.failed-{recovery_id}")
                self._safe_state_path(failed, create_parents=True)
                os.replace(self.db_path, failed)
            for original, backup in reversed(backups):
                if backup.exists() and not original.exists():
                    os.replace(backup, original)
            if temporary.exists():
                failed = self.db_path.with_name(
                    f"loop.db.failed-{recovery_id}"
                )
                self._safe_state_path(failed, create_parents=True)
                try:
                    os.replace(temporary, failed)
                except OSError:
                    pass
            raise SnapshotExportError("REBUILD_REPLACE_FAILED") from exc
        self._write_snapshot()
        return {"status": "PASS", "recovery": recovery}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=None)
    subcommands = parser.add_subparsers(dest="command", required=True)
    def command(name: str) -> argparse.ArgumentParser:
        child = subcommands.add_parser(name)
        child.add_argument("--repo", dest="command_repo", default=None)
        child.add_argument("--json", action="store_true", help="emit JSON result or error")
        return child
    init = command("init")
    init.add_argument("--import-v5", action="store_true")
    register = command("register")
    register.add_argument("--file")
    reconcile = command("reconcile")
    reconcile.add_argument("--task")
    prepare = command("prepare-dispatch")
    prepare.add_argument("--task")
    prepare.add_argument("--sender")
    delivery = command("record-delivery")
    delivery.add_argument("--dispatch")
    delivery.add_argument("--phase")
    delivery.add_argument("--method")
    delivery.add_argument("--result")
    consume = command("consume-event")
    consume.add_argument("--file")
    command("doctor")
    command("rebuild")
    args = parser.parse_args()
    def payload(file_path: str | None = None) -> dict[str, Any]:
        if not file_path:
            return {}
        value = json.loads(Path(file_path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise IdentityError("PAYLOAD_INVALID")
        return value
    controller = Controller(args.command_repo or args.repo or ".")
    try:
        if args.command == "init":
            result = controller.init(args.import_v5)
        elif args.command == "register":
            data = payload(args.file)
            kind = data.pop("kind", None)
            if kind not in {"actor", "worktree", "task"}:
                raise IdentityError("REGISTER_KIND_INVALID")
            result = getattr(controller, f"register_{kind}")(**data)
        elif args.command == "reconcile":
            result = controller.reconcile(args.task)
        elif args.command == "prepare-dispatch":
            result = controller.prepare_dispatch(args.task, args.sender)
        elif args.command == "record-delivery":
            result = controller.record_delivery(args.dispatch, args.phase, args.method, args.result)
        elif args.command == "consume-event":
            result = controller.consume_event(payload(args.file))
        elif args.command == "doctor":
            result = controller.doctor()
        else:
            result = controller.rebuild()
    except (LoopError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(_json({"status": "ERROR", "error": str(exc)}))
        return 2
    print(_json(result))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
