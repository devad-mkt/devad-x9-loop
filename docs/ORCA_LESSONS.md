# Orca Lessons

Adopted concepts:

- task and dispatch identity;
- dependency-ready queue;
- decision gates;
- scoped completion authority;
- three-failure circuit breaker;
- stale Worker warning without auto-kill;
- full handoff versus supervised dispatch.

Rejected mechanisms:

- Orca runtime integration or runtime database truth;
- four coding Workers by default;
- 20-commit stale allowance;
- two-second model polling;
- automatic Worker termination.

Git and durable .devad files remain truth.
