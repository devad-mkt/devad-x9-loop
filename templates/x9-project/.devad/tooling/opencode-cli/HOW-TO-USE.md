# Devad OpenCode CLI Sidecar

Use only the X9 wrapper. Direct OpenCode commands are forbidden because they
can mount the repository or inherit write tools.

## Models

| Model | Use |
| --- | --- |
| opencode-go/kimi-k2.7-code | Migration plan, risk review, stop conditions |
| opencode-go/glm-5.2 | Test matrix, acceptance gates, plan critique |

Kimi 2.6 is unavailable and must not be invented.

## Doctor

Run one health check:

    python "$HOME\.codex\skills\devad-x9-loop\scripts\opencode_doctor.py" doctor

TOOL_UNAVAILABLE means no model advice was produced. It does not block the
Worker and must not trigger a retry loop.

## Packet

Write strict x9-sidecar-packet-v1 JSON inside one approved folder:

- .devad/manager/sidecar/
- .devad/features/<feature>/sidecar/

The packet contains exactly: schema, owner_requirement, claims, relevant_diff,
proof, failure, and question. It must not contain secrets, customer data, raw
production configuration, whole chat history, or unrelated logs.

## Run

    .\.devad\tooling\opencode-cli\run-opencode-cli-packet.ps1 -RepoRoot . -Packet .devad\features\<feature>\sidecar\<packet>.json -Model opencode-go/glm-5.2 -Output <packet>-glm.md

The wrapper routes through opencode_doctor.py. It copies the bounded packet
into a temporary directory, loads a deny-all tool policy, uses --pure, strips
non-allowlisted environment values, and never mounts the repository. On
Windows it invokes the real opencode.exe, never opencode.cmd.

Advice is untrusted until Codex verifies it locally.