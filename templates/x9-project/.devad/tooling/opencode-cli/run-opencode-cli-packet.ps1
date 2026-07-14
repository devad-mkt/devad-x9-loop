param(
    [string] $RepoRoot = '.',
    [Parameter(Mandatory = $true)]
    [string] $Packet,
    [ValidateSet('opencode-go/glm-5.2', 'opencode-go/kimi-k2.7-code')]
    [string] $Model = 'opencode-go/glm-5.2',
    [string] $Output = '',
    [ValidateRange(1, 600)]
    [int] $Timeout = 120
)

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path -LiteralPath $RepoRoot).Path
$packetPath = (Resolve-Path -LiteralPath $Packet).Path
$doctor = Join-Path $HOME '.codex\skills\devad-x9-loop\scripts\opencode_doctor.py'
if (-not (Test-Path -LiteralPath $doctor -PathType Leaf)) {
    throw "Missing installed X9 sidecar doctor: $doctor"
}

if (-not $Output) {
    $modelSlug = ($Model -split '/')[-1]
    $Output = Join-Path (Split-Path -Parent $packetPath) (
        '{0}-{1}.md' -f [IO.Path]::GetFileNameWithoutExtension($packetPath), $modelSlug
    )
} elseif (-not [IO.Path]::IsPathRooted($Output)) {
    $Output = Join-Path (Split-Path -Parent $packetPath) $Output
}

$arguments = @(
    $doctor,
    'request',
    '--repo', $repo,
    '--packet', $packetPath,
    '--model', $Model,
    '--output', $Output,
    '--timeout', [string]$Timeout
)
$result = & python @arguments 2>&1
$exitCode = $LASTEXITCODE
$text = ($result | Out-String).TrimEnd()
if ($exitCode -ne 0) {
    throw ("X9 sidecar request stopped with exit code {0}{1}{2}" -f $exitCode, [Environment]::NewLine, $text)
}
$text