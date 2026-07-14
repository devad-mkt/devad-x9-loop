# X9 Loop Lite State

`SNAPSHOT.json` is tracked recovery truth. `loop.db` is an ignored disposable
SQLite cache. `runtime/ACTION.json` is generated and contains the one action
Linx may perform.

Owner input is immutable, content-addressed local sensitive state. Write the
packet once at .devad/manager/owner-packets/<packet_sha256>.json and copy each
attachment under .devad/manager/owner-packets/artifacts/. Project Git ignores
raw packets and attachments. SNAPSHOT.json stores only hashes and local paths.
Back up raw content only through the owner-approved private backup flow.

The filename stem is its SHA-256 in both locations. Task `owner_packet_path` and
`owner_packet_sha256` identify the packet; the controller verifies it and every
copied artifact before dispatch, then includes bounded `local_work` in the
generated action packet. Worker and Thinx receipts are immutable event-scoped
files at `.devad/workers/<actor>/receipts/<event_id>.json`; the callback carries
the SHA-256 of those exact bytes.

Use `loopctl.py rebuild` when the cache is missing or corrupt. Do not parse
`STATUS.md`, `HANDOFFS.md`, or old `manager/loop/` files as current authority.
