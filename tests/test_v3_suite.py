from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
import unittest
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


class X9SuiteTests(unittest.TestCase):
    def test_all_five_skills_exist(self) -> None:
        for name in SKILLS:
            skill = ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(skill.is_file(), name)
            text = skill.read_text(encoding="utf-8")
            self.assertIn(f"name: {name}", text)

    def test_package_has_required_sections(self) -> None:
        for relative in (
            "README.md",
            "SOURCE_MANIFEST.sha256",
            "templates/x9-project/.devad/ROUTER.md",
            "templates/x9-project/.devad/manager/CURRENT.md",
            "templates/x9-project/.devad/manager/MODEL_STATE.md",
            "templates/x9-project/.devad/manager/WORKTREE_REGISTRY.md",
            "templates/x9-project/.devad/manager/MANAGER_PASS_LOCK.md",
            "templates/x9-project/.devad/manager/LINX_HANDOVER_STATE.md",
            "templates/x9-project/.devad/manager/workers/_template/ROUTER.md",
            "templates/x9-project/.devad/manager/workers/_template/STATUS.md",
            "templates/x9-project/.devad/manager/workers/_template/HANDOFFS.md",
            "templates/x9-project/.devad/features/_template/TASK.md",
            "templates/x9-project/.devad/features/_template/MANIFEST.md",
            "benchmarks/model-routing/README.md",
            "benchmarks/model-routing/templates/TASK_CASE.json",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_router_and_task_are_read_first_contracts(self) -> None:
        router = (ROOT / "templates/x9-project/.devad/ROUTER.md").read_text(encoding="utf-8")
        task = (ROOT / "templates/x9-project/.devad/features/_template/TASK.md").read_text(encoding="utf-8")
        self.assertIn("Read this file first", router)
        self.assertIn("read only the smallest linked file needed", router.lower())
        self.assertIn("Read this file first", task)

    def test_active_worker_files_are_compact(self) -> None:
        for name in ("STATUS.md", "HANDOFFS.md"):
            path = ROOT / "templates/x9-project/.devad/manager/workers/_template" / name
            text = path.read_text(encoding="utf-8")
            self.assertLessEqual(len(text.splitlines()), 120, name)
            self.assertLessEqual(len(text.encode("utf-8")), 12_000, name)
            self.assertIn("CURRENT_STATUS", text)

    def test_role_ownership_is_explicit(self) -> None:
        ownership = (ROOT / "docs/ROLE_OWNERSHIP.md").read_text(encoding="utf-8")
        for role in ("Thinx", "Linx", "Worker", "devad-memory", "codex-token-budget"):
            self.assertIn(role, ownership)

    def test_benchmark_json_is_valid(self) -> None:
        task = json.loads((ROOT / "benchmarks/model-routing/templates/TASK_CASE.json").read_text(encoding="utf-8"))
        deterministic = json.loads((ROOT / "benchmarks/loop-v5/DETERMINISTIC_RESULTS.json").read_text(encoding="utf-8"))
        self.assertEqual(task["quality_floor"], 90)
        self.assertEqual(task["candidates"], [])
        self.assertEqual(deterministic["model_cost_claim"], "NONE_DETERMINISTIC_ONLY")

    def test_manager_contains_conservative_routing(self) -> None:
        policy = (
            ROOT / "skills/devad-x9-loop/references/model-policy-v3.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Binding Profiles", policy)
        self.assertIn("gpt-5.6 high", policy)
        self.assertIn("gpt-5.6 xhigh", policy)
        self.assertIn("JUDGMENT_REQUIRED", policy)
        self.assertIn("at least five real samples", policy)

    def test_model_router_returns_from_ultra(self) -> None:
        path = ROOT / "scripts/model_router.py"
        spec = importlib.util.spec_from_file_location("x9_model_router", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        state = module.ModelState()
        self.assertEqual(state.linx_profile().label, "gpt-5.6 high")
        self.assertEqual(state.thinx_profile().label, "gpt-5.6 xhigh")
        escalated = state.begin_thinx_pass(high_risk=True, proof_failed=False)
        self.assertEqual(escalated.label, "gpt-5.6 ultra")
        self.assertEqual(state.complete_thinx_pass().label, "gpt-5.6 xhigh")
        self.assertFalse(state.escalated)

    def test_linx_cannot_lower_or_take_over(self) -> None:
        policy = (
            ROOT / "skills/devad-x9-loop/references/model-policy-v3.md"
        ).read_text(encoding="utf-8")
        self.assertIn("gpt-5.6 high", policy)
        self.assertIn("owner explicitly asks extra high", policy)
        self.assertIn("LOWER_MODEL_OK", policy)
        self.assertIn("Linx never takes over a stalled Worker", policy)

        manager = (ROOT / "skills/devad-x9-loop/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("runtime/ACTION.json", manager)
        self.assertIn("Linx never reviews code", manager)

    def test_manager_pass_mutex_and_handover_gates_exist(self) -> None:
        contract = (
            ROOT / "skills/devad-x9/references/x9-shared-contract.md"
        ).read_text(encoding="utf-8")
        heartbeat = (
            ROOT / "skills/devad-x9-loop/references/heartbeat-policy.md"
        ).read_text(encoding="utf-8")
        handover = (
            ROOT / "skills/devad-x9-loop/references/manager-handover-policy.md"
        ).read_text(encoding="utf-8")
        router = (
            ROOT / "templates/x9-project/.devad/ROUTER.md"
        ).read_text(encoding="utf-8")
        for text in (contract, router):
            self.assertIn("loop-lite", text.lower())
        self.assertIn("ACTION.json", router)
        self.assertIn("newer owner message", heartbeat)
        self.assertIn("incorrect owner-facing truth", handover)
        self.assertIn("HANDOVER_REQUIRED", handover)

    def test_collaborative_linx_handover_is_gated(self) -> None:
        reference = (
            ROOT
            / "skills/devad-x9-loop/references/collaborative-linx-handover.md"
        ).read_text(encoding="utf-8")
        state = (
            ROOT
            / "templates/x9-project/.devad/manager/LINX_HANDOVER_STATE.md"
        ).read_text(encoding="utf-8")
        heartbeat = (
            ROOT / "skills/devad-x9-loop/references/heartbeat-policy.md"
        ).read_text(encoding="utf-8")

        for required in (
            "HANDOVER_INVENTORY_REQUEST",
            "OWNER_SCOPE_MATRIX",
            "NEW_LINX_PLAN",
            "OLD_LINX_FINAL_REVIEW",
            "LINX_ACTIVATION_OK",
            "STATUS_ONLY",
            "one execution authority",
        ):
            self.assertIn(required, reference)
            self.assertIn(required, state)

        self.assertIn("EVENT_READY", reference)
        self.assertIn("Recurring 15/19-minute pickup is forbidden", reference)
        self.assertIn("LINX_ACTIVATION_OK", heartbeat)
        self.assertIn("SKIP_ACTIVE_MANAGER_PASS", heartbeat)

    def test_linx_handover_activation_validator(self) -> None:
        path = ROOT / "skills/devad-x9-loop/scripts/validate_linx_handover.py"
        spec = importlib.util.spec_from_file_location("x9_linx_handover", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        digest_a = "a" * 64
        digest_b = "b" * 64
        thread_id = "019f5b09-ec4f-7a43-a417-e2a01c4ea398"
        valid = f"""# Linx Handover State
**Status:** ACTIVATED
**Old Linx thread:** old
**New Linx thread:** {thread_id}
**Execution authority:** NEW_LINX
**One execution authority:** PASS
## HANDOVER_INVENTORY_REQUEST
**Mode:** STATUS_ONLY
**Coverage:** PASS
## OWNER_SCOPE_MATRIX
| Requirement | Owner state |
| x | IMPLEMENT |
## NEW_LINX_PLAN
**Path:** D:\\plan.md
**SHA-256:** {digest_b}
## OLD_LINX_FINAL_REVIEW
**Result:** PASS
## LINX_ACTIVATION_OK
**Token:** LINX_ACTIVATION_OK:{thread_id}:{digest_a}:{digest_b}
**Handover SHA-256:** {digest_a}
**Plan SHA-256:** {digest_b}
**Old Linx retired:** YES
## Continuation
**Callback target:** {thread_id}
**Mode:** DIRECT_EVENT_CALLBACK
**Recurring pickup:** FORBIDDEN
**Pass lock:** SKIP_ACTIVE_MANAGER_PASS
"""
        invalid = valid.replace("**Coverage:** PASS", "**Coverage:** PARTIAL")
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state.md"
            state.write_text(valid, encoding="utf-8")
            self.assertEqual(module.validate(state), [])
            state.write_text(invalid, encoding="utf-8")
            self.assertIn("inventory coverage is not PASS", module.validate(state))

    def test_worktree_discipline_is_explicit(self) -> None:
        contract = (
            ROOT / "skills/devad-x9/references/x9-shared-contract.md"
        ).read_text(encoding="utf-8")
        registry = (
            ROOT / "templates/x9-project/.devad/manager/WORKTREE_REGISTRY.md"
        ).read_text(encoding="utf-8")
        for required in (
            "Worktree Discipline",
            "Codex never removes, cleans, resets, stashes, or relocates a worktree",
            "SCOPE_BREACH",
            "CLAIM_EXPANSION_REQUEST",
            "worktree",
        ):
            self.assertIn(required, contract)
        self.assertIn("One active implementation worktree per feature ID", registry)

    def test_worker_sidecar_context_bridge_exists(self) -> None:
        bridge = (
            ROOT
            / "skills/devad-x9-loop/references/worker-sidecar-context-bridge.md"
        ).read_text(encoding="utf-8")
        for required in (
            "gpt-5.6-luna",
            "opencode-go/glm-5.2",
            "opencode-go/kimi-k2.7-code",
            "PLAN_CHALLENGE",
            "BLOCKER_CHALLENGE",
            "full durable task context",
            "Never send raw chat",
        ):
            self.assertIn(required, bridge)

        run_root = (
            ROOT
            / "templates/x9-project/.devad/manager/workers/_template/runs/_template"
        )
        self.assertTrue((run_root / "SIDE_INPUT.md").is_file())
        self.assertTrue((run_root / "SIDE_REVIEWS.md").is_file())

    def test_owner_context_and_attachment_gate_exists(self) -> None:
        reference = (
            ROOT
            / "skills/devad-x9-loop/references/owner-context-and-attachments.md"
        ).read_text(encoding="utf-8")
        for required in (
            "exact owner message",
            "OWNER_CONTEXT_RECEIPT: PASS",
            "MISSING_ATTACHMENT",
            "BINARY_VIEWED",
            "summary alone is not context transfer",
            "low-thinking",
        ):
            self.assertIn(required, reference)

        base = ROOT / "templates/x9-project/.devad/manager/owner-input"
        for relative in (
            "INDEX.md",
            "_template/OWNER_REQUEST.md",
            "_template/ATTACHMENTS.json",
            "_template/VISUAL_CONTEXT.md",
            "_template/CONTEXT_RECEIPT.md",
        ):
            self.assertTrue((base / relative).is_file(), relative)
        self.assertTrue(
            (
                ROOT
                / "skills/devad-x9-loop/scripts/validate_owner_context.py"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()
