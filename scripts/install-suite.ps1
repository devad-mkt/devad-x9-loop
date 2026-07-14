param(
    [string]$CodexHome = "$HOME\.codex",
    [string]$ProjectRoot = "",
    [string]$Python = "python",
    [string]$SkillValidator = "",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Skills = @(
    "devad-x9",
    "devad-x9-loop",
    "devad-x9-manager",
    "codex-x9-backup",
    "codex-token-budget",
    "devad-memory"
)

Write-Host "X9 Loop Lite v6 source: $PackageRoot"
Write-Host "Codex home: $CodexHome"

if (-not $Apply) {
    Write-Host "DRY RUN: no files changed."
    foreach ($Skill in $Skills) {
        Write-Host "Would stage, validate, back up, and install: $Skill"
    }
    if ($ProjectRoot) {
        Write-Host "Would create .devad only if absent: $ProjectRoot"
    }
    exit 0
}

& $Python (Join-Path $PSScriptRoot "validate_suite.py")
if ($LASTEXITCODE -ne 0) {
    throw "Package validation failed before install."
}

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$SkillsRoot = Join-Path $CodexHome "skills"
$StageRoot = Join-Path $CodexHome "x9-install-staging\$Stamp"
$BackupRoot = Join-Path $CodexHome "x9-install-backups\$Stamp"
$FailedRoot = Join-Path $CodexHome "x9-install-failed\$Stamp"
New-Item -ItemType Directory -Force -Path $SkillsRoot, $StageRoot, $BackupRoot | Out-Null

foreach ($Skill in $Skills) {
    $Source = Join-Path $PackageRoot "skills\$Skill"
    $Stage = Join-Path $StageRoot $Skill
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing package skill: $Skill"
    }
    Copy-Item -LiteralPath $Source -Destination $Stage -Recurse
}

if (-not $SkillValidator) {
    $Candidate = Join-Path $CodexHome "skills\.system\skill-creator\scripts\quick_validate.py"
    if (Test-Path -LiteralPath $Candidate) {
        $SkillValidator = $Candidate
    }
}

if ($SkillValidator) {
    foreach ($Skill in $Skills) {
        & $Python $SkillValidator (Join-Path $StageRoot $Skill)
        if ($LASTEXITCODE -ne 0) {
            throw "Official skill validation failed in staging: $Skill"
        }
    }
}

$Installed = New-Object System.Collections.Generic.List[string]
$ProjectStage = $null
$ProjectInstalled = $false
$DevadTarget = $null
try {
    foreach ($Skill in $Skills) {
        $Target = Join-Path $SkillsRoot $Skill
        $Backup = Join-Path $BackupRoot $Skill
        $Stage = Join-Path $StageRoot $Skill
        if (Test-Path -LiteralPath $Target) {
            Move-Item -LiteralPath $Target -Destination $Backup
        }
        Move-Item -LiteralPath $Stage -Destination $Target
        $Installed.Add($Skill)
    }

    if ($ProjectRoot) {
        $ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
        if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
            throw "Project root is missing: $ProjectRoot"
        }
        $projectItem = Get-Item -LiteralPath $ProjectRoot -Force
        if (($projectItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Project root cannot be a reparse path: $ProjectRoot"
        }
        $DevadTarget = Join-Path $ProjectRoot ".devad"
        if (Test-Path -LiteralPath $DevadTarget) {
            throw "Project .devad exists. Use migrate_project.py; installer never overwrites it."
        }
        $ProjectStage = Join-Path $ProjectRoot ".devad.x9-stage-$Stamp"
        if (Test-Path -LiteralPath $ProjectStage) {
            throw "Project stage already exists: $ProjectStage"
        }
        $Template = Join-Path $PackageRoot "templates\x9-project\.devad"
        Copy-Item -LiteralPath $Template -Destination $ProjectStage -Recurse
        if (-not (Test-Path -LiteralPath (Join-Path $ProjectStage "ROUTER.md") -PathType Leaf)) {
            throw "Project template staging validation failed: $ProjectStage"
        }
        Move-Item -LiteralPath $ProjectStage -Destination $DevadTarget
        $ProjectInstalled = $true
    }
}
catch {
    New-Item -ItemType Directory -Force -Path $FailedRoot | Out-Null
    if ($ProjectInstalled -and $DevadTarget -and (Test-Path -LiteralPath $DevadTarget)) {
        Move-Item -LiteralPath $DevadTarget -Destination (Join-Path $FailedRoot "project-overlay-installed")
    }
    elseif ($ProjectStage -and (Test-Path -LiteralPath $ProjectStage)) {
        Move-Item -LiteralPath $ProjectStage -Destination (Join-Path $FailedRoot "project-overlay-stage")
    }
    foreach ($Skill in $Installed) {
        $Target = Join-Path $SkillsRoot $Skill
        if (Test-Path -LiteralPath $Target) {
            Move-Item -LiteralPath $Target -Destination (Join-Path $FailedRoot $Skill)
        }
    }
    foreach ($Skill in $Skills) {
        $Backup = Join-Path $BackupRoot $Skill
        $Target = Join-Path $SkillsRoot $Skill
        if ((Test-Path -LiteralPath $Backup) -and -not (Test-Path -LiteralPath $Target)) {
            Move-Item -LiteralPath $Backup -Destination $Target
        }
    }
    throw
}

Write-Host "PASS: installed six skills"
Write-Host "Rollback backup: $BackupRoot"
