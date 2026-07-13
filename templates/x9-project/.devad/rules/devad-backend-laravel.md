# Devad Backend Laravel

Use for Laravel backend, API routes, service layers, migrations, policies, jobs, Cashier, Socialite, Wayfinder, tests, and backend review.

## Rules

- Follow existing Laravel, Inertia, React, Tailwind, Cashier, Socialite, Wayfinder, Scout, Pennant, Sanctum, Reverb, and Pest conventions from `AGENTS.md`.
- Prefer existing services, models, policies, route patterns, factories, and tests over new abstractions.
- Do not add dependencies, base folders, migrations, schema changes, or package upgrades without approval and rollback notes.
- Use official/Laravel Boost docs search when changing framework behavior and the tool is available.
- Inspect schema before model/migration changes when schema facts matter.
- Frontend calls to backend routes should use Wayfinder/internal route helpers when the client is hydrated.
- Auth, billing, permissions, workspace scope, API keys, destructive operations, provider callbacks, and data writes require focused tests or explicit verification limits.

## Proof

Use the smallest focused PHP/Pest, type, route, build, browser, or smoke check that proves the changed behavior. Do not create throwaway verification scripts when tests already cover the path.
