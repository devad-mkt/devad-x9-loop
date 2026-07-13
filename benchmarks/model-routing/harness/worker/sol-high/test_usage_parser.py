from __future__ import annotations

import json
import unittest

from usage_parser import read_usage_events


def turn(thread: str, turn_id: str, model: str, effort: str, total: int) -> str:
    return (
        f'thread_id="{thread}" turn_id="{turn_id}" model="{model}" '
        f'codex.turn.reasoning_effort="{effort}" total_usage_tokens={total} '
        'token_limit_reached=false'
    )


class UsageParserTests(unittest.TestCase):
    def test_legacy_response_event_still_works(self) -> None:
        payload = {
            "type": "response.completed",
            "response": {
                "model": "gpt-5.5",
                "metadata": {"conversation_id": "legacy"},
                "usage": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110},
            },
        }
        rows = [(1, "legacy", "SSE event: " + json.dumps(payload, separators=(",", ":")))]
        events = read_usage_events(rows)
        self.assertEqual([event.total_tokens for event in events], [110])
        self.assertEqual(events[0].source, "response.completed")

    def test_current_turn_telemetry_uses_per_thread_deltas(self) -> None:
        rows = [
            (1, "t1", turn("t1", "a", "gpt-5.6-sol", "medium", 1000)),
            (2, "t2", turn("t2", "x", "gpt-5.6-terra", "xhigh", 400)),
            (3, "t1", turn("t1", "b", "gpt-5.6-sol", "medium", 1300)),
            (4, "t1", turn("t1", "b", "gpt-5.6-sol", "medium", 1300)),
            (5, "t1", turn("t1", "c", "gpt-5.6-sol", "medium", 1500)),
            (6, "t1", turn("t1", "d", "gpt-5.6-sol", "medium", 50)),
        ]
        events = read_usage_events(rows)
        self.assertEqual([event.total_tokens for event in events], [1000, 400, 300, 200, 50])
        self.assertEqual(events[0].effort, "medium")
        self.assertEqual(events[1].model, "gpt-5.6-terra")
        self.assertEqual(events[-1].turn_id, "d")
        self.assertTrue(all(event.total_tokens > 0 for event in events))

    def test_noise_is_ignored(self) -> None:
        self.assertEqual(read_usage_events([(1, None, "ordinary log without usage")]), [])

    def test_real_current_log_shape_is_supported(self) -> None:
        rows = [
            (
                1,
                "019f-real",
                "session_loop{thread_id=019f-real}:submission_dispatch{otel.name=dispatch "
                "model=gpt-5.6-terra codex.turn.reasoning_effort=xhigh}:session_task.run:run_turn: "
                "post sampling token usage turn_id=turn-a total_usage_tokens=25000 "
                "auto_compact_scope_tokens=24000 token_limit_reached=false",
            ),
            (
                2,
                "019f-real",
                "session_loop{thread_id=019f-real}:submission_dispatch{model=gpt-5.6-terra "
                "codex.turn.reasoning_effort=xhigh}:session_task.run:run_turn: post sampling token usage "
                "turn_id=turn-b total_usage_tokens=26000 token_limit_reached=false",
            ),
        ]
        events = read_usage_events(rows)
        self.assertEqual([event.total_tokens for event in events], [25000, 1000])
        self.assertEqual(events[-1].effort, "xhigh")


if __name__ == "__main__":
    unittest.main()
