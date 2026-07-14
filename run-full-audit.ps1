<#
.SYNOPSIS
    Comprehensive READ-ONLY audit of one or both consoles (every read-tier tool).

.DESCRIPTION
    Decrypts each console's DPAPI blob, sets QUALYS_* env for the child process
    only, and runs scripts/full_readonly_audit.py. Destructive is forced OFF and
    only read tools are invoked. Credential values are scrubbed from the env
    immediately after each run. Reports -> reports/<console>-full-readonly-audit.{json,md}

    Examples:
        .\run-full-audit.ps1
        .\run-full-audit.ps1 -Consoles cloud
#>
param(
    [string[]]$Consoles = @('consulting', 'cloud')
)

$ErrorActionPreference = 'Stop'
$root       = $PSScriptRoot
$py         = Join-Path $root '.venv\Scripts\python.exe'
$audit      = Join-Path $root 'scripts\full_readonly_audit.py'
$secretsDir = Join-Path $root '.secrets'
$reportsDir = Join-Path $root 'reports'
if (-not (Test-Path $reportsDir)) { New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null }

function Get-QualysCreds {
    param([string]$Console)
    $path = Join-Path $secretsDir "qualys-$Console.dat"
    if (-not (Test-Path $path)) { throw "Missing encrypted creds: $path" }
    $enc = (Get-Content $path -Raw).Trim()
    try { $ss = ConvertTo-SecureString $enc } catch { throw "Failed to decrypt $path (DPAPI user-scoped). $_" }
    [System.Net.NetworkCredential]::new('', $ss).Password | ConvertFrom-Json
}

foreach ($console in $Consoles) {
    Write-Host "=== Comprehensive read-only audit: $console ===" -ForegroundColor Cyan
    $c = Get-QualysCreds -Console $console
    $env:QUALYS_USERNAME          = $c.username
    $env:QUALYS_PASSWORD          = $c.password
    $env:QUALYS_PLATFORM          = $c.platform
    if ($c.api_url)     { $env:QUALYS_API_URL     = $c.api_url }
    if ($c.gateway_url) { $env:QUALYS_GATEWAY_URL = $c.gateway_url }
    $env:QUALYS_CONSOLE_LABEL     = $console
    $env:QUALYS_ENABLE_DESTRUCTIVE = 'false'
    $env:QUALYS_TIMEOUT           = '60'
    try {
        & $py $audit --console $console --out (Join-Path $reportsDir "$console-full-readonly-audit")
    } finally {
        # Scrub secret values from the environment (assignment, no Remove-Item).
        $env:QUALYS_USERNAME = ''; $env:QUALYS_PASSWORD = ''
        $env:QUALYS_PLATFORM = ''; $env:QUALYS_API_URL = ''; $env:QUALYS_GATEWAY_URL = ''
        $env:QUALYS_CONSOLE_LABEL = ''
    }
}
Write-Host "Reports written to $reportsDir" -ForegroundColor Green
