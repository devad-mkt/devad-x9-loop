# Devad Deploy Dokploy

Use for Dokploy deploy, domains, env, logs, health, Contabo S3, Git LFS bandwidth, and production/staging safety.

## Rules

- For CORE direct API work, read `.devad/tooling/dokploy/HOW-TO-USE.md` once.
  It contains the current safe dry-test pattern and stricter no-delete/no-env-wipe
  rules.
- Ask internally: `What exact fact do I need?` before any Dokploy read.
- Prefer targeted status, health, latest deployment result, selected branch, selected commit, or short log tail over broad app config.
- Never print raw env, provider credentials, build secrets, tokens, passwords, private keys, or full app JSON.
- Never save full `/application.one` or `/deployment.all` responses to repo files. Keep them in memory and project only safe fields.
- Dokploy app slug and internal API `applicationId` can differ. For CORE, `core-0vmpid` is the app slug; as of 2026-06-19 the internal API `applicationId` is `FMgiOT89JU7bVD1shTPxX`. Reconfirm with `/application.search` before deploys instead of guessing.
- If MCP auth fails but a direct API key is known or supplied by the owner, use narrow direct API calls rather than retrying noisy MCP. Do not write the raw API key to repo files, `.env`, logs, or `.devad` docs.
- For deploys, load `.devad/rules/x9-branch-deploy-policy.md`, confirm local branch/HEAD, remote branch HEAD, Dokploy configured branch, and latest deployment safe fields first; then trigger deploy and poll status by deployment id.
- New X9 feature work belongs on `feature/post-mcp-cli-api-proof-runner-2026-06-22`; `feature/post-v105-native-migration-2026-06-18` is live/Dokploy deploy-only unless the user explicitly requests a live hotfix.
- If a live hotfix lands on v105, reconcile it back to X9 before final handoff or record the missing reconciliation as a blocker.
- If the user asked for deploy/live proof and Dokploy is pinned to v105 while the implementation is only on X9, do not end as complete. Use the deploy closure gate in `.devad/rules/x9-branch-deploy-policy.md`: controlled deploy bridge, explicit owner branch switch, or blocked handoff.
- Git LFS bandwidth is deploy/download artifact cost, not Codex token cost. Stop clone/deploy loops and inspect `.gitattributes` plus `git lfs ls-files` before another deploy.
- Generated Graphify/CodeFlow reports, zips, dumps, and baselines should not live in deploy branches.

## Direct API Fast Path

Use this before declaring Dokploy blocked:

1. Verify the API key can read the OpenAPI document:

```powershell
$headers = @{ 'x-api-key' = $env:DOKPLOY_API_KEY; Accept = 'application/json' }
Invoke-WebRequest `
  -Uri 'https://dok2.devad.me/api/trpc/settings.getOpenApiDocument' `
  -Headers $headers `
  -UseBasicParsing
```

2. Find the internal application id from the slug/name:

```powershell
Invoke-RestMethod `
  -Uri 'https://dok2.devad.me/api/application.search?q=core' `
  -Headers $headers
```

Expected safe fields for CORE: app name `core`, app slug `core-0vmpid`, internal `applicationId` `FMgiOT89JU7bVD1shTPxX`. If this differs, trust the fresh API response.

3. Read app/deploy status with the internal id, not the slug, and project safe fields only:

```powershell
$appId = 'FMgiOT89JU7bVD1shTPxX'
$app = Invoke-RestMethod -Uri "https://dok2.devad.me/api/application.one?applicationId=$appId" -Headers $headers
[ordered]@{
  applicationId = $app.applicationId
  name = $app.name
  appName = $app.appName
  status = $app.applicationStatus
  sourceType = $app.sourceType
  repository = $app.repository
  branch = $app.branch
  autoDeploy = $app.autoDeploy
}
```

If `/api/trpc/settings.getOpenApiDocument` returns `200` but `/api/application.one?applicationId=core-0vmpid` returns `401`, the key may be valid and the id is probably wrong. Run `/application.search` before trying other auth headers or claiming a credential blocker.

4. Trigger deploy only after local HEAD equals remote branch HEAD:

```powershell
git rev-parse HEAD
git ls-remote --heads origin feature/post-v105-native-migration-2026-06-18

$body = @{
  applicationId = $appId
  title = "Codex deploy <slice> <short-sha>"
  description = "Deploy current pushed feature branch for proof"
} | ConvertTo-Json -Compress

Invoke-RestMethod `
  -Method Post `
  -Uri 'https://dok2.devad.me/api/application.deploy' `
  -Headers ($headers + @{ 'Content-Type' = 'application/json' }) `
  -Body $body
```

5. Poll `/deployment.all` until the latest matching deployment reaches `done`, `failed`, `error`, or `cancelled`. The response shape may be a direct array, `{ items: [...] }`, or an older TRPC envelope; normalize before matching:

```powershell
function Get-DokployDeploymentItems($value) {
  if ($null -eq $value) { return @() }
  if ($value -is [array]) { return @($value) }
  if ($value.items) { return @($value.items) }
  if ($value.deployments) { return @($value.deployments) }
  if ($value.result -and $value.result.data -and $value.result.data.json) {
    $json = $value.result.data.json
    if ($json.items) { return @($json.items) }
    if ($json -is [array]) { return @($json) }
    return @($json)
  }
  return @($value)
}
```

`/application.deploy` can return an empty body even when it successfully triggers. If that happens, poll `/deployment.all` and match by exact title or full commit in the description. Record only safe fields: app name, branch, commit/title, deployment id, status, health result, and timestamp.

## Proof

Summaries should include safe fields only: app name, branch, commit/title, deploy id, status, domain/health result, timestamp, and short non-secret error.
