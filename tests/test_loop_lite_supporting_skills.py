from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class SupportingSkillV6Tests(unittest.TestCase):
    def read(self, skill: str, relative: str = "SKILL.md") -> str:
        return (SKILLS / skill / relative).read_text(encoding="utf-8-sig")

    def test_x9_worker_uses_loop_lite_and_terra_policy(self):
        text = self.read("devad-x9")
        self.assertIn("Devad X9 v6", text)
        self.assertIn("loop-lite/SNAPSHOT.json", text)
        self.assertIn("Terra high", text)
        self.assertIn("staged, unstaged, untracked, and committed", text)
        self.assertIn("SCOPE_BREACH", text)
        self.assertIn("C1", text)
        self.assertIn("C2", text)
        self.assertIn("security", text.lower())

    def test_manager_shim_redirects_to_v6_without_second_flow(self):
        text = self.read("devad-x9-manager")
        self.assertIn("v6", text)
        self.assertIn("devad-x9-loop", text)
        self.assertIn("loop-lite", text)
        self.assertIn("Do not run a second manager flow", text)

    def test_memory_names_loop_lite_as_active_and_v5_as_history(self):
        text = self.read("devad-memory")
        self.assertIn(".devad/manager/loop-lite/SNAPSHOT.json", text)
        self.assertIn(".devad/manager/loop/", text)
        self.assertIn("historical", text.lower())

    def test_token_budget_uses_event_metrics_without_fallback_lifetime_totals(self):
        text = self.read("codex-token-budget")
        self.assertIn("X9 Loop Lite v6 Audit", text)
        self.assertIn("SNAPSHOT.json", text)
        self.assertIn("ACTION.json", text)
        self.assertIn("wall time", text.lower())
        self.assertIn("prompt bytes", text.lower())
        self.assertIn("first-pass success", text.lower())
        self.assertIn("fallback lifetime totals are forbidden", text.lower())
        self.assertIn("Unknown", text)
        self.assertNotIn("top thread lifetime/fallback totals", text.lower())

    def test_backup_and_installer_still_cover_all_six_skills(self):
        backup = self.read("codex-x9-backup")
        installer = (ROOT / "scripts" / "install-suite.ps1").read_text(
            encoding="utf-8-sig"
        )
        for name in (
            "devad-x9",
            "devad-x9-loop",
            "devad-x9-manager",
            "codex-x9-backup",
            "codex-token-budget",
            "devad-memory",
        ):
            self.assertIn(name, backup + installer)
        self.assertIn("rollback", installer.lower())

    def test_agent_prompt_uses_loop_lite_action(self):
        text = self.read("devad-x9-loop", "agents/openai.yaml")
        self.assertIn("loop-lite", text)
        self.assertIn("ACTION.json", text)
        self.assertIn("one", text.lower())


    def test_backup_mirrors_reject_reparse_roots(self):
        for relative in (
            "scripts/restore-codex-x9-backup.ps1",
            "scripts/sync-codex-x9-backup.ps1",
        ):
            text = self.read("codex-x9-backup", relative)
            self.assertIn("Assert-NoReparsePath", text)
            self.assertIn("ReparsePoint", text)
            self.assertLess(text.index("Assert-NoReparsePath"), text.index("& robocopy"))

    def test_project_template_is_staged_before_atomic_install(self):
        installer = (ROOT / "scripts" / "install-suite.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("$ProjectStage", installer)
        self.assertIn("Move-Item -LiteralPath $ProjectStage -Destination $DevadTarget", installer)
        self.assertNotIn("Copy-Item -LiteralPath $Template -Destination $ProjectRoot", installer)


if __name__ == "__main__":
    unittest.main()
