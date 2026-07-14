from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "skills" / "devad-x9" / "references" / "x9-shared-contract.md"


class SharedContractV6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CONTRACT.read_text(encoding="utf-8-sig")

    def test_all_safety_sections_remain(self):
        for heading in (
            "## Authority",
            "## Truth Lock",
            "## Local Work",
            "## Worktree Discipline",
            "## Exact Scope",
            "## Destructive Actions",
            "## Security Before Commit",
            "## Commit And Attestation",
            "## Push And Deploy",
            "## Durable `.devad` Truth",
            "## Proof And Claims",
            "## Owner Input Contract",
        ):
            self.assertIn(heading, self.text)

    def test_controller_replaces_markdown_mutex_and_manual_manager_state(self):
        lowered = self.text.lower()
        self.assertIn("loop-lite/snapshot.json", lowered)
        self.assertIn("controller", lowered)
        self.assertIn("historical evidence", lowered)
        self.assertIn("generated human views", lowered)
        self.assertNotIn("every direct manager pass and heartbeat uses", lowered)
        self.assertNotIn("linx maintains it from `git worktree", lowered)

    def test_status_handoffs_and_old_loop_are_not_current_authority(self):
        self.assertIn("STATUS.md and HANDOFFS.md are generated", self.text)
        self.assertIn("never parser authority", self.text)
        self.assertIn(".devad/manager/loop/", self.text)
        self.assertIn("historical", self.text.lower())

    def test_scope_contract_names_all_git_surfaces(self):
        lowered = self.text.lower()
        for word in ("staged", "unstaged", "untracked", "committed"):
            self.assertIn(word, lowered)
        self.assertIn("SCOPE_BREACH", self.text)
        self.assertIn("CLAIM_EXPANSION_REQUEST", self.text)


if __name__ == "__main__":
    unittest.main()
