import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RegistryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.legacy = json.loads((ROOT / "legacy.inventory.json").read_text(encoding="utf-8-sig"))
        self.registry = json.loads((ROOT / "features.registry.json").read_text(encoding="utf-8-sig"))

    def test_every_legacy_item_is_classified_once(self):
        old_ids = [item["id"] for item in self.legacy["items"]]
        features = self.registry["features"]
        covered = [feature.get("legacy_id") for feature in features if feature.get("legacy_id")]
        self.assertEqual(len(covered), len(set(covered)), "duplicate legacy classification")
        self.assertEqual(set(old_ids), set(covered))

    def test_classifications_are_complete(self):
        allowed = {"RETAINED", "MOVED", "ADAPTED", "NEW", "RETIRED"}
        for feature in self.registry["features"]:
            for field in ("id", "owner", "source", "status", "purpose", "required_test"):
                self.assertTrue(feature.get(field), f"{feature.get('id')} missing {field}")
            self.assertIn(feature["status"], allowed)
            if feature["status"] in {"MOVED", "ADAPTED", "RETIRED"}:
                self.assertTrue(feature.get("replacement"))
                self.assertTrue(feature.get("reason"))

    def test_scripts_templates_headings_and_invariants_were_scanned(self):
        kinds = {item["kind"] for item in self.legacy["items"]}
        self.assertTrue({"script", "template", "heading", "invariant"}.issubset(kinds))


if __name__ == "__main__":
    unittest.main()
