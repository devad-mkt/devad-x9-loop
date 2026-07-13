from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class UsageEvent:
    thread_id: str
    turn_id: str
    model: str
    effort: str
    total_tokens: int
    source: str


def read_usage_events(rows: list[tuple[int, str | None, str]]) -> list[UsageEvent]:
    """Parse the legacy response.completed rows currently understood."""
    events: list[UsageEvent] = []
    totals: dict[str, int] = {}
    seen_turns: set[tuple[str, str]] = set()
    for _ts, row_thread_id, body in rows:
        fields = {
            key: quoted or unquoted
            for key, quoted, unquoted in re.findall(
                r'\b(thread_id|turn_id|model|codex\.turn\.reasoning_effort)=(?:"([^"]*)"|([^\s}:]+))', body
            )
        }
        total_match = re.search(r'\btotal_usage_tokens=(\d+)\b', body)
        if total_match and all(key in fields for key in ("thread_id", "turn_id", "model", "codex.turn.reasoning_effort")):
            thread_id = fields["thread_id"]
            turn_key = (thread_id, fields["turn_id"])
            if turn_key in seen_turns:
                continue
            seen_turns.add(turn_key)
            total = int(total_match.group(1))
            previous = totals.get(thread_id, 0)
            delta = total - previous if total >= previous else total
            totals[thread_id] = total
            if delta:
                events.append(
                    UsageEvent(
                        thread_id=thread_id,
                        turn_id=fields["turn_id"],
                        model=fields["model"],
                        effort=fields["codex.turn.reasoning_effort"],
                        total_tokens=delta,
                        source="turn.telemetry",
                    )
                )
            continue

        marker = "SSE event: "
        if marker not in body or '"type":"response.completed"' not in body:
            continue
        payload = json.loads(body.split(marker, 1)[1])
        response = payload.get("response") or {}
        usage = response.get("usage") or {}
        events.append(
            UsageEvent(
                thread_id=str((response.get("metadata") or {}).get("conversation_id") or row_thread_id or ""),
                turn_id="",
                model=str(response.get("model") or ""),
                effort="",
                total_tokens=int(usage.get("total_tokens") or 0),
                source="response.completed",
            )
        )
    return events
