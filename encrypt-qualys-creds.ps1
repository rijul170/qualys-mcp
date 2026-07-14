<#
.SYNOPSIS
    Encrypt Qualys API credentials for one console to a DPAPI-protected file.

.DESCRIPTION
    Prompts for the API username/password + platform and writes an encrypted
    JSON blob to .secrets\qualys-<console>.dat. DPAPI is user-scoped: the blob
    can only be decrypted by the same Windows user on the same machine, so the
    credentials never exist in plaintext on disk and never leave this box.

    Run once per console, e.g.:
        .\encrypt-qualys-creds.ps1 -Console consulting -Platform US2
        .\encrypt-qualys-creds.ps1 -Console cloud      -Platform US2

.NOTES
    The start script (start-qualys-mcp.ps1) decrypts these at launch and sets
    them as environment variables for the child process only.
#>
param(
    [Parameter(Mandatory = $true)][string]$Console,
    [Parameter(Mandatory = $true)][string]$Platform,
    [string]$ApiUrl,
    [string]$GatewayUrl
)

$ErrorActionPreference = 'Stop'
$secretsDir = Join-Path $PSScriptRoot '.secrets'
if (-not (Test-Path $secretsDir)) { New-Item -ItemType Directory -Path $secretsDir -Force | Out-Null }

$username = Read-Host "Qualys API username for '$Console'"
$secure   = Read-Host "Qualys API password for '$Console'" -AsSecureString
$plain    = [System.Net.NetworkCredential]::new('', $secure).Password

$payload = [ordered]@{
    username    = $username
    password    = $plain
    platform    = $Platform
    api_url     = $ApiUrl
    gateway_url = $GatewayUrl
    console     = $Console
} | ConvertTo-Json -Compress

# Encrypt the JSON string with DPAPI (user + machine scoped).
$encrypted = ConvertTo-SecureString $payload -AsPlainText -Force | ConvertFrom-SecureString

$outPath = Join-Path $secretsDir "qualys-$Console.dat"
Set-Content -LiteralPath $outPath -Value $encrypted -Encoding ASCII -NoNewline

# Scrub the plaintext copy from memory.
$plain = $null; $payload = $null
[System.GC]::Collect()

Write-Host "Wrote encrypted credentials for console '$Console' -> $outPath"
Write-Host "Platform: $Platform  (decryptable only by $env:USERNAME on $env:COMPUTERNAME)"
