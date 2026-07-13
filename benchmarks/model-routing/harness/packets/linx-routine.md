# Linx Routine Benchmark Packet

ROLE: Linx routine file pickup and routing. Read only this packet. Do not read
chat, other files, or use tools.

## Contract

- Choose exactly one next action.
- Do not code, route a Worker, push, deploy, or ask the owner in this pass.
- Treat stale manager truth as a routing stop.
- Return exactly one JSON object, no Markdown.

## Durable Facts

- `CENTRAL_FACTS.md` and `MISSION_LOCK.md` were updated at 04:18.
- `LOCAL_WORK_LEDGER.md` and `HANDOFF_INDEX.md` were updated at 13:13.
- Current repo checkout: rescue branch with 12 tracked dirty and 76 untracked
  `.devad` files. Ledger says active-lane local app work is `NO`.
- Brand Worker status says remote provenance review is complete and recommends
  a new isolated integration Worker on remote base `0a082488...`.
- Brand Worker explicitly says Linx must review first; no source integration,
  push, bridge, or deploy is approved by that Worker.
- AI Agent is paused behind Brand.
- SEO is owner-controlled and excluded.
- Owner action is `NONE`.
- X9 manager contract says stale central facts or mission lock stop routing
  until current durable truth is rebuilt.

## Output Schema

{"next_action":"...","classification":"...","owner_action":"...","why":"...","must_not":"..."}
