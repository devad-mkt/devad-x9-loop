# V5 Pressure Results

## RED Baseline

The empty v5 package failed role identity, dispatch delivery, completion,
concurrency, migration, registry, template, and compatibility tests.

The current v3 manager could misroute a task named Linx even when its durable
job was Worker implementation. It also had no packet-scoped dispatch ID,
attempt ledger, exact acknowledgement, or honest sent-once proof.

## GREEN Contract

Local deterministic suite covers:

- TITLE_ROLE_MISMATCH for a Worker titled Linx - paused;
- one dispatch ID per packet and supersession for changed packets;
- accepted-without-ack as DELIVERY_UNCONFIRMED;
- exact one-attempt acknowledgement before sent_once is true;
- stale task/dispatch/role/hash/receipt completion rejection;
- dependency and resource conflict scheduling;
- two coding Worker limit and evidence-gated promotion to three;
- dry-run migration writes nothing;
- v3 inventory migration coverage.

Real model quality and token comparisons remain in dated benchmark folders and
must not be inferred from these deterministic tests.
