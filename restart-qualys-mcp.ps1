#requires -RunAsAdministrator
<#
.SYNOPSIS
    Restart both Qualys MCP instances via the QualysMCP watchdog task.

.DESCRIPTION
    The instances run elevated under the QualysMCP scheduled task, so a
    non-admin shell cannot bounce them. This (elevated) helper stops both
    instances and kicks the task, which relaunches them with the task's
    configured destructive setting (now that start/supervise correctly parse
    the -EnableDestructive argument). If no task exists, starts them directly
    with destructive on both.

    Run ELEVATED:  & 'E:\Qualys MCP\restart-qualys-mcp.ps1'
#>
$ErrorActionPreference = 'SilentlyContinue'
$root = $PSScriptRoot

Write-Host "Stopping running Qualys MCP instances..." -ForegroundColor Cyan
foreach ($p in 8781, 8782) {
    Get-NetTCPConnection -LocalPort $p -State Listen |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { Stop-Process -Id $_ -Force }
}
Get-CimInstance Win32_Process -Filter "Name = 'qualys-mcp.exe'" |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Seconds 3

if (Get-ScheduledTask -TaskName 'QualysMCP' -ErrorAction SilentlyContinue) {
    Write-Host "Kicking QualysMCP watchdog task (uses its configured destructive setting)..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName 'QualysMCP'
} else {
    Write-Host "No QualysMCP task found; starting directly with destructive on both..." -ForegroundColor Yellow
    & (Join-Path $root 'start-qualys-mcp.ps1') -EnableDestructive consulting,cloud
}

Start-Sleep -Seconds 10
foreach ($p in 8781, 8782) {
    $up = (Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded
    Write-Host ("  port {0} listening: {1}" -f $p, $up)
}
Write-Host "Done. Verify tool parity from the project with: python scripts\audit_tools.py" -ForegroundColor Cyan
