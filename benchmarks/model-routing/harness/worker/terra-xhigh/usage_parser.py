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


_TURN_TELEMETRY = re.compile(
    r'\b(thread_id|turn_id|model|codex\.turn\.reasoning_effort|total_usage_tokens)='
    r'(?:"([^"]*)"|([^\s}]+))'
)


def read_usage_events(rows: list[tuple[int, str | None, str]]) -> list[UsageEvent]:
    """Parse response.completed and current turn telemetry rows."""
    events: list[UsageEvent] = []
    previous_totals: dict[str, int] = {}
    seen_turns: set[tuple[str, str]] = set()
    for _ts, row_thread_id, body in rows:
        marker = "SSE event: "
        if marker in body and '"type":"response.completed"' in body:
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
            continue

        values = {
            name: quoted_value or unquoted_value
            for name, quoted_value, unquoted_value in _TURN_TELEMETRY.findall(body)
        }
        if not {"thread_id", "turn_id", "model", "codex.turn.reasoning_effort", "total_usage_tokens"} <= values.keys():
            continue

        thread_id = values["thread_id"] or str(row_thread_id or "")
        turn_id = values["turn_id"]
        key = (thread_id, turn_id)
        if turn_id and key in seen_turns:
            continue
        if turn_id:
            seen_turns.add(key)

        total_tokens = int(values["total_usage_tokens"])
        previous_total = previous_totals.get(thread_id)
        delta = total_tokens if previous_total is None or total_tokens < previous_total else total_tokens - previous_total
        previous_totals[thread_id] = total_tokens
        if delta <= 0:
            continue

        events.append(
            UsageEvent(
                thread_id=thread_id,
                turn_id=turn_id,
                model=values["model"],
                effort=values["codex.turn.reasoning_effort"],
                total_tokens=delta,
                source="codex.turn.telemetry",
            )
        )
    return events
