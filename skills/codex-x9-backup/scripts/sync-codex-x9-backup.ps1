param(
    [ValidateSet('Daily', 'DryRun')]
    [string]$Mode = 'DryRun',
    [switch]$Push,
    [string]$RepoPath,
    [string]$RepoUrl = $env:CODEX_X9_BACKUP_REMOTE,
    [string]$ProfileRoot = $env:USERPROFILE,
    [string]$Python = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $RepoPath -or $RepoPath.Trim().Length -eq 0) {
    $RepoPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
}

function Resolve-Python {
    param([string]$Preferred)
    if ($Preferred -and (Test-Path -LiteralPath $Preferred)) {
        return $Preferred
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    throw "Python not found. Pass -Python with a valid python.exe path."
}

function Invoke-RepoGit {
    param([string[]]$Arguments)
    Push-Location -LiteralPath $RepoPath
    try {
        & git @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function Ensure-Repo {
    if (-not (Test-Path -LiteralPath $RepoPath)) {
        if (-not $RepoUrl -or $RepoUrl.Trim().Length -eq 0) {
            throw 'Backup clone is missing. Pass -RepoUrl or set CODEX_X9_BACKUP_REMOTE.'
        }
        $parent = Split-Path -Parent $RepoPath
        if ($parent -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        & git clone $RepoUrl $RepoPath
        if ($LASTEXITCODE -ne 0) {
            throw "git clone failed with exit code $LASTEXITCODE"
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoPath '.git'))) {
        throw "RepoPath exists but is not a git clone: $RepoPath"
    }
}

function Write-RepoTextFile {
    param([string]$RelativePath, [string]$Content)
    $path = Join-Path $RepoPath $RelativePath
    $dir = Split-Path -Parent $path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Set-Content -LiteralPath $path -Value $Content -Encoding UTF8
}

function Ensure-Lfs {
    Invoke-RepoGit @('lfs', 'install', '--local')
    Invoke-RepoGit @('config', 'core.longpaths', 'true')
    $attributes = @'
*.jsonl filter=lfs diff=lfs merge=lfs -text
*.sqlite filter=lfs diff=lfs merge=lfs -text
*.sqlite.bak* filter=lfs diff=lfs merge=lfs -text
*.db filter=lfs diff=lfs merge=lfs -text
'@
    Write-RepoTextFile '.gitattributes' $attributes
    $ignore = @'
.local/
__pycache__/
*.pyc
*.tmp
*.log
manifests/latest-dry-run.json
manifests/secret-scan-latest.json
'@
    Write-RepoTextFile '.gitignore' $ignore
}

function Assert-InRepoSnapshot {
    param([string]$Path)
    $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $snapshot = [System.IO.Path]::GetFullPath((Join-Path $RepoPath 'snapshot')).TrimEnd('\')
    $prefix = $snapshot + '\'
    if ($full -ne $snapshot -and -not $full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to mirror outside snapshot: $full"
    }
}

function Assert-NoReparsePath {
    param([string]$Path, [string]$ExpectedRoot)
    $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $root = [System.IO.Path]::GetFullPath($ExpectedRoot).TrimEnd('\')
    $prefix = $root + '\'
    if ($full -ne $root -and -not $full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes approved root: $full"
    }
    $cursor = $full
    while ($true) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse path is forbidden for mirror operations: $cursor"
            }
        }
        if ($cursor -eq $root) { break }
        $parent = [System.IO.Directory]::GetParent($cursor)
        if ($null -eq $parent) { throw "Cannot prove mirror path boundary: $full" }
        $cursor = $parent.FullName.TrimEnd('\')
        if ($cursor.Length -lt $root.Length) { throw "Cannot prove mirror path boundary: $full" }
    }
    return $full
}

function Invoke-RobocopyMirror {
    param([string]$Source, [string]$Destination)
    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Host "SKIP missing source: $Source"
        return
    }
    Assert-InRepoSnapshot $Destination
    [void](Assert-NoReparsePath -Path $Source -ExpectedRoot $ProfileRoot)
    [void](Assert-NoReparsePath -Path $Destination -ExpectedRoot $RepoPath)
    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    [void](Assert-NoReparsePath -Path $Destination -ExpectedRoot $RepoPath)
    $excludeDirs = @('.git', 'node_modules', 'cache', '.cache', 'tmp', '.tmp', '.sandbox', '.sandbox-bin', '.sandbox-secrets', 'packages', '.plugin-appserver', '__pycache__')
    $excludeFiles = @('auth.json', 'cap_sid', '*.sqlite-wal', '*.sqlite-shm', 'logs_*.sqlite', '*.log', '.env', '.env.*', '*cookie*', '*cookies*', '*.pyc')
    $args = @($Source, $Destination, '/MIR', '/R:2', '/W:1', '/COPY:DAT', '/DCOPY:DAT', '/FFT', '/XJ', '/XD') + $excludeDirs + @('/XF') + $excludeFiles
    & robocopy @args | Out-Host
    $code = $LASTEXITCODE
    if ($code -gt 7) {
        throw "robocopy failed from $Source to $Destination with exit code $code"
    }
}

function Copy-AllowedRootFiles {
    $codex = Join-Path $ProfileRoot '.codex'
    $dest = Join-Path $RepoPath 'snapshot\dot-codex'
    if (-not (Test-Path -LiteralPath $dest)) {
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
    }
    $files = @(
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
    foreach ($name in $files) {
        $source = Join-Path $codex $name
        if (Test-Path -LiteralPath $source) {
            Copy-Item -LiteralPath $source -Destination (Join-Path $dest $name) -Force
        }
    }
    $forbidden = @('auth.json', 'cap_sid', 'logs_*.sqlite', '*.sqlite-wal', '*.sqlite-shm', '*.log', '.env', '.env.*')
    foreach ($pattern in $forbidden) {
        Get-ChildItem -LiteralPath $dest -Force -File -Filter $pattern -ErrorAction SilentlyContinue | Remove-Item -Force
    }
}

function Copy-ProfileSnapshot {
    $codex = Join-Path $ProfileRoot '.codex'
    $agents = Join-Path $ProfileRoot '.agents'
    $opencode = Join-Path $ProfileRoot '.config\opencode'
    $pairs = @(
        @((Join-Path $codex 'sessions'), (Join-Path $RepoPath 'snapshot\dot-codex\sessions')),
        @((Join-Path $codex 'archived_sessions'), (Join-Path $RepoPath 'snapshot\dot-codex\archived_sessions')),
        @((Join-Path $codex 'skills'), (Join-Path $RepoPath 'snapshot\dot-codex\skills')),
        @((Join-Path $codex 'skills-disabled'), (Join-Path $RepoPath 'snapshot\dot-codex\skills-disabled')),
        @((Join-Path $codex 'memories'), (Join-Path $RepoPath 'snapshot\dot-codex\memories')),
        @((Join-Path $codex 'rules'), (Join-Path $RepoPath 'snapshot\dot-codex\rules')),
        @((Join-Path $codex 'automations'), (Join-Path $RepoPath 'snapshot\dot-codex\automations')),
        @((Join-Path $codex 'state'), (Join-Path $RepoPath 'snapshot\dot-codex\state')),
        @((Join-Path $codex 'tooling'), (Join-Path $RepoPath 'snapshot\dot-codex\tooling')),
        @((Join-Path $codex 'attachments'), (Join-Path $RepoPath 'snapshot\dot-codex\attachments')),
        @((Join-Path $codex 'generated_images'), (Join-Path $RepoPath 'snapshot\dot-codex\generated_images')),
        @((Join-Path $codex 'recovered_project_chats'), (Join-Path $RepoPath 'snapshot\dot-codex\recovered_project_chats')),
        @($agents, (Join-Path $RepoPath 'snapshot\dot-agents')),
        @($opencode, (Join-Path $RepoPath 'snapshot\dot-config-opencode'))
    )
    foreach ($pair in $pairs) {
        Invoke-RobocopyMirror -Source $pair[0] -Destination $pair[1]
    }
    Copy-AllowedRootFiles
}

function Run-Manifest {
    param([string]$Output, [switch]$ScanSnapshot)
    $scanFlag = if ($ScanSnapshot) { '--scan-snapshot' } else { '--scan-source' }
    & $PythonExe (Join-Path $PSScriptRoot 'backup-manifest.py') --profile-root $ProfileRoot --repo-path $RepoPath --mode $Mode --output $Output $scanFlag
    if ($LASTEXITCODE -ne 0) {
        throw "backup-manifest.py failed with exit code $LASTEXITCODE"
    }
}

$PythonExe = Resolve-Python $Python
Ensure-Repo
Ensure-Lfs

$manifestDir = Join-Path $RepoPath 'manifests'
$runDir = Join-Path $manifestDir 'runs'
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')

if ($Mode -eq 'DryRun') {
    $dryManifest = Join-Path $manifestDir 'latest-dry-run.json'
    Run-Manifest -Output $dryManifest
    Write-Host "DRY_RUN_COMPLETE"
    Write-Host "Manifest: $dryManifest"
    exit 0
}

Copy-ProfileSnapshot

$redactionReport = Join-Path $manifestDir 'redactions-latest.json'
& $PythonExe (Join-Path $PSScriptRoot 'redact-secrets.py') --root (Join-Path $RepoPath 'snapshot') --output $redactionReport
if ($LASTEXITCODE -ne 0) {
    throw "BLOCKED: secret redaction failed. Nothing will be committed or pushed. Report: $redactionReport"
}

$latestManifest = Join-Path $manifestDir 'latest.json'
Run-Manifest -Output $latestManifest -ScanSnapshot
Copy-Item -LiteralPath $latestManifest -Destination (Join-Path $runDir "$timestamp.json") -Force

$secretReport = Join-Path $manifestDir 'secret-scan-latest.json'
& $PythonExe (Join-Path $PSScriptRoot 'secret-scan.py') --root (Join-Path $RepoPath 'snapshot') --output $secretReport --max-findings 50
if ($LASTEXITCODE -ne 0) {
    throw "BLOCKED: secret scan failed. Nothing will be committed or pushed. Report: $secretReport"
}

Invoke-RepoGit @('add', '.gitattributes', '.gitignore', 'scripts', 'manifests')
Invoke-RepoGit @('add', '-f', 'snapshot')
$status = (& git -C $RepoPath status --porcelain)
if (-not $status) {
    Write-Host "PASS: no backup changes to commit."
    exit 0
}

$message = "Daily Codex X9 backup $timestamp"
Invoke-RepoGit @('commit', '-m', $message)

if ($Push) {
    Invoke-RepoGit @('push', 'origin', 'main')
    Write-Host "PASS: backup committed and pushed."
}
else {
    Write-Host "PARTIAL: backup committed locally; push was not requested."
}
