from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOPCTL_PATH = ROOT / "skills" / "devad-x9-loop" / "scripts" / "loopctl.py"
ORIGINAL_SQLITE_CONNECT = sqlite3.connect


def load_loopctl():
    spec = importlib.util.spec_from_file_location("loopctl", LOOPCTL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LOOPCTL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [*args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def git_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    run("git", "init", "-b", "main", cwd=path)
    run("git", "config", "user.name", "X9 Test", cwd=path)
    run("git", "config", "user.email", "x9@example.invalid", cwd=path)
    (path / "src").mkdir()
    (path / "tests").mkdir()
    (path / "src" / "a.py").write_text("A = 1\n", encoding="utf-8")
    (path / "src" / "b.py").write_text("B = 1\n", encoding="utf-8")
    (path / "tests" / "test_a.py").write_text("def test_a(): pass\n", encoding="utf-8")
    run("git", "add", "src", "tests", cwd=path)
    run("git", "commit", "-m", "fixture", cwd=path)
    return run("git", "rev-parse", "HEAD", cwd=path).stdout.strip()


class LoopLiteCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loopctl = load_loopctl()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.base_sha = git_repo(self.repo)
        self.clock_value = "2026-07-13T12:00:00Z"
        self.controller = self.loopctl.Controller(
            self.repo, now_fn=lambda: self.clock_value
        )
        self.controller.init()
        self.owner_packet_path, self.owner_packet_sha256 = self.owner_packet_for(self.repo)
        self._raw_register_task = self.controller.register_task
        def register_with_owner(*args, **kwargs):
            if len(args) < 10 and "owner_packet_path" not in kwargs:
                worktree_id = kwargs.get("worktree_id")
                if worktree_id is None:
                    worktree_id = args[2]
                connection = self.controller._connect()
                try:
                    row = connection.execute("SELECT path FROM worktrees WHERE worktree_id=?", (worktree_id,)).fetchone()
                finally:
                    connection.close()
                if not row:
                    raise RuntimeError(f"unknown worktree {worktree_id}")
                packet_path, packet_sha256 = self.owner_packet_for(Path(row[0]))
                kwargs["owner_packet_path"] = packet_path
                kwargs["owner_packet_sha256"] = packet_sha256
            return self._raw_register_task(*args, **kwargs)
        self.controller.register_task = register_with_owner

    def owner_packet_for(self, root):
        artifacts = root / ".devad" / "manager" / "owner-packets" / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        attachment_bytes = b"owner context"
        attachment_sha256 = hashlib.sha256(attachment_bytes).hexdigest()
        attachment = artifacts / f"{attachment_sha256}.txt"
        attachment.write_bytes(attachment_bytes)
        packet = {"schema": "x9-owner-packet-v1", "owner_text": "keep owner context", "attachments": [{"path": attachment.relative_to(root).as_posix(), "sha256": attachment_sha256}]}
        data = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
        packet_sha256 = hashlib.sha256(data).hexdigest()
        packet_path = root / ".devad" / "manager" / "owner-packets" / f"{packet_sha256}.json"
        packet_path.write_bytes(data)
        return packet_path.relative_to(root).as_posix(), packet_sha256

    def build_result_event(self, task_id, dispatch_id, worker_id, packet_sha256, changed_files, event_id,
                           *, outcome="COMPLETE", proof=None, c1=None, c2=None, blocker=None, ack_delivery=True):
        connection = self.controller._connect()
        try:
            worktree = connection.execute(
                "SELECT w.path FROM tasks t JOIN worktrees w ON w.worktree_id=t.worktree_id WHERE t.task_id=?",
                (task_id,),
            ).fetchone()
        finally:
            connection.close()
        if not worktree:
            raise RuntimeError(f"unknown task {task_id}")
        connection = self.controller._connect()
        try:
            dispatch_status = connection.execute(
                "SELECT status FROM dispatches WHERE dispatch_id=?", (dispatch_id,)
            ).fetchone()
        finally:
            connection.close()
        if ack_delivery and dispatch_status and dispatch_status["status"] == "PREPARED":
            self.controller.record_delivery(
                dispatch_id, phase="DISPATCH", method="test-transport", result="acknowledged"
            )
        worktree_root = Path(worktree[0])
        result_path = worktree_root / ".devad" / "workers" / worker_id / "receipts" / f"{event_id}.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        if changed_files and proof is None:
            proof_root = worktree_root / ".devad" / "workers" / worker_id / "proof" / event_id
            proof_root.mkdir(parents=True, exist_ok=True)
            proof = []
            for kind in ("security", "tests"):
                proof_path = proof_root / f"{kind}.json"
                proof_document = {
                    "schema": "x9-loop-lite-proof-v1", "event_id": event_id, "task_id": task_id,
                    "dispatch_id": dispatch_id, "worker_id": worker_id, "role": "WORKER",
                    "kind": kind, "status": "PASS",
                }
                proof_path.write_text(json.dumps(proof_document, sort_keys=True, separators=(",", ":")), encoding="utf-8")
                proof.append({"path": proof_path.relative_to(worktree_root).as_posix(), "sha256": hashlib.sha256(proof_path.read_bytes()).hexdigest(), "kind": kind})
            for changed_file in changed_files:
                source = worktree_root / changed_file
                source.write_bytes(source.read_bytes() + b"# result fixture\\n")
            run("git", "add", *changed_files, *(item["path"] for item in proof), cwd=worktree_root)
            run("git", "commit", "-m", "claimed result", cwd=worktree_root)
            c1 = c1 or run("git", "rev-parse", "HEAD", cwd=worktree_root).stdout.strip()
            attestation = worktree_root / ".devad" / "docs" / "commits" / f"{c1}.md"
            attestation.parent.mkdir(parents=True, exist_ok=True)
            attestation.write_text(f"C1: {c1}\\n", encoding="utf-8")
            run("git", "add", attestation.relative_to(worktree_root).as_posix(), cwd=worktree_root)
            run("git", "commit", "-m", "attest result", cwd=worktree_root)
            c2 = c2 or run("git", "rev-parse", "HEAD", cwd=worktree_root).stdout.strip()
        result = {
            "schema": "x9-loop-lite-result-v1", "event_id": event_id, "task_id": task_id,
            "dispatch_id": dispatch_id, "worker_id": worker_id, "role": "WORKER",
            "packet_sha256": packet_sha256, "outcome": outcome, "changed_files": changed_files,
            "proof": [] if proof is None else proof, "c1": c1, "c2": c2, "blocker": blocker,
        }
        result_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return {
            "event_id": event_id, "event_type": "WORKER_RESULT", "task_id": task_id,
            "dispatch_id": dispatch_id, "actor_id": worker_id, "role": "WORKER",
            "packet_sha256": packet_sha256, "result_path": result_path.relative_to(worktree_root).as_posix(),
            "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        }

    def build_thinx_event(self, task_id, dispatch_id, actor_id, packet_sha256, event_id, decision="PASS", *, ack_review=True):
        connection = self.controller._connect()
        try:
            worktree = connection.execute(
                "SELECT w.path FROM tasks t JOIN worktrees w ON w.worktree_id=t.worktree_id WHERE t.task_id=?",
                (task_id,),
            ).fetchone()
        finally:
            connection.close()
        if not worktree:
            raise RuntimeError(f"unknown task {task_id}")
        connection = self.controller._connect()
        try:
            review_state = connection.execute(
                "SELECT t.status AS task_status,d.status AS dispatch_status FROM tasks t JOIN dispatches d ON d.task_id=t.task_id WHERE t.task_id=? AND d.dispatch_id=?",
                (task_id, dispatch_id),
            ).fetchone()
        finally:
            connection.close()
        if ack_review and review_state and review_state["task_status"] == "THINX_REVIEW_REQUIRED" and review_state["dispatch_status"] == "COMPLETE":
            self.controller.record_delivery(
                dispatch_id, phase="REVIEW", method="test-thinx", result="acknowledged"
            )
        worktree_root = Path(worktree[0])
        result_path = worktree_root / ".devad" / "workers" / actor_id / "receipts" / f"{event_id}.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        receipt = {
            "schema": "x9-loop-lite-thinx-decision-v1", "event_id": event_id, "task_id": task_id,
            "dispatch_id": dispatch_id, "actor_id": actor_id, "role": "THINX",
            "packet_sha256": packet_sha256, "decision": decision,
        }
        result_path.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return {
            "event_id": event_id, "event_type": "THINX_DECISION", "task_id": task_id,
            "dispatch_id": dispatch_id, "actor_id": actor_id, "role": "THINX",
            "packet_sha256": packet_sha256, "result_path": result_path.relative_to(worktree_root).as_posix(),
            "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        }
    def register_base(self):
        self.controller.register_actor(
            actor_id="linx-task", role="LINX", title="Linx v6", model="gpt-5.6-sol-high"
        )
        self.controller.register_actor(
            actor_id="worker-a", role="WORKER", title="Worker A", model="gpt-5.6-terra-high"
        )
        self.controller.register_worktree(
            worktree_id="wt-a", path=self.repo, repository_id="fixture"
        )
        self.controller.register_task(
            task_id="task-a",
            worker_id="worker-a",
            worktree_id="wt-a",
            base_sha=self.base_sha,
            claims=[{"path": "src/a.py", "kind": "file"}],
            resources=[],
            dependencies=[],
            finish_line="Focused test passes",
        )


class DatabaseAndSnapshotTests(LoopLiteCase):
    def test_init_rejects_loop_lite_junction_outside_repository(self):
        linked_repo = Path(self.temp.name) / "linked-repo"
        git_repo(linked_repo)
        manager = linked_repo / ".devad" / "manager"
        manager.mkdir(parents=True)
        outside = Path(self.temp.name) / "outside-state"
        outside.mkdir()
        state_link = manager / "loop-lite"
        if os.name == "nt":
            linked = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(state_link), str(outside)],
                capture_output=True,
                check=False,
            )
            if linked.returncode:
                self.skipTest("directory junctions unavailable")
        else:
            os.symlink(outside, state_link, target_is_directory=True)
        try:
            controller = self.loopctl.Controller(linked_repo)
            with self.assertRaisesRegex(self.loopctl.LoopError, "STATE_PATH_UNSAFE"):
                controller.init()
            self.assertEqual([], list(outside.iterdir()))
        finally:
            if os.name == "nt":
                os.rmdir(state_link)
            else:
                state_link.unlink(missing_ok=True)

    def test_init_creates_disposable_db_and_small_tracked_snapshot(self):
        root = self.repo / ".devad" / "manager" / "loop-lite"
        self.assertTrue((root / "loop.db").is_file())
        self.assertTrue((root / "SNAPSHOT.json").is_file())
        self.assertLess((root / "SNAPSHOT.json").stat().st_size, 8192)
        snapshot = json.loads((root / "SNAPSHOT.json").read_text(encoding="utf-8"))
        self.assertEqual("x9-loop-lite-snapshot-v1", snapshot["schema"])
        self.assertEqual(0, snapshot["generation"])

        connection = self.controller._connect()
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            for table in (
                "actors",
                "worktrees",
                "tasks",
                "claims",
                "dispatches",
                "events",
                "gates",
                "outbox",
                "metrics",
            ):
                self.assertIn(table, tables)
            self.assertEqual(1, connection.execute("PRAGMA foreign_keys").fetchone()[0])
            self.assertEqual("wal", connection.execute("PRAGMA journal_mode").fetchone()[0].lower())
        finally:
            connection.close()

    def test_v5_import_is_read_only_and_preserves_source_files(self):
        legacy = self.repo / ".devad" / "manager" / "loop"
        legacy.mkdir(parents=True)
        registry = legacy / "ROLE_REGISTRY.json"
        registry.write_text(
            json.dumps(
                {
                    "tasks": {
                        "old-worker": {
                            "role": "WORKER",
                            "title": "Old Worker",
                            "immutable": True,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        before = registry.read_bytes()
        imported = self.controller.init(import_v5=True)
        self.assertEqual(before, registry.read_bytes())
        self.assertEqual(1, imported["imported"]["actors"])

    def test_snapshot_failure_blocks_dispatch_until_reconciled(self):
        self.register_base()
        original = self.controller._write_snapshot

        def fail_snapshot():
            raise OSError("simulated snapshot export failure")

        self.controller._write_snapshot = fail_snapshot
        with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "SNAPSHOT_EXPORT_FAILED"):
            self.controller.register_actor(
                actor_id="reader", role="READER", title="Reader", model="cheap"
            )
        self.controller._write_snapshot = original
        with self.assertRaisesRegex(self.loopctl.StateNotDurableError, "SNAPSHOT_STALE"):
            self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        result = self.controller.reconcile()
        self.assertEqual("PASS", result["snapshot"])

    def test_rebuild_recovers_from_corrupt_db_without_deleting_it(self):
        self.register_base()
        db = self.controller.db_path
        db.write_bytes(b"not sqlite")
        result = self.controller.rebuild()
        self.assertEqual("PASS", result["status"])
        self.assertTrue(db.is_file())
        self.assertTrue(list(db.parent.glob("loop.db.corrupt-*")))
        connection = sqlite3.connect(db)
        try:
            self.assertEqual(
                1,
                connection.execute(
                    "SELECT COUNT(*) FROM tasks WHERE task_id='task-a'"
                ).fetchone()[0],
            )
        finally:
            connection.close()


class IdentityAndDispatchTests(LoopLiteCase):
    def test_module_does_not_monkey_patch_sqlite_connect(self):
        self.assertIs(ORIGINAL_SQLITE_CONNECT, sqlite3.connect)

    def test_role_title_detection_uses_token_boundaries(self):
        result = self.controller.register_actor(
            actor_id="worker-a", role="WORKER", title="Sidebar", model="terra"
        )
        self.assertEqual([], result["warnings"])

    def test_role_is_immutable_and_title_mismatch_is_reported(self):
        result = self.controller.register_actor(
            actor_id="worker-a", role="WORKER", title="Linx - paused", model="terra"
        )
        self.assertIn(
            "TITLE_ROLE_MISMATCH:worker-a:WORKER:Linx - paused", result["warnings"]
        )
        with self.assertRaisesRegex(self.loopctl.IdentityError, "ROLE_IMMUTABLE"):
            self.controller.register_actor(
                actor_id="worker-a", role="LINX", title="Linx", model="sol"
            )

    def test_prepare_dispatch_is_idempotent_and_action_is_small(self):
        self.register_base()
        first = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        second = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        self.assertEqual(first["dispatch_id"], second["dispatch_id"])
        self.assertTrue(first["dispatch_id"].startswith("dsp-"))
        self.assertEqual(first["packet_sha256"], second["packet_sha256"])
        action = self.controller.action_path
        self.assertLess(action.stat().st_size, 4096)
        payload = json.loads(action.read_text(encoding="utf-8"))
        self.assertEqual("SEND_DISPATCH", payload["action"])
        self.assertEqual("worker-a", payload["target_actor_id"])

    def test_action_is_runtime_only_after_snapshot_succeeds(self):
        self.register_base()
        self.assertEqual(
            self.repo / ".devad" / "manager" / "loop-lite" / "runtime" / "ACTION.json",
            self.controller.action_path,
        )
        original = self.controller._write_snapshot
        self.controller._write_snapshot = lambda: (_ for _ in ()).throw(OSError("snapshot"))
        with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "SNAPSHOT_EXPORT_FAILED"):
            self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        self.controller._write_snapshot = original
        self.assertFalse(self.controller.action_path.exists())

    def test_pending_and_blocked_gates_block_dispatch(self):
        self.register_base()
        self.controller.set_gate("task-a", "owner", "PENDING", "wait")
        with self.assertRaisesRegex(self.loopctl.TaskNotReadyError, "GATE_NOT_PASS"):
            self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        self.controller.set_gate("task-a", "owner", "BLOCKED", "stop")
        with self.assertRaisesRegex(self.loopctl.TaskNotReadyError, "GATE_NOT_PASS"):
            self.controller.prepare_dispatch("task-a", sender_id="linx-task")

    def test_changed_packet_supersedes_old_dispatch(self):
        self.register_base()
        first = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        self.controller.set_gate("task-a", "owner-approval", "PASS", "owner packet")
        second = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        self.assertNotEqual(first["dispatch_id"], second["dispatch_id"])
        self.assertEqual(first["dispatch_id"], second["supersedes"])
        connection = self.controller._connect()
        try:
            first_status = connection.execute(
                "SELECT status FROM dispatches WHERE dispatch_id=?", (first["dispatch_id"],)
            ).fetchone()[0]
            old_outbox = connection.execute(
                "SELECT 1 FROM outbox WHERE dispatch_id=?", (first["dispatch_id"],)
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual("SUPERSEDED", first_status)
        self.assertIsNotNone(old_outbox)
        action = json.loads(self.controller.action_path.read_text(encoding="utf-8"))
        self.assertEqual(second["dispatch_id"], action["dispatch_id"])

    def test_superseded_dispatch_event_cannot_complete_task(self):
        self.register_base()
        first = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        self.controller.set_gate("task-a", "owner-approval", "PASS", "owner packet")
        second = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        stale = self.build_result_event(
            "task-a", first["dispatch_id"], "worker-a", first["packet_sha256"], [], "evt-stale-dispatch"
        )
        with self.assertRaisesRegex(self.loopctl.StaleCompletionError, "STALE_COMPLETION"):
            self.controller.consume_event(stale)
        connection = self.controller._connect()
        try:
            self.assertEqual(
                "REGISTERED",
                connection.execute("SELECT status FROM tasks WHERE task_id='task-a'").fetchone()[0],
            )
            self.assertEqual(
                "PREPARED",
                connection.execute(
                    "SELECT status FROM dispatches WHERE dispatch_id=?", (second["dispatch_id"],)
                ).fetchone()[0],
            )
        finally:
            connection.close()

    def test_delivery_reports_real_attempts_and_one_callback_retry(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        did = dispatch["dispatch_id"]
        first = self.controller.record_delivery(
            did, phase="DISPATCH", method="codex-thread", result="accepted"
        )
        self.assertEqual("DELIVERY_UNCONFIRMED", first["status"])
        self.assertEqual(1, first["attempts"])
        self.assertFalse(first["sent_once"])

        callback_one = self.controller.record_delivery(
            did, phase="CALLBACK", method="codex-direct", result="failed"
        )
        self.assertEqual("RETRY_SAME_EVENT_ONCE", callback_one["next"])
        callback_two = self.controller.record_delivery(
            did, phase="CALLBACK", method="codex-direct", result="failed"
        )
        self.assertEqual("CALLBACK_FAILED", callback_two["status"])
        self.assertEqual("MANUAL_ONE_SHOT_PICKUP", callback_two["next"])
        with self.assertRaisesRegex(self.loopctl.DeliveryError, "CALLBACK_RETRY_LIMIT"):
            self.controller.record_delivery(
                did, phase="CALLBACK", method="codex-direct", result="failed"
            )


class ClaimsAndSchedulingTests(LoopLiteCase):
    def test_windows_paths_are_canonical_and_overlaps_are_rejected(self):
        self.controller.register_actor("worker-a", "WORKER", "Worker A", "terra")
        self.controller.register_actor("worker-b", "WORKER", "Worker B", "terra")
        self.controller.register_worktree("wt-a", self.repo, "fixture")
        self.controller.register_worktree("wt-b", self.repo, "fixture")
        self.controller.register_task(
            "task-a",
            "worker-a",
            "wt-a",
            self.base_sha,
            [{"path": "Src\\Feature", "kind": "dir"}],
            [],
            [],
            "done",
        )
        with self.assertRaisesRegex(self.loopctl.ClaimConflictError, "CLAIM_CONFLICT"):
            self.controller.register_task(
                "task-b",
                "worker-b",
                "wt-b",
                self.base_sha,
                [{"path": "src/feature/item.py", "kind": "file"}],
                [],
                [],
                "done",
            )

    def test_exclusive_resources_are_serialized(self):
        self.controller.register_actor("worker-a", "WORKER", "Worker A", "terra")
        self.controller.register_actor("worker-b", "WORKER", "Worker B", "terra")
        self.controller.register_worktree("wt-a", self.repo, "fixture")
        self.controller.register_worktree("wt-b", self.repo, "fixture")
        self.controller.register_task(
            "task-a", "worker-a", "wt-a", self.base_sha,
            [{"path": "src/a.py", "kind": "file"}], ["browser-profile:default"], [], "done"
        )
        with self.assertRaisesRegex(self.loopctl.ResourceConflictError, "RESOURCE_CONFLICT"):
            self.controller.register_task(
                "task-b", "worker-b", "wt-b", self.base_sha,
                [{"path": "src/b.py", "kind": "file"}], ["BROWSER-PROFILE:DEFAULT"], [], "done"
            )

    def test_rollout_limit_is_one_then_two_then_three(self):
        healthy = {
            "lost_work": 0,
            "duplicate_delivery": 0,
            "stale_completion": 0,
            "scope_breach": 0,
            "parser_failure": 0,
            "orphan_lock": 0,
            "false_pass": 0,
            "context_compaction": 0,
        }
        self.assertEqual(1, self.loopctl.coding_limit(0, healthy))
        self.assertEqual(1, self.loopctl.coding_limit(2, healthy))
        self.assertEqual(2, self.loopctl.coding_limit(3, healthy))
        self.assertEqual(2, self.loopctl.coding_limit(9, healthy))
        self.assertEqual(3, self.loopctl.coding_limit(10, healthy))
        unhealthy = dict(healthy, scope_breach=1)
        self.assertEqual(1, self.loopctl.coding_limit(10, unhealthy))

    def test_dependency_and_claim_expansion_gate(self):
        self.register_base()
        self.controller.register_actor("worker-b", "WORKER", "Worker B", "terra")
        self.controller.register_worktree("wt-b", self.repo, "fixture")
        self.controller.register_task(
            "task-b", "worker-b", "wt-b", self.base_sha,
            [{"path": "src/b.py", "kind": "file"}], [], ["task-a"], "done"
        )
        with self.assertRaisesRegex(self.loopctl.TaskNotReadyError, "DEPENDENCY_NOT_COMPLETE"):
            self.controller.prepare_dispatch("task-b", sender_id="linx-task")
        request = self.controller.request_claim_expansion("task-a", "tests/new_test.py")
        self.assertEqual("CLAIM_EXPANSION_REQUEST", request["status"])
        self.assertEqual("PENDING", request["gate_status"])


class ReconcileAndCompletionTests(LoopLiteCase):
    def test_reconcile_classifies_git_paths_without_overwriting_them(self):
        self.register_base()
        (self.repo / "src" / "a.py").write_text("A = 2\n", encoding="utf-8")
        (self.repo / "src" / "b.py").write_text("B = 2\n", encoding="utf-8")
        run("git", "add", "src/a.py", cwd=self.repo)
        before_a = (self.repo / "src" / "a.py").read_bytes()
        before_b = (self.repo / "src" / "b.py").read_bytes()
        result = self.controller.reconcile("task-a")
        self.assertEqual(["src/a.py"], result["git"]["staged"])
        self.assertEqual(["src/b.py"], result["git"]["unstaged"])
        self.assertEqual(["src/b.py"], result["scope_breach"])
        self.assertEqual(before_a, (self.repo / "src" / "a.py").read_bytes())
        self.assertEqual(before_b, (self.repo / "src" / "b.py").read_bytes())

    def test_completion_rejects_stale_identity_duplicate_and_scope_breach(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        did = dispatch["dispatch_id"]
        self.controller.record_delivery(did, "DISPATCH", "codex-thread", "accepted")
        event = self.build_result_event(
            "task-a", did, "worker-a", dispatch["packet_sha256"], [], "evt-1"
        )
        first = self.controller.consume_event(event)
        self.assertEqual("CONSUMED", first["status"])
        duplicate = self.controller.consume_event(event)
        self.assertEqual("DUPLICATE_EVENT", duplicate["status"])
        stale = dict(event, event_id="evt-2", packet_sha256="0" * 64)
        with self.assertRaisesRegex(self.loopctl.StaleCompletionError, "STALE_COMPLETION"):
            self.controller.consume_event(stale)

    def test_unclaimed_result_path_is_scope_breach(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", sender_id="linx-task")
        event = self.build_result_event(
            task_id="task-a",
            dispatch_id=dispatch["dispatch_id"],
            worker_id="worker-a",
            packet_sha256=dispatch["packet_sha256"],
            changed_files=["src/b.py"],
            event_id="evt-breach",
        )
        with self.assertRaisesRegex(self.loopctl.ScopeBreachError, "SCOPE_BREACH:src/b.py"):
            self.controller.consume_event(event)


class DoctorAndCliTests(LoopLiteCase):
    def test_doctor_is_read_only_and_reports_unknown_token_telemetry(self):
        self.register_base()
        db_before = self.controller.db_path.read_bytes()
        snapshot_before = self.controller.snapshot_path.read_bytes()
        result = self.controller.doctor()
        self.assertEqual("Unknown", result["metrics"]["token_telemetry"])
        self.assertEqual(db_before, self.controller.db_path.read_bytes())
        self.assertEqual(snapshot_before, self.controller.snapshot_path.read_bytes())

    def test_cli_exposes_all_required_commands(self):
        help_run = run(sys.executable, str(LOOPCTL_PATH), "--help", cwd=self.repo)
        for command in (
            "init",
            "register",
            "reconcile",
            "prepare-dispatch",
            "record-delivery",
            "consume-event",
            "doctor",
            "rebuild",
        ):
            self.assertIn(command, help_run.stdout)


class ProductionRegressionTests(LoopLiteCase):
    def add_task(self, task_id, worker_id, claim, resource=None):
        self.controller.register_actor(worker_id, "WORKER", worker_id, "terra")
        self.controller.register_worktree(f"wt-{task_id}", self.repo, "fixture")
        self.controller.register_task(
            task_id,
            worker_id,
            f"wt-{task_id}",
            self.base_sha,
            [{"path": claim, "kind": "file"}],
            [resource] if resource else [],
            [],
            "done",
        )

    def complete_task(self, task_id, worker_id):
        dispatch = self.controller.prepare_dispatch(task_id, "linx-task")
        event = self.build_result_event(
            task_id, dispatch["dispatch_id"], worker_id, dispatch["packet_sha256"], [], f"evt-{task_id}"
        )
        return self.controller.consume_event(event)

    def test_completed_tasks_release_claims_and_resources(self):
        self.controller.register_actor("linx-task", "LINX", "Linx", "sol")
        self.add_task("task-a", "worker-a", "src/a.py", "browser:default")
        self.complete_task("task-a", "worker-a")
        self.add_task("task-b", "worker-b", "src/a.py", "browser:default")

    def test_prepare_dispatch_enforces_rollout_capacity(self):
        self.controller.register_actor("linx-task", "LINX", "Linx", "sol")
        for index, letter in enumerate("abcde"):
            self.add_task(f"task-{letter}", f"worker-{letter}", f"src/{letter}.py")
        self.controller.prepare_dispatch("task-a", "linx-task")
        with self.assertRaisesRegex(self.loopctl.TaskNotReadyError, "CODING_LIMIT"):
            self.controller.prepare_dispatch("task-b", "linx-task")
        self.complete_task("task-a", "worker-a")
        self.controller.prepare_dispatch("task-b", "linx-task")
        self.complete_task("task-b", "worker-b")
        self.controller.prepare_dispatch("task-c", "linx-task")
        self.complete_task("task-c", "worker-c")
        self.controller.prepare_dispatch("task-d", "linx-task")
        self.controller.prepare_dispatch("task-e", "linx-task")

    def test_reconcile_reports_all_git_categories_and_never_false_clean(self):
        self.register_base()
        (self.repo / "src" / "a.py").write_text("A = 2\n", encoding="utf-8")
        run("git", "add", "src/a.py", cwd=self.repo)
        run("git", "commit", "-m", "after-base", cwd=self.repo)
        (self.repo / "src" / "b.py").write_text("B = 2\n", encoding="utf-8")
        run("git", "add", "src/b.py", cwd=self.repo)
        (self.repo / "tests" / "test_a.py").write_text("changed\n", encoding="utf-8")
        (self.repo / "scratch.txt").write_text("untracked\n", encoding="utf-8")
        result = self.controller.reconcile("task-a")
        self.assertEqual(["src/b.py"], result["git"]["staged"])
        self.assertEqual(["tests/test_a.py"], result["git"]["unstaged"])
        self.assertEqual(["scratch.txt"], result["git"]["untracked"])
        self.assertEqual(["src/a.py"], result["git"]["committed"])
        self.controller._run_git = lambda *args: subprocess.CompletedProcess(args, 1, "", "broken")
        with self.assertRaisesRegex(self.loopctl.GitStateError, "GIT_STATE_UNKNOWN"):
            self.controller.reconcile("task-a")

    def test_consume_event_binds_dispatch_to_task_and_checks_actual_git_scope(self):
        self.register_base()
        self.add_task("task-b", "worker-b", "src/b.py")
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        wrong_task = self.build_result_event(
            "task-b", dispatch["dispatch_id"], "worker-b", dispatch["packet_sha256"], ["src/b.py"], "evt-wrong-task", proof=[]
        )
        with self.assertRaisesRegex(self.loopctl.StaleCompletionError, "STALE_COMPLETION"):
            self.controller.consume_event(wrong_task)
        (self.repo / wrong_task["result_path"]).unlink()
        (self.repo / "src" / "b.py").write_text("B = 2\n", encoding="utf-8")
        hidden_change = self.build_result_event(
            "task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], ["src/a.py"], "evt-hidden-change"
        )
        with self.assertRaisesRegex(self.loopctl.ScopeBreachError, "SCOPE_BREACH:src/b.py"):
            self.controller.consume_event(hidden_change)

    def test_default_timestamp_is_real_utc(self):
        controller = self.loopctl.Controller(self.repo)
        controller.register_actor("linx-task", "LINX", "Linx", "sol")
        controller.register_actor("worker-a", "WORKER", "Worker", "terra")
        controller.register_worktree("wt-a", self.repo, "fixture")
        controller.register_task("task-a", "worker-a", "wt-a", self.base_sha, [{"path": "src/a.py", "kind": "file"}], [], [], "done", self.owner_packet_path, self.owner_packet_sha256)
        dispatch = controller.prepare_dispatch("task-a", "linx-task")
        connection = controller._connect()
        try:
            timestamp = connection.execute("SELECT created_at FROM dispatches WHERE dispatch_id=?", (dispatch["dispatch_id"],)).fetchone()[0]
        finally:
            connection.close()
        self.assertRegex(timestamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

    def test_rebuild_rejects_untrusted_snapshot_table_names(self):
        self.register_base()
        snapshot = json.loads(self.controller.snapshot_path.read_text(encoding="utf-8"))
        snapshot["tables"]["sqlite_master"] = []
        self.controller.snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        self.controller.db_path.write_bytes(b"not sqlite")
        with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "SNAPSHOT_TABLE_UNKNOWN"):
            self.controller.rebuild()

class SecondProductionReviewTests(LoopLiteCase):
    def test_scope_excludes_only_controller_runtime_and_validated_result(self):
        self.register_base()
        (self.repo / ".devad" / "features").mkdir(parents=True)
        (self.repo / ".devad" / "features" / "unsafe.md").write_text("x", encoding="utf-8")
        (self.repo / ".devad" / "manager" / "workers").mkdir(parents=True)
        (self.repo / ".devad" / "manager" / "workers" / "unsafe.md").write_text("x", encoding="utf-8")
        result = self.controller.reconcile("task-a")
        self.assertIn(".devad/features/unsafe.md", result["scope_breach"])
        self.assertIn(".devad/manager/workers/unsafe.md", result["scope_breach"])
        self.assertNotIn(".devad/manager/loop-lite/loop.db", result["scope_breach"])

    def test_tampered_snapshot_is_not_hidden_as_controller_runtime(self):
        self.register_base()
        self.controller.snapshot_path.write_text("{}", encoding="utf-8")
        result = self.controller.reconcile("task-a")
        self.assertIn(".devad/manager/loop-lite/snapshot.json", result["scope_breach"])

    def test_duplicate_event_returns_before_git_read(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event(
            "task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], [], "evt-duplicate"
        )
        self.assertEqual("CONSUMED", self.controller.consume_event(event)["status"])
        self.controller._run_git = lambda *args: (_ for _ in ()).throw(self.loopctl.GitStateError("GIT_STATE_UNKNOWN"))
        self.assertEqual("DUPLICATE_EVENT", self.controller.consume_event(event)["status"])

    def test_action_contains_complete_immutable_packet_and_size_guard(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        action = json.loads(self.controller.action_path.read_text(encoding="utf-8"))
        for key in ("schema", "action_id", "action", "dispatch_id", "task_id", "target_actor_id", "target_role", "packet_sha256", "attempt", "packet"):
            self.assertIn(key, action)
        self.assertEqual(dispatch["dispatch_id"], action["dispatch_id"])
        self.assertEqual("WORKER", action["target_role"])
        for key in ("worktree_id", "worktree_path", "base_sha", "dependencies", "claims", "resources", "gates", "finish_line"):
            self.assertIn(key, action["packet"])
        self.assertLess(self.controller.action_path.stat().st_size, 4096)
        self.controller._transition_task_state("task-a", "COMPLETE")
        self.controller.register_actor("worker-b", "WORKER", "Worker B", "terra")
        self.controller.register_worktree("wt-b", self.repo, "fixture")
        self.controller.register_task("task-b", "worker-b", "wt-b", self.base_sha, [{"path": "src/b.py", "kind": "file"}], [], [], "x" * 4500)
        with self.assertRaisesRegex(self.loopctl.LoopError, "ACTION_TOO_LARGE"):
            self.controller.prepare_dispatch("task-b", "linx-task")
        self.assertFalse((self.controller.action_path.parent / "ACTION-task-b.json").exists())

    def test_snapshot_stays_small_after_ten_completed_dispatches(self):
        self.controller.register_actor("linx-task", "LINX", "Linx", "sol")
        for index in range(11):
            worker = f"worker-{index}"
            task = f"task-{index}"
            self.controller.register_actor(worker, "WORKER", worker, "terra")
            self.controller.register_worktree(f"wt-{index}", self.repo, "fixture")
            self.controller.register_task(task, worker, f"wt-{index}", self.base_sha, [{"path": f"src/{index}.py", "kind": "file"}], [], [], "done")
            if index < 10:
                self.controller.prepare_dispatch(task, "linx-task")
                self.controller._transition_task_state(task, "COMPLETE")
        self.controller.prepare_dispatch("task-10", "linx-task")
        self.assertLess(self.controller.snapshot_path.stat().st_size, 8192)
        snapshot = json.loads(self.controller.snapshot_path.read_text(encoding="utf-8"))
        self.assertLessEqual(len(snapshot["tables"]["dispatches"]), 1)
        self.assertEqual([], snapshot["tables"]["outbox"])

    def test_import_v5_migrates_valid_rows_without_writing_legacy_files(self):
        legacy = self.repo / ".devad" / "manager" / "loop"
        legacy.mkdir(parents=True)
        files = {
            "ROLE_REGISTRY.json": {"tasks": {"linx-v5": {"role": "LINX", "title": "Linx"}, "worker-v5": {"role": "WORKER", "title": "Worker"}}},
            "WORKTREE_INDEX.json": {"worktrees": {"wt-v5": {"path": str(self.repo), "repository_id": "fixture"}}},
            "TASK_GRAPH.json": {"tasks": {"task-v5": {"worker_id": "worker-v5", "worktree_id": "wt-v5", "base_sha": self.base_sha, "dependencies": [], "finish_line": "done"}, "skip-v5": {"worker_id": "missing"}}},
            "RESOURCE_CLAIMS.json": {"tasks": {"task-v5": {"claims": [{"path": "src/a.py", "kind": "file"}], "resources": []}}},
            "DECISION_GATES.json": {"tasks": {"task-v5": {"gates": {"owner": {"status": "PASS", "note": "ok"}}}}},
        }
        before = {}
        for name, value in files.items():
            path = legacy / name
            path.write_text(json.dumps(value), encoding="utf-8")
            before[name] = path.read_bytes()
        result = self.controller.init(import_v5=True)
        self.assertEqual(2, result["imported"]["actors"])
        self.assertEqual(1, result["imported"]["worktrees"])
        self.assertEqual(1, result["imported"]["tasks"])
        self.assertGreaterEqual(result["skipped"], 1)
        for name, data in before.items():
            self.assertEqual(data, (legacy / name).read_bytes())
        connection = self.controller._connect()
        try:
            self.assertEqual("PASS", connection.execute("SELECT status FROM gates WHERE task_id='task-v5' AND name='owner'").fetchone()[0])
        finally:
            connection.close()

    def test_cli_supports_documented_safe_flags(self):
        self.register_base()
        register_file = Path(self.temp.name) / "register.json"
        register_file.write_text(json.dumps({"kind": "actor", "actor_id": "reader", "role": "READER", "title": "Reader", "model": "cheap"}), encoding="utf-8")
        run(sys.executable, str(LOOPCTL_PATH), "register", "--repo", str(self.repo), "--file", str(register_file), cwd=self.repo)
        run(sys.executable, str(LOOPCTL_PATH), "reconcile", "--repo", str(self.repo), "--task", "task-a", cwd=self.repo)
        prepared = run(sys.executable, str(LOOPCTL_PATH), "prepare-dispatch", "--repo", str(self.repo), "--task", "task-a", "--sender", "linx-task", cwd=self.repo)
        dispatch = json.loads(prepared.stdout)
        run(sys.executable, str(LOOPCTL_PATH), "record-delivery", "--repo", str(self.repo), "--dispatch", dispatch["dispatch_id"], "--phase", "DISPATCH", "--method", "test", "--result", "accepted", cwd=self.repo)
        event = self.build_result_event("task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], [], "evt-cli")
        event_file = Path(self.temp.name) / "event.json"
        event_file.write_text(json.dumps(event), encoding="utf-8")
        run(sys.executable, str(LOOPCTL_PATH), "consume-event", "--repo", str(self.repo), "--file", str(event_file), cwd=self.repo)
        run(sys.executable, str(LOOPCTL_PATH), "init", "--repo", str(self.repo), "--import-v5", cwd=self.repo)

    def test_linked_worktrees_are_real_isolated_git_scopes(self):
        worktrees = [self.repo.parent / name for name in ("linked-a", "linked-b", "linked-c")]
        for index, worktree in enumerate(worktrees):
            run("git", "worktree", "add", "-b", f"task-{index}", str(worktree), "HEAD", cwd=self.repo)
        self.controller.register_actor("linx-task", "LINX", "Linx", "sol")
        for index, worktree in enumerate(worktrees):
            worker = f"worker-{index}"
            self.controller.register_actor(worker, "WORKER", worker, "terra")
            self.controller.register_worktree(f"wt-{index}", worktree, "fixture")
            self.controller.register_task(f"task-{index}", worker, f"wt-{index}", self.base_sha, [{"path": f"src/{chr(97 + index)}.py", "kind": "file"}], ["integration:default"] if index == 0 else [], [], "done")
        self.controller.register_actor("worker-extra", "WORKER", "extra", "terra")
        self.controller.register_worktree("wt-extra", worktrees[0], "fixture")
        with self.assertRaisesRegex(self.loopctl.ResourceConflictError, "RESOURCE_CONFLICT"):
            self.controller.register_task("task-extra", "worker-extra", "wt-extra", self.base_sha, [{"path": "tests/test_a.py", "kind": "file"}], ["integration:default"], [], "done")
        with self.assertRaisesRegex(self.loopctl.ClaimConflictError, "CLAIM_CONFLICT"):
            self.controller.register_task("task-overlap", "worker-extra", "wt-extra", self.base_sha, [{"path": "src/a.py", "kind": "file"}], [], [], "done")
        dispatch = self.controller.prepare_dispatch("task-0", "linx-task")
        with self.assertRaisesRegex(self.loopctl.TaskNotReadyError, "CODING_LIMIT"):
            self.controller.prepare_dispatch("task-1", "linx-task")
        (worktrees[1] / "src" / "b.py").write_text("B = 2\n", encoding="utf-8")
        self.assertEqual([], self.controller.reconcile("task-0")["scope_breach"])
        self.assertEqual(["src/b.py"], self.controller.reconcile("task-1")["git"]["unstaged"])
        event = self.build_result_event("task-0", dispatch["dispatch_id"], "worker-0", dispatch["packet_sha256"], [], "evt-linked")
        self.assertTrue((worktrees[0] / event["result_path"]).is_file())
        self.assertEqual("CONSUMED", self.controller.consume_event(event)["status"])

    def test_generated_status_and_handoffs_are_bounded_non_authoritative_views(self):
        status = self.repo / ".devad" / "manager" / "loop-lite" / "runtime" / "STATUS.md"
        handoffs = self.repo / ".devad" / "manager" / "loop-lite" / "runtime" / "HANDOFFS.md"
        for path in (status, handoffs):
            self.assertTrue(path.is_file())
            self.assertLessEqual(len(path.read_text(encoding="utf-8").splitlines()), 120)
            self.assertLess(path.stat().st_size, 12288)
            self.assertIn("Generated", path.read_text(encoding="utf-8"))
            self.assertIn("not parser authority", path.read_text(encoding="utf-8"))
        self.register_base()
        status.write_text("tampered status", encoding="utf-8")
        handoffs.write_text("tampered handoff", encoding="utf-8")
        self.controller.prepare_dispatch("task-a", "linx-task")
        before = (status.read_bytes(), handoffs.read_bytes())
        self.controller.doctor()
        self.assertEqual(before, (status.read_bytes(), handoffs.read_bytes()))
        self.controller.reconcile("task-a")
        self.assertIn("Generated", status.read_text(encoding="utf-8"))
        self.assertIn("Generated", handoffs.read_text(encoding="utf-8"))

    def test_no_public_test_only_state_mutator(self):
        public_methods = [
            name for name, value in inspect.getmembers(self.loopctl.Controller, inspect.isfunction)
            if not name.startswith("_")
        ]
        self.assertFalse([name for name in public_methods if "for_test" in name])
        for name in public_methods:
            source = inspect.getsource(getattr(self.loopctl.Controller, name))
            self.assertFalse("RESULT.json" in source and any(marker in source for marker in (".write_text", ".write_bytes", ".mkdir")))


class FinalProductionSafetyTests(LoopLiteCase):
    def test_reconcile_materializes_a_current_action_without_model_choice(self):
        self.register_base()
        self.controller.reconcile("task-a")
        self.assertEqual("NOOP", json.loads(self.controller.action_path.read_text(encoding="utf-8"))["action"])
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        self.controller.action_path.unlink()
        self.controller.reconcile("task-a")
        action = json.loads(self.controller.action_path.read_text(encoding="utf-8"))
        self.assertEqual("SEND_DISPATCH", action["action"])
        self.assertEqual(dispatch["dispatch_id"], action["dispatch_id"])
        event = self.build_result_event("task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], [], "evt-current")
        self.controller.consume_event(event)
        self.controller.reconcile("task-a")
        self.assertEqual("NOOP", json.loads(self.controller.action_path.read_text(encoding="utf-8"))["action"])

    def test_doctor_is_read_only_and_fails_durable_integrity_checks(self):
        self.register_base()
        snapshot = json.loads(self.controller.snapshot_path.read_text(encoding="utf-8"))
        snapshot["generation"] += 1
        self.controller.snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        db_before = self.controller.db_path.read_bytes()
        snapshot_before = self.controller.snapshot_path.read_bytes()
        result = self.controller.doctor()
        self.assertEqual("FAIL", result["status"])
        self.assertFalse(result["durable"])
        for key in ("integrity_check", "foreign_key_check", "snapshot", "action", "worktrees", "receipts", "conflicts"):
            self.assertIn(key, result["checks"])
        self.assertEqual(db_before, self.controller.db_path.read_bytes())
        self.assertEqual(snapshot_before, self.controller.snapshot_path.read_bytes())

    def test_rebuild_validates_before_preserving_old_db_and_snapshot_history_stays_bounded(self):
        self.register_base()
        snapshot = json.loads(self.controller.snapshot_path.read_text(encoding="utf-8"))
        snapshot["tables"]["tasks"][0]["unexpected_column"] = "unsafe"
        self.controller.snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        self.controller.db_path.write_bytes(b"corrupt-but-preserved")
        with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "SNAPSHOT_COLUMN_UNKNOWN"):
            self.controller.rebuild()
        self.assertEqual(b"corrupt-but-preserved", self.controller.db_path.read_bytes())

        bounded_repo = Path(self.temp.name) / "bounded-repo"
        bounded_base = git_repo(bounded_repo)
        bounded = self.loopctl.Controller(bounded_repo, now_fn=lambda: self.clock_value)
        bounded.init()
        bounded_owner_path, bounded_owner_sha = self.owner_packet_for(bounded_repo)
        bounded.register_actor("linx-task", "LINX", "Linx", "sol")
        for index in range(32):
            worker = f"bounded-{index}"
            task = f"bounded-task-{index}"
            bounded.register_actor(worker, "WORKER", worker, "terra")
            bounded.register_worktree(f"bounded-wt-{index}", bounded_repo, "fixture")
            bounded.register_task(task, worker, f"bounded-wt-{index}", bounded_base, [{"path": f"src/bounded-{index}.py", "kind": "file"}], [], [], "done", bounded_owner_path, bounded_owner_sha)
            bounded._transition_task_state(task, "COMPLETE")
        self.assertLess(bounded.snapshot_path.stat().st_size, 8192)
        compact = json.loads(bounded.snapshot_path.read_text(encoding="utf-8"))
        self.assertLessEqual(len(compact["tables"]["tasks"]), 1)
        self.assertLessEqual(len(compact["completed_task_ids"]), 16)

    def test_strict_worker_and_thinx_receipts(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        malformed = self.build_result_event(
            "task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], ["src/a.py"], "evt-malformed",
            proof=[], c1=None, c2=None,
        )
        with self.assertRaisesRegex(self.loopctl.StaleCompletionError, "RESULT_INVALID"):
            self.controller.consume_event(malformed)
        (self.repo / malformed["result_path"]).unlink()
        blocked = self.build_result_event(
            "task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], [], "evt-blocked",
            outcome="BLOCKED", blocker="waiting",
        )
        self.assertEqual("RETRY_READY", self.controller.consume_event(blocked)["status"])
        connection = self.controller._connect()
        try:
            self.assertEqual("RETRY_READY", connection.execute("SELECT status FROM tasks WHERE task_id='task-a'").fetchone()[0])
        finally:
            connection.close()

        self.controller.register_actor("thinx-a", "THINX", "Thinx", "sol")
        self.controller._transition_task_state("task-a", "THINX_REVIEW_REQUIRED")
        thinx = self.build_thinx_event("task-a", dispatch["dispatch_id"], "thinx-a", dispatch["packet_sha256"], "evt-thinx")
        self.assertEqual("THINX_CONSUMED", self.controller.consume_event(thinx)["status"])
        with self.assertRaisesRegex(self.loopctl.StaleCompletionError, "EVENT_INVALID"):
            self.controller.consume_event({"event_id": "bad"})

    def test_claim_validation_preserves_worktree_path_and_git_timeout_is_controlled(self):
        self.controller.register_actor("worker-a", "WORKER", "Worker", "terra")
        self.controller.register_worktree("wt-a", self.repo, "fixture")
        connection = self.controller._connect()
        try:
            stored = connection.execute("SELECT path FROM worktrees WHERE worktree_id='wt-a'").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(str(self.repo.resolve()), stored)
        for index, claim in enumerate(("*.py", "C:/repo/file.py", "/repo/file.py", ".", "src/a.py")):
            kind = "invalid" if claim == "src/a.py" else "file"
            with self.assertRaisesRegex(self.loopctl.ScopeBreachError, "INVALID_(PATH|CLAIM_KIND)"):
                self.controller.register_task(f"invalid-{index}", "worker-a", "wt-a", self.base_sha, [{"path": claim, "kind": kind}], [], [], "done")
        seen = {}
        def timeout(*args, **kwargs):
            seen.update(kwargs)
            raise subprocess.TimeoutExpired(args[0], kwargs.get("timeout"))
        original = self.loopctl.subprocess.run
        self.loopctl.subprocess.run = timeout
        try:
            with self.assertRaisesRegex(self.loopctl.GitStateError, "GIT_STATE_UNKNOWN"):
                self.controller._run_git(["status"])
        finally:
            self.loopctl.subprocess.run = original
        self.assertLessEqual(seen["timeout"], 10)

    def test_delivery_retry_updates_action_and_cli_json_is_boolean_output_mode(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        first = self.controller.record_delivery(dispatch["dispatch_id"], "DISPATCH", "test", "failed")
        self.assertEqual(1, first["attempts"])
        action = json.loads(self.controller.action_path.read_text(encoding="utf-8"))
        self.assertEqual(dispatch["dispatch_id"], action["dispatch_id"])
        self.assertEqual(2, action["attempt"])
        second = self.controller.record_delivery(dispatch["dispatch_id"], "DISPATCH", "test", "acknowledged")
        self.assertEqual(2, second["attempts"])
        connection = self.controller._connect()
        try:
            self.assertEqual("DISPATCHED", connection.execute("SELECT status FROM dispatches WHERE dispatch_id=?", (dispatch["dispatch_id"],)).fetchone()[0])
        finally:
            connection.close()
        cli = run(sys.executable, str(LOOPCTL_PATH), "doctor", "--repo", str(self.repo), "--json", cwd=self.repo)
        self.assertIn("status", json.loads(cli.stdout))

class RecoveryAndProofEdgesTests(LoopLiteCase):
    def test_rebuild_retains_completed_worktree_and_recovers_receipt_git_evidence(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event("task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], [], "evt-recovery")
        self.assertEqual("CONSUMED", self.controller.consume_event(event)["status"])
        snapshot = json.loads(self.controller.snapshot_path.read_text(encoding="utf-8"))
        self.assertIn({"worktree_id": "wt-a", "path": str(self.repo.resolve())}, snapshot["recovery_worktrees"])
        self.controller.db_path.write_bytes(b"corrupt")
        rebuilt = self.controller.rebuild()
        self.assertEqual(1, rebuilt["recovery"]["receipts"])
        self.assertGreaterEqual(rebuilt["recovery"]["git_paths"], 1)
        self.assertIn("recovery", self.controller.reconcile())
        receipt = self.repo / event["result_path"]
        receipt.write_text("{bad", encoding="utf-8")
        self.controller.db_path.write_bytes(b"corrupt-again")
        with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "RECOVERY_RECEIPT_INVALID"):
            self.controller.rebuild()

    def test_rebuild_rejects_receipt_symlink_outside_worktree(self):
        self.register_base()
        outside_dir = self.repo.parent / "outside-receipts"
        outside_dir.mkdir()
        outside = outside_dir / "evt-link.json"
        outside.write_text(
            json.dumps({"schema": "x9-loop-lite-result-v1", "event_id": "evt-link"}),
            encoding="utf-8",
        )
        receipts = self.repo / ".devad" / "workers" / "worker-a" / "receipts"
        receipts.parent.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            linked = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(receipts), str(outside_dir)],
                capture_output=True,
                check=False,
            )
            if linked.returncode:
                outside.unlink(missing_ok=True)
                outside_dir.rmdir()
                self.skipTest("directory junctions unavailable")
        else:
            os.symlink(outside_dir, receipts, target_is_directory=True)
        try:
            self.controller.db_path.write_bytes(b"corrupt")
            with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "RECOVERY_RECEIPT_INVALID"):
                self.controller.rebuild()
        finally:
            if os.name == "nt":
                os.rmdir(receipts)
            else:
                receipts.unlink(missing_ok=True)
            outside.unlink(missing_ok=True)
            outside_dir.rmdir()
    def test_complete_requires_exact_worker_owned_security_and_tests_proofs(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event("task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], ["src/a.py"], "evt-proof-contract")
        receipt_path = self.repo / event["result_path"]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        proof_root = ".devad/workers/worker-a/proof/evt-proof-contract"
        self.assertEqual(
            {f"{proof_root}/security.json", f"{proof_root}/tests.json"},
            {item["path"] for item in receipt["proof"]},
        )
        source_hash = hashlib.sha256((self.repo / "src" / "a.py").read_bytes()).hexdigest()
        receipt["proof"] = [
            {"path": "src/a.py", "sha256": source_hash, "kind": "security"},
            {"path": "src/a.py", "sha256": source_hash, "kind": "tests"},
        ]
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        event["result_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(self.loopctl.StaleCompletionError, "RESULT_INVALID"):
            self.controller.consume_event(event)

    def test_empty_complete_rejects_non_system_devad_paths(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        hidden = self.repo / ".devad" / "features" / "unclaimed.json"
        hidden.parent.mkdir(parents=True, exist_ok=True)
        hidden.write_text("{}", encoding="utf-8")
        event = self.build_result_event("task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], [], "evt-empty-feature")
        with self.assertRaisesRegex(self.loopctl.ScopeBreachError, "SCOPE_BREACH"):
            self.controller.consume_event(event)

class SecurityBoundaryRegressionTests(LoopLiteCase):
    def test_worker_result_requires_dispatch_acknowledgement(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event(
            "task-a",
            dispatch["dispatch_id"],
            "worker-a",
            dispatch["packet_sha256"],
            [],
            "evt-before-ack",
            ack_delivery=False,
        )
        with self.assertRaisesRegex(
            self.loopctl.StaleCompletionError, "STALE_COMPLETION"
        ):
            self.controller.consume_event(event)
        self.controller.record_delivery(
            dispatch["dispatch_id"],
            phase="DISPATCH",
            method="test-transport",
            result="acknowledged",
        )
        self.assertEqual("CONSUMED", self.controller.consume_event(event)["status"])

    def test_thinx_result_requires_review_acknowledgement(self):
        self.register_base()
        last_dispatch = None
        for index in range(3):
            last_dispatch = self.controller.prepare_dispatch(
                "task-a", "linx-task"
            )
            blocked = self.build_result_event(
                "task-a",
                last_dispatch["dispatch_id"],
                "worker-a",
                last_dispatch["packet_sha256"],
                [],
                f"evt-review-block-{index}",
                outcome="BLOCKED",
                blocker="bounded attempt failed",
            )
            self.controller.consume_event(blocked)
        self.controller.register_actor(
            "thinx-a", "THINX", "Thinx", "gpt-5.6-sol-xhigh"
        )
        decision = self.build_thinx_event(
            "task-a",
            last_dispatch["dispatch_id"],
            "thinx-a",
            last_dispatch["packet_sha256"],
            "evt-review-before-ack",
            ack_review=False,
        )
        with self.assertRaisesRegex(
            self.loopctl.StaleCompletionError, "STALE_COMPLETION"
        ):
            self.controller.consume_event(decision)
        self.controller.record_delivery(
            last_dispatch["dispatch_id"],
            phase="REVIEW",
            method="test-thinx",
            result="acknowledged",
        )
        self.assertEqual(
            "THINX_CONSUMED",
            self.controller.consume_event(decision)["status"],
        )

    def test_completed_task_cannot_dispatch_again(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event(
            "task-a",
            dispatch["dispatch_id"],
            "worker-a",
            dispatch["packet_sha256"],
            [],
            "evt-complete-once",
        )
        self.assertEqual("CONSUMED", self.controller.consume_event(event)["status"])
        with self.assertRaisesRegex(
            self.loopctl.TaskNotReadyError, "TASK_STATE_NOT_DISPATCHABLE"
        ):
            self.controller.prepare_dispatch("task-a", "linx-task")

    def test_worktree_identity_cannot_be_remapped(self):
        self.register_base()
        with self.assertRaisesRegex(
            self.loopctl.IdentityError, "WORKTREE_IMMUTABLE"
        ):
            self.controller.register_worktree(
                "wt-a", self.repo.parent / "different", "fixture"
            )

    def test_completion_rejects_dirty_claimed_path_after_c2(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event(
            "task-a",
            dispatch["dispatch_id"],
            "worker-a",
            dispatch["packet_sha256"],
            ["src/a.py"],
            "evt-dirty-after-c2",
        )
        (self.repo / "src" / "a.py").write_text("A = 99\n", encoding="utf-8")
        with self.assertRaisesRegex(
            self.loopctl.ScopeBreachError, "SCOPE_BREACH"
        ):
            self.controller.consume_event(event)

    def test_completion_rejects_commit_after_c2(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event(
            "task-a",
            dispatch["dispatch_id"],
            "worker-a",
            dispatch["packet_sha256"],
            ["src/a.py"],
            "evt-commit-after-c2",
        )
        (self.repo / "src" / "a.py").write_text("A = 101\n", encoding="utf-8")
        run("git", "add", "src/a.py", cwd=self.repo)
        run("git", "commit", "-m", "unexpected later commit", cwd=self.repo)
        with self.assertRaisesRegex(
            self.loopctl.StaleCompletionError, "RESULT_INVALID"
        ):
            self.controller.consume_event(event)

    def test_rebuild_rejects_missing_snapshot_table(self):
        self.register_base()
        snapshot = json.loads(
            self.controller.snapshot_path.read_text(encoding="utf-8")
        )
        del snapshot["tables"]["metrics"]
        self.controller.snapshot_path.write_text(
            json.dumps(snapshot), encoding="utf-8"
        )
        self.controller.db_path.write_bytes(b"not sqlite")
        with self.assertRaisesRegex(
            self.loopctl.SnapshotExportError, "SNAPSHOT_TABLE_UNKNOWN"
        ):
            self.controller.rebuild()

    def test_rebuild_failure_restores_db_wal_and_shm_as_one_set(self):
        self.register_base()
        paths = [
            self.controller.db_path,
            Path(str(self.controller.db_path) + "-wal"),
            Path(str(self.controller.db_path) + "-shm"),
        ]
        expected = {
            paths[0]: paths[0].read_bytes(),
            paths[1]: b"original wal",
            paths[2]: b"original shm",
        }
        paths[1].write_bytes(expected[paths[1]])
        paths[2].write_bytes(expected[paths[2]])
        original_replace = self.loopctl.os.replace

        def fail_install(source, target):
            source_path = Path(source)
            target_path = Path(target)
            if ".rebuild-" in source_path.name and target_path == paths[0]:
                raise OSError("install failed")
            return original_replace(source, target)

        self.loopctl.os.replace = fail_install
        try:
            with self.assertRaisesRegex(
                self.loopctl.SnapshotExportError, "REBUILD_REPLACE_FAILED"
            ):
                self.controller.rebuild()
        finally:
            self.loopctl.os.replace = original_replace
        for path, data in expected.items():
            self.assertEqual(data, path.read_bytes())
        self.assertFalse(list(self.controller.root.glob("*.rebuild-*")))
        self.assertEqual(
            1, len(list(self.controller.root.glob("loop.db.failed-*")))
        )

class AcceptanceProductionTests(LoopLiteCase):
    def test_owner_packet_required_verified_and_in_action(self):
        self.controller.register_actor("linx-task", "LINX", "Linx", "sol")
        self.controller.register_actor("worker-a", "WORKER", "Worker", "terra")
        self.controller.register_worktree("wt-a", self.repo, "fixture")
        with self.assertRaisesRegex(self.loopctl.IdentityError, "OWNER_PACKET_REQUIRED"):
            self._raw_register_task("raw-task", "worker-a", "wt-a", self.base_sha, [{"path": "src/a.py", "kind": "file"}], [], [], "done")
        self.controller.register_task("task-a", "worker-a", "wt-a", self.base_sha, [{"path": "src/a.py", "kind": "file"}], [], [], "done", self.owner_packet_path, self.owner_packet_sha256)
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        packet = json.loads(self.controller.action_path.read_text(encoding="utf-8"))["packet"]
        self.assertEqual(self.owner_packet_path.casefold(), packet["owner_packet_path"])
        self.assertEqual(self.owner_packet_sha256, packet["owner_packet_sha256"])
        self.assertEqual(self.owner_packet_sha256, Path(self.owner_packet_path).stem)
        attachment = next((self.repo / self.owner_packet_path).parent.joinpath("artifacts").glob("*.txt"))
        self.assertEqual(hashlib.sha256(attachment.read_bytes()).hexdigest(), attachment.stem)
        attachment.write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(self.loopctl.IdentityError, "OWNER_PACKET_INVALID"):
            self.controller.prepare_dispatch("task-a", "linx-task")
        self.assertTrue(dispatch["dispatch_id"])

    def test_tracked_owner_packet_is_rejected_before_dispatch(self):
        self.register_base()
        run("git", "add", ".devad/manager/owner-packets", cwd=self.repo)
        run("git", "commit", "-m", "incorrectly track owner packet", cwd=self.repo)
        with self.assertRaisesRegex(self.loopctl.IdentityError, "OWNER_PACKET_TRACKED"):
            self.controller.prepare_dispatch("task-a", "linx-task")

    def test_owner_packet_paths_must_be_content_addressed_and_durable(self):
        self.controller.register_actor("linx-task", "LINX", "Linx", "sol")
        self.controller.register_actor("worker-a", "WORKER", "Worker", "terra")
        self.controller.register_worktree("wt-a", self.repo, "fixture")
        legacy = self.repo / ".devad" / "manager" / "owner-packets" / "OWNER_PACKET.json"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_bytes((self.repo / self.owner_packet_path).read_bytes())
        (self.repo / self.owner_packet_path).unlink()
        self._raw_register_task(
            "legacy-owner", "worker-a", "wt-a", self.base_sha,
            [{"path": "src/a.py", "kind": "file"}], [], [], "done",
            legacy.relative_to(self.repo).as_posix(), self.owner_packet_sha256,
        )
        with self.assertRaisesRegex(self.loopctl.IdentityError, "OWNER_PACKET_INVALID"):
            self.controller.prepare_dispatch("legacy-owner", "linx-task")
    def test_event_scoped_receipt_and_local_work_packet(self):
        self.register_base()
        (self.repo / "src" / "a.py").write_text("A = 2\n", encoding="utf-8")
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        action = json.loads(self.controller.action_path.read_text(encoding="utf-8"))
        self.assertIn("src/a.py", action["packet"]["local_work"]["unstaged"])
        event = self.build_result_event("task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], ["src/a.py"], "evt-proof")
        self.assertIn("/receipts/evt-proof.json", event["result_path"])
        self.assertEqual("CONSUMED", self.controller.consume_event(event)["status"])
        old = dict(event)
        old["event_id"] = "evt-old"
        old["result_path"] = ".devad/workers/worker-a/RESULT.json"
        with self.assertRaisesRegex(self.loopctl.StaleCompletionError, "STALE_COMPLETION"):
            self.controller.consume_event(old)

    def test_unclaimed_local_work_and_three_failure_circuit(self):
        self.register_base()
        (self.repo / "src" / "b.py").write_text("B = 2\n", encoding="utf-8")
        with self.assertRaisesRegex(self.loopctl.ScopeBreachError, "LOCAL_WORK_SCOPE_BREACH"):
            self.controller.prepare_dispatch("task-a", "linx-task")
        (self.repo / "src" / "b.py").write_text("B = 1\n", encoding="utf-8")
        dispatch_ids = []
        for index in range(3):
            dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
            dispatch_ids.append(dispatch["dispatch_id"])
            event = self.build_result_event("task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"], [], f"evt-block-{index}", outcome="BLOCKED", blocker="waiting")
            result = self.controller.consume_event(event)
            self.assertEqual("RETRY_READY" if index < 2 else "THINX_REVIEW_REQUIRED", result["status"])
        self.assertEqual(3, len(set(dispatch_ids)))
        self.controller.register_actor("thinx-a", "THINX", "Thinx", "sol")
        connection = self.controller._connect()
        try:
            packet_sha = connection.execute("SELECT packet_sha256 FROM dispatches WHERE dispatch_id=?", (dispatch_ids[-1],)).fetchone()[0]
        finally:
            connection.close()
        thinx = self.build_thinx_event("task-a", dispatch_ids[-1], "thinx-a", packet_sha, "evt-reset")
        self.assertEqual("THINX_CONSUMED", self.controller.consume_event(thinx)["status"])
        connection = self.controller._connect()
        try:
            self.assertEqual("REGISTERED", connection.execute("SELECT status FROM tasks WHERE task_id='task-a'").fetchone()[0])
        finally:
            connection.close()

    def test_rebuild_install_rollback_preserves_db(self):
        self.register_base()
        before = self.controller.db_path.read_bytes()
        original = self.loopctl.os.replace
        calls = []
        def fail_install(source, target):
            calls.append((source, target))
            if len(calls) == 2:
                raise OSError("install failed")
            return original(source, target)
        self.loopctl.os.replace = fail_install
        try:
            with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "REBUILD_REPLACE_FAILED"):
                self.controller.rebuild()
        finally:
            self.loopctl.os.replace = original
        self.assertEqual(before, self.controller.db_path.read_bytes())
class IndependentReviewRegressionTests(LoopLiteCase):
    def test_rebuild_preserves_thinx_review_dispatch_and_identity(self):
        self.register_base()
        self.controller.register_actor("thinx-a", "THINX", "Thinx", "sol")
        last = None
        for index in range(3):
            last = self.controller.prepare_dispatch("task-a", "linx-task")
            event = self.build_result_event(
                "task-a", last["dispatch_id"], "worker-a", last["packet_sha256"],
                [], f"evt-review-{index}", outcome="BLOCKED", blocker="retry",
            )
            self.controller.consume_event(event)
        self.assertIsNotNone(last)
        self.controller.rebuild()
        self.controller.record_delivery(
            last["dispatch_id"], phase="REVIEW", method="test-thinx", result="acknowledged"
        )
        thinx = self.build_thinx_event(
            "task-a", last["dispatch_id"], "thinx-a", last["packet_sha256"],
            "evt-review-pass", ack_review=False,
        )
        self.assertEqual("THINX_CONSUMED", self.controller.consume_event(thinx)["status"])

    def test_rebuild_restores_completed_dependencies_and_rejects_id_reuse(self):
        self.register_base()
        self.controller._transition_task_state("task-a", "COMPLETE")
        self.controller.register_actor("worker-b", "WORKER", "Worker B", "terra")
        self.controller.register_task(
            "task-b", "worker-b", "wt-a", self.base_sha,
            [{"path": "src/b.py", "kind": "file"}], [], ["task-a"], "B done",
        )
        self.controller.rebuild()
        prepared = self.controller.prepare_dispatch("task-b", "linx-task")
        self.assertTrue(prepared["dispatch_id"].startswith("dsp-"))
        with self.assertRaisesRegex(self.loopctl.IdentityError, "TASK_ID_RETIRED"):
            self.controller.register_task(
                "task-a", "worker-b", "wt-a", self.base_sha,
                [{"path": "src/a.py", "kind": "file"}], [], [], "reused",
            )

    def test_reverted_out_of_scope_commit_is_still_a_scope_breach(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        (self.repo / "src" / "b.py").write_text("B = 2\n", encoding="utf-8")
        run("git", "add", "src/b.py", cwd=self.repo)
        run("git", "commit", "-m", "out of scope intermediate", cwd=self.repo)
        (self.repo / "src" / "b.py").write_text("B = 1\n", encoding="utf-8")
        run("git", "add", "src/b.py", cwd=self.repo)
        run("git", "commit", "-m", "revert out of scope intermediate", cwd=self.repo)
        self.assertIn("src/b.py", self.controller.reconcile("task-a")["git"]["committed"])
        event = self.build_result_event(
            "task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"],
            ["src/a.py"], "evt-history-scope",
        )
        with self.assertRaisesRegex(self.loopctl.ScopeBreachError, "src/b.py"):
            self.controller.consume_event(event)

    def test_modified_accepted_receipt_blocks_next_dispatch(self):
        self.register_base()
        dispatch = self.controller.prepare_dispatch("task-a", "linx-task")
        event = self.build_result_event(
            "task-a", dispatch["dispatch_id"], "worker-a", dispatch["packet_sha256"],
            [], "evt-receipt-tamper", outcome="BLOCKED", blocker="retry",
        )
        self.controller.consume_event(event)
        receipt = self.repo / event["result_path"]
        receipt.write_bytes(receipt.read_bytes() + b" ")
        with self.assertRaisesRegex(self.loopctl.StateNotDurableError, "RECEIPT_SET_MISMATCH"):
            self.controller.prepare_dispatch("task-a", "linx-task")

    def test_blocker_metric_is_removed_when_task_completes(self):
        self.register_base()
        first = self.controller.prepare_dispatch("task-a", "linx-task")
        blocked = self.build_result_event(
            "task-a", first["dispatch_id"], "worker-a", first["packet_sha256"],
            [], "evt-metric-block", outcome="BLOCKED", blocker="retry",
        )
        self.controller.consume_event(blocked)
        second = self.controller.prepare_dispatch("task-a", "linx-task")
        complete = self.build_result_event(
            "task-a", second["dispatch_id"], "worker-a", second["packet_sha256"],
            [], "evt-metric-complete",
        )
        self.controller.consume_event(complete)
        connection = self.controller._connect()
        try:
            metric = connection.execute(
                "SELECT value FROM metrics WHERE key=?", ("blocked:task-a",)
            ).fetchone()
        finally:
            connection.close()
        self.assertTrue(metric is None or metric["value"] == "0")
        self.assertLess(self.controller.snapshot_path.stat().st_size, 8192)

    def test_oversize_snapshot_rolls_back_before_database_commit(self):
        self.register_base()
        before = json.loads(self.controller.snapshot_path.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(self.loopctl.SnapshotExportError, "SNAPSHOT_TOO_LARGE"):
            self.controller.set_gate("task-a", "oversize", "PASS", "x" * 9000)
        connection = self.controller._connect()
        try:
            generation = self.controller._generation(connection)
            gate = connection.execute(
                "SELECT 1 FROM gates WHERE task_id=? AND name=?", ("task-a", "oversize")
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(before["generation"], generation)
        self.assertIsNone(gate)


if __name__ == "__main__":
    unittest.main()
