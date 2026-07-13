from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path


def field(body: str, name: str) -> str:
    match = re.search(
        rf"\b{re.escape(name)}\s*[=:]\s*(\"[^\"]*\"|[A-Za-z0-9_.:-]+)",
        body,
        re.IGNORECASE,
    )
    return match.group(1).strip('"') if match else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("thread_ids", nargs="+")
    parser.add_argument("--db", type=Path, default=Path.home() / ".codex" / "logs_2.sqlite")
    args = parser.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    report: dict[str, object] = {}
    for thread_id in args.thread_ids:
        rows = con.execute(
            "select ts, feedback_log_body from logs "
            "where target='codex_core::session::turn' and "
            "(thread_id=? or feedback_log_body like ?) order by ts",
            (thread_id, f"%{thread_id}%"),
        ).fetchall()
        previous: int | None = None
        seen_turns: set[str] = set()
        turns: list[dict[str, object]] = []
        for ts, body in rows:
            total = int(field(body, "total_usage_tokens") or 0)
            turn_id = field(body, "turn_id") or field(body, "turn.id")
            if not total or (turn_id and turn_id in seen_turns):
                continue
            if turn_id:
                seen_turns.add(turn_id)
            delta = total if previous is None or total < previous else total - previous
            previous = total
            turns.append(
                {
                    "ts": ts,
                    "turn_id": turn_id,
                    "model": field(body, "model"),
                    "effort": field(body, "codex.turn.reasoning_effort") or field(body, "reasoning_effort"),
                    "cumulative": total,
                    "delta": delta,
                }
            )
        report[thread_id] = {
            "turn_count": len(turns),
            "turn_tokens": sum(int(turn["delta"]) for turn in turns),
            "model": turns[-1]["model"] if turns else "",
            "effort": turns[-1]["effort"] if turns else "",
            "turns": turns,
        }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
