param(
    [string] $RepoRoot = (Get-Location).Path,
    [Parameter(Mandatory = $true)]
    [string] $Packet,
    [ValidateSet('opencode-go/glm-5.2', 'opencode-go/kimi-k2.7-code', 'opencode/deepseek-v4-flash-free', 'opencode/mimo-v2.5-free')]
    [string] $Model = 'opencode-go/glm-5.2',
    [string] $Output = '',
    [string] $Prompt = 'Read the attached packet. Return concise markdown only. PLAN/REVIEW ONLY. Do not run commands. Do not edit files.'
)

$ErrorActionPreference = 'Stop'

if ($Model -like 'openrouter/*') {
    throw 'OpenRouter models are not allowed for Devad sidecars.'
}

$repo = (Resolve-Path -LiteralPath $RepoRoot).Path
$packetPath = (Resolve-Path -LiteralPath $Packet).Path

$args = @(
    'run',
    '--model', $Model,
    '--dir', $repo,
    '--file', $packetPath,
    '--title', "Devad sidecar $Model",
    $Prompt
)

$result = & opencode @args 2>&1
$exitCode = $LASTEXITCODE
$text = ($result | Out-String).TrimEnd()

if ($Output) {
    $outputPath = if ([System.IO.Path]::IsPathRooted($Output)) {
        $Output
    } else {
        Join-Path (Get-Location).Path $Output
    }
    $parent = Split-Path -Parent $outputPath
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $utf8NoBom = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($outputPath, $text, $utf8NoBom)
}

if ($exitCode -ne 0) {
    throw "opencode run failed with exit code $exitCode`n$text"
}

$text
