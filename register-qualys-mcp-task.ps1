#requires -RunAsAdministrator
<#
.SYNOPSIS
    Install the QualysMCP watchdog scheduled task (mirrors the Falcon MCP model).

.DESCRIPTION
    Keeps both Qualys MCP instances alive — 127.0.0.1:8781 (consulting) and
    :8782 (cloud) — by running supervise-qualys-mcp.ps1 (idempotent
    check-and-restart) at startup (password mode only), at logon, and every 5 min.

    Password handling:
      * Enter your Windows password  -> LogonType=Password (LSA); survives reboots
        even when logged out. If the password is rejected, the script AUTOMATICALLY
        falls back to an Interactive task (no password) so you always end up with a
        working watchdog.
      * Press Enter to skip           -> Interactive task; runs while logged in.
    Password is read with -AsSecureString: never echoed, logged, or written to disk.

    Uses -Force (replace-in-place) so a failure can never leave you with NO task.
    The Startup-folder launcher is kept as an independent fallback. Run ELEVATED.

.EXAMPLE
    & 'E:\Qualys MCP\register-qualys-mcp-task.ps1' -EnableDestructive consulting,cloud
#>
param(
    [string]$TaskName = 'QualysMCP',
    [string[]]$EnableDestructive = @()
)

$ErrorActionPreference = 'Stop'
$root       = $PSScriptRoot
$supervisor = Join-Path $root 'supervise-qualys-mcp.ps1'
if (-not (Test-Path $supervisor)) { throw "Supervisor not found: $supervisor" }
$user = "$env:USERDOMAIN\$env:USERNAME"

$destArg = ''
if ($EnableDestructive.Count -gt 0) {
    $destArg = " -EnableDestructive $($EnableDestructive -join ',')"
}

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$supervisor`"$destArg"

$triggerLogon  = New-ScheduledTaskTrigger -AtLogOn
$triggerRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Write-Host "Registering '$TaskName' to keep Qualys MCP (:8781, :8782) alive." -ForegroundColor Cyan
Write-Host "Enter the Windows password for $user for unattended reboot survival," -ForegroundColor Cyan
Write-Host "or press Enter to skip (task then runs only while you are logged in)." -ForegroundColor DarkGray
$secure = Read-Host -Prompt "Password for $user (Enter to skip)" -AsSecureString
$plain  = [System.Net.NetworkCredential]::new('', $secure).Password

function Register-Interactive {
    $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
    Register-ScheduledTask -TaskName $TaskName -Action $action `
        -Trigger @($triggerLogon, $triggerRepeat) -Principal $principal -Settings $settings -Force `
        -Description 'Qualys MCP watchdog (:8781 consulting, :8782 cloud). Runs while logged in; checks every 5 min.' -ErrorAction Stop | Out-Null
}

$registered = $false
try {
    if ([string]::IsNullOrEmpty($plain)) {
        Register-Interactive
        Write-Host "Registered '$TaskName' [Interactive - runs while logged in]." -ForegroundColor Green
        $registered = $true
    } else {
        $triggerStartup = New-ScheduledTaskTrigger -AtStartup
        try {
            Register-ScheduledTask -TaskName $TaskName -Action $action `
                -Trigger @($triggerStartup, $triggerLogon, $triggerRepeat) `
                -User $user -Password $plain -RunLevel Highest -Settings $settings -Force `
                -Description 'Qualys MCP watchdog (:8781 consulting, :8782 cloud). Survives reboot unattended; checks every 5 min.' -ErrorAction Stop | Out-Null
            Write-Host "Registered '$TaskName' [Password/LSA - survives logged-out reboot]." -ForegroundColor Green
            $registered = $true
        } catch {
            Write-Host "Password rejected ($($_.Exception.Message))." -ForegroundColor Yellow
            Write-Host "Falling back to Interactive (no password; runs while logged in)..." -ForegroundColor Yellow
            Register-Interactive
            Write-Host "Registered '$TaskName' [Interactive fallback]." -ForegroundColor Green
            $registered = $true
        }
    }
} catch {
    Write-Host "ERROR: task registration failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "No change made. The Startup-folder launcher still restarts the servers at logon." -ForegroundColor Yellow
} finally {
    $plain = $null
    [System.GC]::Collect()
}

if (-not $registered) { return }

# Registration succeeded: stop running instances (elevated context can kill them)
# so the kick relaunches both with the new destructive setting.
Write-Host "Applying setting: stopping running instances..." -ForegroundColor DarkGray
foreach ($p in 8781, 8782) {
    try {
        Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique |
            ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
    } catch {}
}
Get-CimInstance Win32_Process -Filter "Name = 'qualys-mcp.exe'" -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 3

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 6
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State | Format-Table -AutoSize
foreach ($p in 8781, 8782) {
    $up = try { (Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded } catch { $false }
    Write-Host ("  port {0} listening: {1}" -f $p, $up)
}
Write-Host "Done. (A Startup-folder launcher is also kept as an independent fallback.)" -ForegroundColor Cyan
