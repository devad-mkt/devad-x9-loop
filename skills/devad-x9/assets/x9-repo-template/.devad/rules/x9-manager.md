# X9 User-Managed Multi-Chat

Use this only when the user wants multiple Codex chats/worktrees working on the
same repository.

## Core Rule

The user is the manager. Codex can prepare prompts, check reports, review diffs,
and recommend merge order, but it must not create a heavy local control plane or
burn tokens watching workers. Workers run as ordinary task chats using X5-style
discipline.

## Setup

1. Split work only by clear file/path ownership.
2. Use short worktree paths under `<worktree-root>\<lane>` unless the
   user chooses another root.
3. One worker chat gets one lane and one branch.
4. Worker prompt must include allowed files, denied files, expected tests, stop
   rules, and report format.
5. Workers must not edit `.devad` unless their task explicitly requires it.

## Isolation

- Each worker has its own worktree and branch.
- Each worker owns a small path list. Shared files need manager approval before
  edits.
- Workers do not read other worker worktrees or handoffs unless the manager
  gives a specific handoff.
- No worker merges, deploys, force-pushes, or rebases shared branches without
  explicit user approval.

## Combining

1. Collect worker report.
2. Inspect `git status`, `git diff --name-status`, and the actual diff.
3. Check file overlap against other workers before merge.
4. Run the lane tests and any cross-lane smoke needed by touched shared files.
5. Merge one lane at a time.
6. Update the task handoff after each accepted lane.

## Conflict Policy

- If two workers changed the same file, stop and review both diffs manually.
- Prefer the smallest behavior-preserving merge over replaying a whole worker
  branch.
- If a worker edited outside its lane, treat it as not ready until explained or
  reverted by that worker.

## Worker Report Contract

```text
Worktree:
Branch/HEAD:
Task:
Files touched:
Tests run:
Browser proof:
Known risks:
Ready to merge? yes/no
```

## Sidecars

Use sidecars only as bounded reviewers through direct headless CLI. Do not use
ACP, PI workflow execution, or OpenRouter. Codex verifies useful claims locally
before edits or final claims.
