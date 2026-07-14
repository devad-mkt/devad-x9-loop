from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate_project.py"


def files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def link_directory(link: Path, target: Path) -> None:
    if os.name == "nt":
        result = subprocess.run(
            f'mklink /J "{link}" "{target}"',
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            shell=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return
    link.symlink_to(target, target_is_directory=True)


class LoopLiteMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        old_loop = self.repo / ".devad" / "manager" / "loop"
        old_loop.mkdir(parents=True)
        (self.repo / ".devad" / "OLD.md").write_text("preserve exact\n", encoding="utf-8")
        (old_loop / "PASS_CAPSULE.json").write_text('{"old":true}\n', encoding="utf-8")
        (self.repo / ".devad" / "manager" / "MANAGER_PASS_LOCK.md").write_text(
            "historical lock\n", encoding="utf-8"
        )

    def invoke(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), *extra],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def test_dry_run_writes_nothing_and_names_loop_lite(self):
        before = files(self.repo)
        result = self.invoke()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, files(self.repo))
        self.assertIn("DRY_RUN", result.stdout)
        self.assertIn("manager\\loop-lite", result.stdout)
        self.assertNotIn("manager\\loop\\PASS_CAPSULE.json", result.stdout)

    def test_apply_creates_overlay_and_preserves_all_old_bytes(self):
        before = files(self.repo)
        result = self.invoke("--apply")
        self.assertEqual(0, result.returncode, result.stderr)
        after = files(self.repo)
        for relative, content in before.items():
            self.assertEqual(content, after[relative], relative)

        loop_lite = self.repo / ".devad" / "manager" / "loop-lite"
        self.assertTrue((loop_lite / "SNAPSHOT.json").is_file())
        self.assertTrue((loop_lite / ".gitignore").is_file())
        self.assertTrue((loop_lite / "contracts" / "TASK.json").is_file())
        owner_packets = self.repo / ".devad" / "manager" / "owner-packets"
        self.assertTrue((owner_packets / ".gitignore").is_file())
        self.assertTrue((owner_packets / "README.md").is_file())
        self.assertFalse((loop_lite / "loop.db").exists())
        self.assertFalse((loop_lite / "runtime" / "ACTION.json").exists())
        self.assertIn("ACTIVATION_NOT_SENT", result.stdout)

    def test_existing_loop_lite_file_is_preserved_not_overwritten(self):
        target = self.repo / ".devad" / "manager" / "loop-lite" / "SNAPSHOT.json"
        target.parent.mkdir(parents=True)
        target.write_text('{"keep":"me"}\n', encoding="utf-8")
        before = target.read_bytes()
        result = self.invoke("--apply")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, target.read_bytes())
        self.assertIn("PRESERVE_EXISTING", result.stdout)

    def test_apply_rejects_linked_parent_and_does_not_write_outside_repo(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        linked_parent = self.repo / ".devad" / "manager" / "loop-lite"
        link_directory(linked_parent, outside)

        result = self.invoke("--apply")

        self.assertNotEqual(0, result.returncode)
        self.assertIn("unsafe migration path", result.stderr)
        self.assertEqual({}, files(outside))
        self.assertFalse((self.repo / ".devad" / "ROUTER.md").exists())

    def test_activation_packet_reuses_thinx_and_does_not_message_old_linx(self):
        result = self.invoke("--apply")
        self.assertEqual(0, result.returncode, result.stderr)
        packet = self.repo / ".devad" / "manager" / "passes" / "2026-07-13-x9-loop-lite-v6-activation.md"
        text = packet.read_text(encoding="utf-8")
        self.assertIn("fresh Linx v6", text)
        self.assertIn("reuse the existing Thinx", text)
        self.assertIn("do not message the current linx", text.lower())
        self.assertIn("shadow reconciliation", text.lower())


if __name__ == "__main__":
    unittest.main()
