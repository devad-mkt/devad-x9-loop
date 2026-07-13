import hashlib
import importlib.util
import json
import tempfile
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def load_loop_contract():
    path = SKILLS / "devad-x9-loop" / "scripts" / "loop_contract.py"
    spec = importlib.util.spec_from_file_location("loop_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackageContractTests(unittest.TestCase):
    def test_required_skills_exist(self):
        expected = {
            "devad-x9",
            "devad-x9-loop",
            "devad-x9-manager",
            "codex-x9-backup",
            "codex-token-budget",
            "devad-memory",
        }
        actual = {p.name for p in SKILLS.iterdir() if p.is_dir()}
        self.assertEqual(expected, actual)
        for name in expected:
            self.assertTrue((SKILLS / name / "SKILL.md").is_file())

    def test_manager_is_a_small_redirect(self):
        text = (SKILLS / "devad-x9-manager" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("devad-x9-loop", text)
        self.assertLessEqual(len(text.splitlines()), 40)

    def test_readme_has_required_details(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for heading in (
            "Existing X9 Worker features",
            "Existing X9 Manager features",
            "New Loop v5 features",
            "Safety and deployment gates",
            "Supporting skills",
            "Retired and rejected mechanisms",
            "Migration and rollback",
        ):
            self.assertIn(heading, text)
        self.assertGreaterEqual(text.count("<details>"), 7)

    def test_feature_registry_is_complete(self):
        registry = json.loads((ROOT / "features.registry.json").read_text(encoding="utf-8"))
        allowed = {"RETAINED", "MOVED", "ADAPTED", "NEW", "RETIRED"}
        self.assertGreaterEqual(len(registry["features"]), 25)
        for feature in registry["features"]:
            for key in ("id", "owner", "source", "status", "purpose", "required_test"):
                self.assertTrue(feature.get(key), f"{feature.get('id')} missing {key}")
            self.assertIn(feature["status"], allowed)
            if feature["status"] in {"MOVED", "ADAPTED", "RETIRED"}:
                self.assertTrue(feature.get("replacement"))
                self.assertTrue(feature.get("reason"))

    def test_project_template_has_loop_state(self):
        loop = ROOT / "templates" / "x9-project" / ".devad" / "manager" / "loop"
        expected = {
            "ROLE_REGISTRY.json",
            "PASS_CAPSULE.json",
            "WORKTREE_INDEX.json",
            "TASK_GRAPH.json",
            "RESOURCE_CLAIMS.json",
            "EVENT_CURSOR.json",
            "DISPATCH_LEDGER.jsonl",
            "DECISION_GATES.json",
        }
        self.assertEqual(expected, {p.name for p in loop.iterdir() if p.is_file()})
        capsule = (loop / "PASS_CAPSULE.json").read_bytes()
        self.assertLess(len(capsule), 8192)


class IdentityAndDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = load_loop_contract()

    def test_title_role_mismatch_is_detected(self):
        registry = {
            "tasks": {
                "task-worker-1": {
                    "role": "WORKER",
                    "title": "Linx - paused",
                    "immutable": True,
                }
            }
        }
        errors = self.loop.validate_role_registry(registry)
        self.assertIn(
            "TITLE_ROLE_MISMATCH:task-worker-1:WORKER:Linx - paused", errors
        )

    def test_role_words_do_not_match_inside_other_words(self):
        registry = {
            "tasks": {
                "task-worker-2": {
                    "role": "WORKER",
                    "title": "Sidebar clone Worker",
                    "immutable": True,
                }
            }
        }
        self.assertEqual([], self.loop.validate_role_registry(registry))

    def test_dispatch_dedup_and_honest_attempts(self):
        packet = b"exact packet"
        packet_hash = hashlib.sha256(packet).hexdigest()
        ledger = []
        dispatch = self.loop.create_dispatch(
            ledger, "task-linx", "task-worker", "WORKER", packet_hash
        )
        self.loop.record_attempt(ledger, dispatch, "thread", "accepted")
        report = self.loop.delivery_report(ledger, dispatch)
        self.assertEqual("DELIVERY_UNCONFIRMED", report["status"])
        self.assertEqual(1, report["attempts"])
        self.assertFalse(report["sent_once"])
        self.loop.acknowledge(ledger, dispatch, "task-worker", packet_hash, "receipt.md", "abc")
        report = self.loop.delivery_report(ledger, dispatch)
        self.assertEqual("ACKNOWLEDGED", report["status"])
        self.assertTrue(report["sent_once"])
        self.assertEqual("SKIP_ALREADY_DELIVERED", self.loop.retry_decision(ledger, dispatch))

    def test_changed_packet_gets_new_dispatch(self):
        ledger = []
        first = self.loop.create_dispatch(ledger, "linx", "worker", "WORKER", "a" * 64)
        second = self.loop.create_dispatch(
            ledger, "linx", "worker", "WORKER", "b" * 64, supersedes=first
        )
        self.assertNotEqual(first, second)
        self.assertEqual(first, ledger[-1]["supersedes"])

    def test_completion_rejects_wrong_identity(self):
        expected = {
            "task_id": "task-1",
            "dispatch_id": "dsp-1",
            "role": "WORKER",
            "packet_sha256": "a" * 64,
        }
        receipt = dict(expected)
        receipt["task_id"] = "old-task"
        self.assertEqual(
            "STALE_COMPLETION:task_id",
            self.loop.validate_completion(expected, receipt),
        )

    def test_scheduler_respects_limits_and_claims(self):
        tasks = [
            {"id": "a", "status": "READY", "pool": "CODING", "dependencies": []},
            {"id": "b", "status": "READY", "pool": "CODING", "dependencies": []},
            {"id": "c", "status": "READY", "pool": "CODING", "dependencies": []},
        ]
        claims = {
            "a": ["file:src/a.py"],
            "b": ["file:src/b.py"],
            "c": ["file:src/c.py"],
        }
        self.assertEqual(["a", "b"], self.loop.select_ready_tasks(tasks, claims)["CODING"])
        claims["b"] = ["file:src/a.py"]
        selected = self.loop.select_ready_tasks(tasks, claims)["CODING"]
        self.assertNotIn("b", selected)

    def test_promotion_gate_requires_all_evidence(self):
        good = {
            "calendar_days": 3,
            "dispatches": 10,
            "lost_work": 0,
            "identity_errors": 0,
            "resource_conflicts": 0,
            "critical_errors": 0,
            "orchestration_retries": 1,
        }
        self.assertTrue(self.loop.can_promote_coding_pool(good))
        bad = dict(good, calendar_days=2)
        self.assertFalse(self.loop.can_promote_coding_pool(bad))


class CallbackPickupPolicyTests(unittest.TestCase):
    def test_callback_is_primary_and_recurring_pickup_is_forbidden(self):
        skill = (SKILLS / "devad-x9-loop" / "SKILL.md").read_text(encoding="utf-8")
        heartbeat = (
            SKILLS / "devad-x9-loop" / "references" / "heartbeat-policy.md"
        ).read_text(encoding="utf-8")
        pickup = (
            SKILLS / "devad-x9-loop" / "references" / "handoff-pickup-policy.md"
        ).read_text(encoding="utf-8")
        for text in (skill, heartbeat, pickup):
            self.assertIn("EVENT_READY", text)
            self.assertIn("same registered Linx task", text)
            self.assertIn("Recurring 15/19-minute pickup is forbidden", text)
        self.assertIn("PAUSE_NOT_DELETE", heartbeat)

    def test_callback_contract_has_identity_receipt_and_bounded_delivery(self):
        callback = (
            SKILLS / "devad-x9-loop" / "references" / "direct-event-callback.md"
        ).read_text(encoding="utf-8")
        for field in (
            "LINX_TASK_ID",
            "SOURCE_TASK_ID",
            "SOURCE_ROLE",
            "DISPATCH_ID",
            "PACKET_SHA256",
            "EVENT_TYPE",
            "RECEIPT_PATH",
            "RECEIPT_SHA256",
        ):
            self.assertIn(field, callback)
        self.assertIn("at most three", callback.lower())
        self.assertIn("MANAGER_WAKE_FAILED", callback)
        self.assertIn("release", callback.lower())
        self.assertIn("MANAGER_PASS_LOCK", callback)

    def test_active_recurring_heartbeat_is_reported_and_template_uses_callback(self):
        checker = (
            SKILLS / "devad-x9-loop" / "scripts" / "check_x9_manager_state.py"
        ).read_text(encoding="utf-8")
        state = (
            ROOT / "templates/x9-project/.devad/manager/LINX_HANDOVER_STATE.md"
        ).read_text(encoding="utf-8")
        self.assertIn("recurring heartbeat active", checker)
        self.assertIn("DIRECT_EVENT_CALLBACK", state)
        self.assertIn("**Recurring pickup:** FORBIDDEN", state)
        self.assertNotIn("**Cadence:** 19 minutes", state)

    def test_linx_executes_known_safe_next_action_instead_of_reporting_it(self):
        skill = (SKILLS / "devad-x9-loop" / "SKILL.md").read_text(encoding="utf-8")
        algorithm = (
            SKILLS / "devad-x9-loop" / "references" / "manager-pass-algorithm.md"
        ).read_text(encoding="utf-8")
        for text in (skill, algorithm):
            self.assertIn("NEXT_ONLY_FORBIDDEN", text)
            self.assertIn("Preparation and validation do not consume", text)
            self.assertIn("no owner decision", text)


class MigrationSafetyTests(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        script = ROOT / "scripts" / "migrate_project.py"
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".devad").mkdir()
            marker = repo / ".devad" / "EXISTING.md"
            marker.write_text("keep", encoding="utf-8")
            before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
            import subprocess

            run = subprocess.run(
                [sys.executable, str(script), "--repo", str(repo)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, run.returncode, run.stderr)
            after = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertIn("DRY_RUN", run.stdout)


if __name__ == "__main__":
    unittest.main()
