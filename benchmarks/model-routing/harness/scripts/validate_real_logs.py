from __future__ import annotations

import argparse
import importlib.util
import sqlite3
import sys
from pathlib import Path


def load_parser(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_usage_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--thread-id")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path.home() / ".codex" / "logs_2.sqlite",
    )
    args = parser.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    if args.thread_id:
        rows = con.execute(
            "select ts, thread_id, feedback_log_body from logs "
            "where target='codex_core::session::turn' and "
            "(thread_id=? or feedback_log_body like ?) order by ts",
            (args.thread_id, f"%{args.thread_id}%"),
        ).fetchall()
    else:
        rows = con.execute(
            "select ts, thread_id, feedback_log_body from logs "
            "where target='codex_core::session::turn' "
            "and feedback_log_body like '%total_usage_tokens=%' "
            "order by ts desc limit 8"
        ).fetchall()
        rows.reverse()

    module = load_parser(args.candidate.resolve())
    events = module.read_usage_events(rows)
    print(f"rows={len(rows)} parsed={len(events)}")
    for event in events:
        print(f"{event.model} {event.effort} delta={event.total_tokens}")
    return 0 if events else 1


if __name__ == "__main__":
    raise SystemExit(main())
