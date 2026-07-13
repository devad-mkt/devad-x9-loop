# Owner Context And Attachments

Use this whenever the owner sends a new requirement, correction, image,
screenshot, document, or other attachment that affects a lane.

## Core Rule

Linx must preserve the exact owner message and every required attachment in a
durable owner-input bundle before routing Thinx, Worker, Reader, CHUNK, or
SIDE. A summary alone is not context transfer.

Lower-cost or low-thinking models receive the same complete relevant input
bundle. Saving model cost never permits dropping owner words, images,
screenshots, corrections, constraints, or acceptance details.

## Bundle

Create:

    .devad/manager/owner-input/<input-id>/
      OWNER_REQUEST.md
      ATTACHMENTS.json
      VISUAL_CONTEXT.md

Update:

    .devad/manager/owner-input/INDEX.md

OWNER_REQUEST.md contains:

- the exact owner message, verbatim and clearly delimited;
- normalized atomic requirements without replacing the verbatim text;
- feature/lane, priority, exclusions, corrections, and acceptance meaning;
- links to prior owner-input bundles that remain active;
- a SHA-256 identity.

## Attachments

Do not rely on a temporary clipboard or chat attachment path.

For each attachment:

1. create a stable project-owned or approved private path;
2. record original name, stable path, media type, bytes, SHA-256, sensitivity,
   required/optional status, and intended meaning in ATTACHMENTS.json;
3. preserve the binary when policy permits;
4. inspect images/screenshots with a visual-capable tool/model;
5. record visible facts, OCR text, UI state, annotations, and unknowns in
   VISUAL_CONTEXT.md.

If the binary cannot be stabilized or read, record
MISSING_ATTACHMENT:<attachment-id> and stop any decision that depends on it.

Sensitive attachments remain outside Git in approved private storage. The
manifest records a stable private reference and hash, never secret content.

## Routing

Every Linx request to another role includes:

    OWNER_INPUT_ID: <input-id>
    OWNER_REQUEST: <path + sha256>
    ATTACHMENT_MANIFEST: <path + sha256>
    VISUAL_CONTEXT: <path + sha256>
    REQUIRED_ATTACHMENTS: <ids>

When thread tooling supports structured image/file items, attach each required
binary to that same message. A path in text is not proof that the receiver saw
the attachment.

When the receiving model cannot inspect a binary, use a hidden visual Reader
and mark the receipt VISUAL_READER_SPOTCHECK. For UI/visual acceptance, the
decision owner must directly view the binary or spot-check the visual digest.

## Receipt Gate

Every receiving role writes or returns:

    OWNER_CONTEXT_RECEIPT: PASS
    OWNER_REQUEST_SHA256: <sha256>

and one row per required attachment:

    | attachment-id | sha256 | BINARY_VIEWED | PASS |

Allowed modes:

- BINARY_VIEWED
- VISUAL_READER_SPOTCHECK
- TEXT_DOCUMENT_READ

VISUAL_NOTES_ONLY is not sufficient when the binary is required for visual
judgment.

Validate with:

    python scripts/validate_owner_context.py --bundle <bundle> --receipt <receipt>

Missing/mismatched owner text, required attachment, hash, visual mode, or
receipt means OWNER_CONTEXT_RECEIPT: BLOCKED. The receiver must not plan,
approve, code, claim PASS, or claim BLOCKED from incomplete context.

## Delta Messages

Each new owner correction gets a new input ID. Link it to the previous bundle
and mark exactly what it supersedes. Do not overwrite the historical exact
message. Linx routes the newest active chain, not an old summary.

## Role Duties

| Role | Duty |
| --- | --- |
| Linx | Capture exact message, stabilize attachments, build/index bundle, route identities |
| Thinx | Read exact owner request and required visual evidence before decision |
| Worker | Read bundle before plan/mutation and cite it in STATUS/HANDOFFS |
| Luna Reader | Extract/inspect only; preserve requirement IDs and attachment identities |
| GLM/Kimi SIDE | Receive the secret-safe task packet plus visual facts/hashes; binary only if route supports it |

Never claim that a sidecar saw an image when it received only OCR or notes.
