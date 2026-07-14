<#
.SYNOPSIS
    Run the live READ-ONLY audit against one or both consoles.

.DESCRIPTION
    Decrypts each console's DPAPI credential blob, sets QUALYS_* env vars for the
    child Python process only, and runs scripts/live_readonly_audit.py. The audit
    calls only read tools (connectivity + a curated read per API family) and
    writes reports/<console>-readonly-audit.{json,md}. Credentials are scrubbed
    from the environment immediately after each run.

    Prereq: .\encrypt-qualys-creds.ps1 -Console <name> -Platform US3  (run first).

    Examples:
        .\run-live-audit.ps1                       # both consoles
        .\run-live-audit.ps1 -Consoles consulting  # just one
#>
param(
    [string[]]$Consoles = @('consulting', 'cloud')
)

$ErrorActionPreference = 'Stop'
$root       = $PSScriptRoot
$py         = Join-Path $root '.venv\Scripts\python.exe'
$audit      = Join-Path $root 'scripts\live_readonly_audit.py'
$secretsDir = Join-Path $root '.secrets'
$reportsDir = Join-Path $root 'reports'
if (-not (Test-Path $reportsDir)) { New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null }

function Get-QualysCreds {
    param([string]$Console)
    $path = Join-Path $secretsDir "qualys-$Console.dat"
    if (-not (Test-Path $path)) { throw "Missing encrypted creds: $path. Run encrypt-qualys-creds.ps1 -Console $Console -Platform US3 first." }
    $enc = (Get-Content $path -Raw).Trim()
    try { $ss = ConvertTo-SecureString $enc } catch { throw "Failed to decrypt $path (DPAPI is user-scoped; run as the user who encrypted it). $_" }
    [System.Net.NetworkCredential]::new('', $ss).Password | ConvertFrom-Json
}

foreach ($console in $Consoles) {
    Write-Host "=== Live read-only audit: $console ===" -ForegroundColor Cyan
    $c = Get-QualysCreds -Console $console
    $env:QUALYS_USERNAME      = $c.username
    $env:QUALYS_PASSWORD      = $c.password
    $env:QUALYS_PLATFORM      = $c.platform
    if ($c.api_url)     { $env:QUALYS_API_URL     = $c.api_url }
    if ($c.gateway_url) { $env:QUALYS_GATEWAY_URL = $c.gateway_url }
    $env:QUALYS_CONSOLE_LABEL = $console
    try {
        & $py $audit --console $console --out (Join-Path $reportsDir "$console-readonly-audit")
    } finally {
        Remove-Item Env:\QUALYS_USERNAME, Env:\QUALYS_PASSWORD, Env:\QUALYS_PLATFORM, `
                    Env:\QUALYS_API_URL, Env:\QUALYS_GATEWAY_URL, Env:\QUALYS_CONSOLE_LABEL `
                    -ErrorAction SilentlyContinue
    }
}
Write-Host "Reports written to $reportsDir" -ForegroundColor Green
