param(
    [string]$TargetProfile = $env:USERPROFILE,
    [string]$RepoPath,
    [switch]$DryRun,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $RepoPath -or $RepoPath.Trim().Length -eq 0) {
    $RepoPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
}

if (-not $DryRun -and -not $Apply) {
    $DryRun = $true
}

function Assert-SourceExists {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing backup source: $Path"
    }
}

function Assert-CodexStopped {
    $running = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @('Codex', 'codex') }
    if ($running) {
        $names = ($running | Select-Object -ExpandProperty ProcessName -Unique) -join ', '
        throw "BLOCKED: Codex is running ($names). Fully exit Codex before applying restore."
    }
}

function Invoke-RobocopyRestore {
    param([string]$Source, [string]$Destination)
    Assert-SourceExists $Source
    if ($DryRun) {
        $files = Get-ChildItem -LiteralPath $Source -Recurse -File -Force -ErrorAction SilentlyContinue
        $bytes = ($files | Measure-Object Length -Sum).Sum
        [pscustomobject]@{ Source = $Source; Destination = $Destination; Files = ($files | Measure-Object).Count; MB = [math]::Round($bytes / 1MB, 2) }
        return
    }
    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    & robocopy $Source $Destination /MIR /R:2 /W:1 /COPY:DAT /DCOPY:DAT /FFT /XJ | Out-Host
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy restore failed from $Source to $Destination with exit code $LASTEXITCODE"
    }
}

$snapshot = Join-Path $RepoPath 'snapshot'
Assert-SourceExists $snapshot

if ($Apply) {
    Assert-CodexStopped
}

$targetCodex = Join-Path $TargetProfile '.codex'
$targetAgents = Join-Path $TargetProfile '.agents'
$targetOpenCode = Join-Path $TargetProfile '.config\opencode'

$pairs = @(
    @((Join-Path $snapshot 'dot-codex\sessions'), (Join-Path $targetCodex 'sessions')),
    @((Join-Path $snapshot 'dot-codex\archived_sessions'), (Join-Path $targetCodex 'archived_sessions')),
    @((Join-Path $snapshot 'dot-codex\skills'), (Join-Path $targetCodex 'skills')),
    @((Join-Path $snapshot 'dot-codex\skills-disabled'), (Join-Path $targetCodex 'skills-disabled')),
    @((Join-Path $snapshot 'dot-codex\memories'), (Join-Path $targetCodex 'memories')),
    @((Join-Path $snapshot 'dot-codex\rules'), (Join-Path $targetCodex 'rules')),
    @((Join-Path $snapshot 'dot-codex\automations'), (Join-Path $targetCodex 'automations')),
    @((Join-Path $snapshot 'dot-codex\state'), (Join-Path $targetCodex 'state')),
    @((Join-Path $snapshot 'dot-codex\tooling'), (Join-Path $targetCodex 'tooling')),
    @((Join-Path $snapshot 'dot-codex\attachments'), (Join-Path $targetCodex 'attachments')),
    @((Join-Path $snapshot 'dot-codex\generated_images'), (Join-Path $targetCodex 'generated_images')),
    @((Join-Path $snapshot 'dot-codex\recovered_project_chats'), (Join-Path $targetCodex 'recovered_project_chats')),
    @((Join-Path $snapshot 'dot-agents'), $targetAgents),
    @((Join-Path $snapshot 'dot-config-opencode'), $targetOpenCode)
)

$plan = foreach ($pair in $pairs) {
    if (Test-Path -LiteralPath $pair[0]) {
        Invoke-RobocopyRestore -Source $pair[0] -Destination $pair[1]
    }
}

$rootSource = Join-Path $snapshot 'dot-codex'
$rootFiles = @(
    'session_index.jsonl',
    'state_5.sqlite',
    '.codex-global-state.json',
    '.codex-global-state.json.bak',
    'config.toml',
    'version.json',
    'models_cache.json',
    'installation_id',
    'chrome-native-hosts.json',
    'chrome-native-hosts-v2.json',
    'goals_1.sqlite',
    'memories_1.sqlite'
)

if ($DryRun) {
    $plan | Format-Table -AutoSize | Out-String -Width 260 | Write-Host
    $rootPlan = foreach ($name in $rootFiles) {
        $src = Join-Path $rootSource $name
        [pscustomobject]@{ Source = $src; Destination = (Join-Path $targetCodex $name); Exists = (Test-Path -LiteralPath $src) }
    }
    $rootPlan | Format-Table -AutoSize | Out-String -Width 260 | Write-Host
    Write-Host "DRY_RUN_COMPLETE"
    Write-Host "Restore proof after apply still requires Codex app list_threads/list_projects visibility."
    exit 0
}

if (-not (Test-Path -LiteralPath $targetCodex)) {
    New-Item -ItemType Directory -Path $targetCodex -Force | Out-Null
}

foreach ($name in $rootFiles) {
    $src = Join-Path $rootSource $name
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $targetCodex $name) -Force
    }
}

Write-Host "PARTIAL: files restored. Verify Codex app visibility with list_threads and list_projects before calling restore PASS."
