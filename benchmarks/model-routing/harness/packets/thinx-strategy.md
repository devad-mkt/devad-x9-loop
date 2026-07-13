# Thinx Strategy Benchmark Packet

ROLE: Thinx file-only strategy. Assume every input below passed identity and
read-receipt validation. Do not read chat, other files, or use tools.

## Contract

- Choose exactly one next action for Linx.
- No code, commit, push, bridge, deploy, provider action, or owner question.
- Return exactly one JSON object, no Markdown.

## Verified Inputs

- Mission order: finish Brand first; AI Agent waits behind Brand; SEO is
  excluded.
- Remote source is `0a082488...`.
- A prior Brand C1 behavior is accepted, but its old C2 cannot be reused.
- Provenance review found no app/test overlap with remote changes and no merge
  conflict markers.
- Required safe path: create a fresh isolated integration Worker, replay only
  accepted C1 behavior onto exact remote base, rerun focused gates, create new
  C1 and C2, then stop for review before source push.
- No owner action is needed.
- No push, bridge, deploy, or live proof is approved in this step.

## Output Schema

{"next_action":"...","classification":"...","owner_action":"...","why":"...","must_not":"..."}
