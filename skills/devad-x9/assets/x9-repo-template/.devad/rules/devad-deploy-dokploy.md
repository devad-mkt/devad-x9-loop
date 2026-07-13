# Deploy With Dokploy

Use this rule for scoped Dokploy reads and owner-approved deploys. Load the
project's branch/deploy policy and `.devad/tooling/dokploy/HOW-TO-USE.md` first.

## Rules

- Ask `What exact fact is needed?` before an API read.
- Prefer health, current branch, current commit, latest deployment, or a short
  non-secret log tail over broad configuration reads.
- Keep API keys only in process memory or a secret manager.
- Never print environment values, credentials, tokens, passwords, private keys,
  full app JSON, or full deployment responses.
- App slug and internal `applicationId` may differ. Discover the current ID
  through a narrow search; never reuse an ID from a template.
- Confirm local branch/HEAD, remote branch HEAD, Dokploy configured branch, and
  latest deployment before triggering anything.
- New implementation and live hotfix branches are separate unless the durable
  project policy explicitly says otherwise.
- Reconcile an approved live hotfix back to the implementation branch or record
  the missing reconciliation as a blocker.
- Stop repeated clone/deploy loops when Git LFS bandwidth or artifact placement
  is the real issue.
- Never place generated reports, archives, dumps, or baselines in deploy images.

## Read-Only Fast Path

```powershell
$base = $env:DOKPLOY_BASE_URL.TrimEnd('/')
$headers = @{ 'x-api-key' = $env:DOKPLOY_API_KEY; Accept = 'application/json' }

Invoke-WebRequest `
  -Uri "$base/api/trpc/settings.getOpenApiDocument" `
  -Headers $headers -UseBasicParsing

$query = [uri]::EscapeDataString('<application-name-or-slug>')
$search = Invoke-RestMethod `
  -Uri "$base/api/application.search?q=$query" `
  -Headers $headers
```

Project only safe fields: app name, status, repository, branch, auto-deploy,
deployment ID, short title, and timestamps.

## Deploy Gate

Deploy only after the owner approves the exact app/action and all project gates
pass:

1. Local intended HEAD equals the pushed remote HEAD.
2. Security and commit attestation pass for the exact range.
3. Dokploy is configured for the intended branch.
4. Migration, environment, queue, worker, and rollback risks are classified.
5. A live health/browser/API proof plan exists.

Trigger the documented project action, then poll deployment state to `done`,
`failed`, `error`, or `cancelled`. An empty trigger response may still mean the
deployment started; confirm through the deployment list and exact title/commit.

## Absolute No

Do not delete or recreate apps, databases, volumes, networks, domains,
certificates, registries, or compose services. Do not rotate secrets, bulk-edit
environment variables, prune, reset, rollback, force-push, or change branches
without explicit owner approval and a rollback plan.

## Proof

Record only app name, branch, commit/title, deployment ID, status, health result,
timestamp, and a short non-secret error.
