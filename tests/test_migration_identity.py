import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_migration():
    path = ROOT / "scripts" / "migrate_project.py"
    spec = importlib.util.spec_from_file_location("x9_migration", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class MigrationIdentityTests(unittest.TestCase):
    def test_explicit_lock_roles_extend_stale_workers_snapshot(self):
        migration = load_migration()
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            manager = repo / ".devad" / "manager"
            manager.mkdir(parents=True)
            (manager / "WORKERS.md").write_text(
                "| Role / lane | Task ID |\n"
                "| Worker lane | 11111111-1111-1111-1111-111111111111 |\n",
                encoding="utf-8",
            )
            (manager / "MANAGER_PASS_LOCK.md").write_text(
                "- Replacement Linx: 22222222-2222-2222-2222-222222222222\n"
                "- Locked THINX: 33333333-3333-3333-3333-333333333333\n",
                encoding="utf-8",
            )
            roles = migration.parse_current_roles(repo)
            self.assertEqual("WORKER", roles["11111111-1111-1111-1111-111111111111"]["role"])
            self.assertEqual("LINX", roles["22222222-2222-2222-2222-222222222222"]["role"])
            self.assertEqual("THINX", roles["33333333-3333-3333-3333-333333333333"]["role"])
            self.assertEqual("", roles["22222222-2222-2222-2222-222222222222"]["title"])
            self.assertEqual("Replacement Linx", roles["22222222-2222-2222-2222-222222222222"]["lane_label"])


if __name__ == "__main__":
    unittest.main()
