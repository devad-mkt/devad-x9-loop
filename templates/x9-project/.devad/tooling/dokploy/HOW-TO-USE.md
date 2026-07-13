# Dokploy API Guide

Use this template for scoped reads and owner-approved deploys. Replace every
placeholder from current project truth. Do not commit credentials or full API
responses.

## Required Inputs

- `DOKPLOY_BASE_URL`, for example `https://dokploy.example.com`
- `DOKPLOY_API_KEY`, supplied only through process memory or a secret manager
- exact application ID and expected Git branch from durable project facts

Never hardcode a real API key, private key-file path, application ID, domain,
or production branch in this reusable template.

## Safe Read Pattern

```powershell
$base = $env:DOKPLOY_BASE_URL.TrimEnd('/')
$key = $env:DOKPLOY_API_KEY
if (-not $base -or -not $key) { throw 'Missing Dokploy environment variables.' }
$headers = @{ 'x-api-key' = $key; Accept = 'application/json' }

Invoke-WebRequest `
  -Uri "$base/api/trpc/settings.getOpenApiDocument" `
  -Headers $headers -UseBasicParsing
```

Project-specific reads may inspect safe fields such as app name, status,
branch, repository, auto-deploy, deployment ID, short title, and timestamps.
Do not save environment responses, credentials, tokens, or full logs.

## Destructive Guard

Never delete or recreate apps, databases, volumes, networks, domains,
certificates, registries, or compose services. Never rotate secrets, bulk-edit
environment variables, prune, reset, rollback, force-push, or change deploy
branches without an explicit task-specific owner approval and rollback plan.

## Deploy Gate

Before an owner-approved deploy:

1. Verify repo path, branch, HEAD, dirty files, and remote HEAD.
2. Verify the Dokploy branch and latest deployment safe fields.
3. Confirm the intended commit and migration/env/queue risks.
4. Trigger only the approved application and action.
5. Poll to a terminal state.
6. Verify health plus task-specific browser/API proof.
7. Record only non-secret proof fields.

Read the project-specific `.devad` deploy rules before using this template.
