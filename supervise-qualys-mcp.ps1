<#
.SYNOPSIS
    Watchdog: restart any Qualys MCP console instance that has stopped listening.

.DESCRIPTION
    Intended to run on a short schedule (e.g. every 5 minutes) via Task
    Scheduler. Checks each console port; if a port is not listening, re-runs
    start-qualys-mcp.ps1 (which is a no-op for consoles already up).
#>
param(
    [string[]]$EnableDestructive = @()
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

# Normalize comma-joined values from `-File` invocation (scheduled task) so the
# flag propagates correctly to start-qualys-mcp.ps1.
$EnableDestructive = @($EnableDestructive | ForEach-Object { $_ -split ',' } | Where-Object { $_ -ne '' })

$ports = @(8781, 8782)
$needStart = $false
foreach ($p in $ports) {
    $up = try { (Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded } catch { $false }
    if (-not $up) { Write-Host "$(Get-Date -Format s) port $p down"; $needStart = $true }
}

if ($needStart) {
    & (Join-Path $root 'start-qualys-mcp.ps1') -EnableDestructive $EnableDestructive
} else {
    Write-Host "$(Get-Date -Format s) all Qualys MCP consoles healthy"
}
