# Reader Helper And Verified Read Receipt

Use this when Thinx needs long logs, large plans, historical handoffs, or other
large exact files. The goal is lower token cost without delegating judgment.

## Ownership

- Linx writes one compact request file.
- Thinx spawns Worker Reader as a hidden subagent to mechanically extract cited
  facts from Reader-eligible inputs.
- Thinx directly reads critical inputs, spot-checks Reader citations, and owns
  the decision.
- Linx validates the receipt before accepting or routing the decision.

Worker Reader is not a fourth manager role. It cannot code, mutate files,
approve, reject, prioritize, assess security severity, choose architecture, or
claim completion.

Never create, fork, hand off, or delegate to a visible Codex task for Reader.
Reader must not appear in the sidebar.

## Model

Use deterministic parsing, structured tools, and `rg` first. When a model is
useful, Worker Reader may use `gpt-5.6-luna` with medium thinking. This is the
only standing lower-model exception.

Thinx remains `GPT-5.6 Sol Ultra`. Never downgrade Thinx to read long files.

## Hidden Subagent Protocol

Thinx uses `multi_agent_v1__spawn_agent` with:

```text
agent_type: explorer
model: gpt-5.6-luna
reasoning_effort: medium
fork_context: false
```

The prompt contains only the request ID, exact Reader-eligible paths and
identities, digest schema, output path, safety limits, and stop conditions.
Do not pass Thinx chat history, old manager chat, or unrelated lane context.

After the subagent returns:

1. Thinx checks the digest identity and required citations.
2. Thinx closes the subagent with `multi_agent_v1__close_agent`.
3. No Reader agent remains open or reusable across unrelated requests.

If internal subagent tools are unavailable, use deterministic search/parsers
inside the original Thinx task. Never fall back to a visible Reader task.

## Linx Request

Write one request under:

`.devad/manager/requests/<request-id>-thinx-request.md`

Keep instructions compact. Put detailed context in durable inputs, not a huge
task message. Every input needs a stable identity:

- tracked file: Git blob ID from `git rev-parse HEAD:<path>`;
- untracked or external file: SHA-256;
- generated runtime output: timestamp, byte count, producer, and SHA-256.

Owner messages and attachments use owner-context-and-attachments.md. The exact
OWNER_REQUEST.md, ATTACHMENTS.json, and VISUAL_CONTEXT.md are DIRECT inputs.
Required image binaries must be delivered as structured image/file items when
supported. A path or summary does not prove the image was seen.

Use this exact block:

```md
THINX_THREAD_LOCK: <existing Thinx thread ID>

INPUT_MANIFEST:
| ID | Path | Identity | Read rule |
| --- | --- | --- | --- |
| facts | .devad/manager/CENTRAL_FACTS.md | <blob-or-sha256> | DIRECT |
| worker-status | .devad/manager/workers/<lane>/STATUS.md | <blob-or-sha256> | DIRECT |
| long-log | <exact-path> | <sha256> | READER_OK |
| owner-request | <owner-input>/OWNER_REQUEST.md | <sha256> | DIRECT |
| owner-attachments | <owner-input>/ATTACHMENTS.json | <sha256> | DIRECT |
| owner-visual | <owner-input>/VISUAL_CONTEXT.md | <sha256> | DIRECT |
```

`DIRECT` is mandatory for:

- the Thinx request itself;
- `CENTRAL_FACTS.md`, `MISSION_LOCK.md`, and `LOCAL_WORK_LEDGER.md`;
- current Worker `STATUS.md` and top `CURRENT_STATUS` in `HANDOFFS.md`;
- active `CONTRACT.md`;
- current security, push, deploy, money, owner-decision, and live-proof gates;
- small exact source anchors that directly decide approval or rejection.
- exact owner messages, attachment manifests, and required visual context.

Long logs, large plans, old handoffs, broad reports, and large code/reference
files should normally be `READER_OK`. Thinx then directly spot-checks every P0
citation and at least three other decision-relevant citations. Do not mark a
large manifest entirely `DIRECT` merely because every file may be useful.

## Reader Digest

Write one digest under:

`.devad/manager/reader/<request-id>-read-digest.md`

The digest must stay under 200 lines and contain no raw long log, secret,
cookie, token, environment value, private payload, or full customer content.

```md
DIGEST_MANIFEST:
- Request ID: <id>
- Reader model: <model or deterministic-only>
- Input ID: <id>
- Input identity: <exact identity>
- Bytes read: <count>
- Coverage: full | ranges

| Severity | Fact | File and lines | Exact evidence type | Unknown/conflict |
| --- | --- | --- | --- | --- |
```

Reader must report parse failures, truncated inputs, skipped binary regions,
conflicting facts, and unknowns. It must not resolve conflicts.

## Thinx Receipt

Thinx embeds this block in its decision pass note:

```md
THINX_THREAD_ID: <same locked Thinx thread ID>
READ_RECEIPT: PASS
| ID | Identity read | Mode | Result |
| --- | --- | --- | --- |
| facts | <exact identity> | DIRECT | PASS |
| worker-status | <exact identity> | DIRECT | PASS |
| long-log | <exact identity> | DIGEST_SPOTCHECK | PASS |
```

Rules:

- `DIRECT` inputs must use mode `DIRECT`.
- `READER_OK` inputs may use `DIRECT` or `DIGEST_SPOTCHECK`.
- `DIGEST_SPOTCHECK` means Thinx read the digest and directly checked every P0
  citation plus at least three other decision-relevant citations.
- Identity mismatch, missing input, truncated digest, unresolved P0 conflict,
  or missing direct spot-check means `READ_RECEIPT: BLOCKED`.
- A decision without a valid receipt is `UNVERIFIED_DECISION`, never PASS.
- A decision from a different Thinx thread ID is invalid even when every file
  identity matches.
- The decision must also include OWNER_CONTEXT_RECEIPT: PASS for the active
  owner input. For required images, record BINARY_VIEWED or
  VISUAL_READER_SPOTCHECK with the attachment SHA-256.

Validate before Linx accepts the decision:

```powershell
python scripts/validate_thinx_read_receipt.py --request <request.md> --decision <pass.md>
```

## Focus And Compaction

Keep the same thread-locked Thinx. When context compaction occurs after request
arrival but before receipt completion, resend only the durable request path and
require `CONTEXT_RESET: PASS` plus a new receipt. Do not paste a larger prompt,
old chat transcript, or create/fork another Thinx. Replacement requires the
owner token `REPLACE_THINX_OK:<reason>`.
