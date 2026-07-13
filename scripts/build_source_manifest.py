from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "SOURCE_MANIFEST.sha256"
EXCLUDE = {"SOURCE_MANIFEST.sha256"}


def main() -> int:
    lines: list[str] = []
    for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        if relative in EXCLUDE or ".git" in path.parts or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {relative}")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT} with {len(lines)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
