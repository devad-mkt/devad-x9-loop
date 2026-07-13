from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_owner_context.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("owner_context_validator", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("validator cannot load")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OwnerContextTests(unittest.TestCase):
    def test_required_attachment_and_receipt_pass(self) -> None:
        module = load_validator()
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp)
            request = bundle / "OWNER_REQUEST.md"
            request.write_text("Exact request", encoding="utf-8")
            image = bundle / "screen.png"
            image.write_bytes(b"safe-image-fixture")
            image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
            request_hash = hashlib.sha256(request.read_bytes()).hexdigest()
            (bundle / "ATTACHMENTS.json").write_text(
                json.dumps(
                    {
                        "input_id": "owner-1",
                        "attachments": [
                            {
                                "id": "screen-1",
                                "stable_path": "screen.png",
                                "sha256": image_hash,
                                "required": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            receipt = bundle / "receipt.md"
            receipt.write_text(
                "OWNER_CONTEXT_RECEIPT: PASS\n"
                f"OWNER_REQUEST_SHA256: {request_hash}\n"
                f"| screen-1 | {image_hash} | BINARY_VIEWED | PASS |\n",
                encoding="utf-8",
            )
            self.assertEqual(module.validate_bundle(bundle, receipt), [])

    def test_missing_attachment_is_blocked(self) -> None:
        module = load_validator()
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp)
            request = bundle / "OWNER_REQUEST.md"
            request.write_text("Exact request", encoding="utf-8")
            (bundle / "ATTACHMENTS.json").write_text(
                json.dumps(
                    {
                        "input_id": "owner-2",
                        "attachments": [
                            {
                                "id": "missing",
                                "stable_path": "missing.png",
                                "sha256": "0" * 64,
                                "required": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            receipt = bundle / "receipt.md"
            receipt.write_text("OWNER_CONTEXT_RECEIPT: PASS\n", encoding="utf-8")
            errors = module.validate_bundle(bundle, receipt)
            self.assertTrue(any("MISSING_ATTACHMENT:missing" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
