from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SKILLS = {
    "devad-x9",
    "devad-x9-loop",
    "devad-x9-manager",
    "codex-x9-backup",
    "codex-token-budget",
    "devad-memory",
}
PRIVATE_MARKERS = (
    "A-" + "haj",
    r"D:" + r"\CDX-3",
    "devadio/" + "codex-x9-backup",
    "env-" + "extra",
)


class PublicPackageTests(unittest.TestCase):
    def test_public_package_has_six_skills(self) -> None:
        actual = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(actual, REQUIRED_SKILLS)

    def test_public_manifest_marks_distribution(self) -> None:
        manifest = json.loads((ROOT / "kit.manifest.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(manifest["distribution"], "public")
        self.assertNotIn("baseline_main_sha", manifest)

    def test_private_evidence_is_not_distributed(self) -> None:
        self.assertFalse((ROOT / "archives").exists())
        self.assertFalse((ROOT / "docs" / "commits").exists())
        self.assertFalse((ROOT / "docs" / "security").exists())
        self.assertFalse((ROOT / "benchmarks" / "model-routing" / "results").exists())

    def test_no_personal_paths_or_private_backup_remote(self) -> None:
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.suffix in {".pyc", ".zip"}:
                continue
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            for marker in PRIVATE_MARKERS:
                self.assertNotIn(marker, text, f"private marker in {path.relative_to(ROOT)}")

    def test_readme_defines_bounded_linx_wake(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8-sig")
        for phrase in (
            "Files do not wake Linx",
            "same Linx task ID",
            "DONT_NOTIFY",
            "stop or delete the monitor",
            "no infinite polling",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
