<#
.SYNOPSIS
    Look up a host by name on one console and pull its vulnerabilities (read-only).

.EXAMPLE
    .\query-host.ps1 -Console cloud -Name WEBSERVER-01
#>
param(
    [Parameter(Mandatory = $true)][string]$Console,
    [Parameter(Mandatory = $true)][string]$Name
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$enc = (Get-Content (Join-Path $root ".secrets\qualys-$Console.dat") -Raw).Trim()
$c = [System.Net.NetworkCredential]::new('', (ConvertTo-SecureString $enc)).Password | ConvertFrom-Json
$env:QUALYS_USERNAME = $c.username; $env:QUALYS_PASSWORD = $c.password; $env:QUALYS_PLATFORM = $c.platform
try {
    & (Join-Path $root '.venv\Scripts\python.exe') (Join-Path $root 'scripts\find_host.py') --console $Console --name $Name
}
finally {
    $env:QUALYS_USERNAME = ''; $env:QUALYS_PASSWORD = ''; $env:QUALYS_PLATFORM = ''
}
