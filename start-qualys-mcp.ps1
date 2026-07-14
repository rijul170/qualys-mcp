<#
.SYNOPSIS
    Launch both Qualys MCP console instances (streamable-http).

.DESCRIPTION
    Decrypts each console's DPAPI credential blob, sets QUALYS_* env vars, and
    starts one qualys-mcp process per console on its own port:
        qualys-consulting -> 127.0.0.1:8781
        qualys-cloud      -> 127.0.0.1:8782
    Mirrors the Falcon MCP launcher (log rotation, skip-if-listening).

    Destructive tools stay hidden unless you pass -EnableDestructive for a
    console (maps to QUALYS_ENABLE_DESTRUCTIVE=true).
#>
param(
    [string[]]$EnableDestructive = @()   # e.g. -EnableDestructive cloud
)

$ErrorActionPreference = 'Stop'

# Normalize: `powershell.exe -File ... -EnableDestructive consulting,cloud`
# passes "consulting,cloud" as a SINGLE element, so a plain -contains check
# fails. Split any comma-joined elements so it works whether the value arrives
# split (interactive &) or joined (-File / scheduled task).
$EnableDestructive = @($EnableDestructive | ForEach-Object { $_ -split ',' } | Where-Object { $_ -ne '' })

$root       = $PSScriptRoot
$exe        = Join-Path $root '.venv\Scripts\qualys-mcp.exe'
$logDir     = Join-Path $root 'logs'
$secretsDir = Join-Path $root '.secrets'

$logMaxBytes   = 50MB
$logRotateKeep = 7

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
if (-not (Test-Path $exe))    { throw "qualys-mcp.exe not found at $exe. Run: .\.venv\Scripts\pip install -e ." }

# console -> port map
$consoles = @(
    @{ Name = 'consulting'; Port = 8781 },
    @{ Name = 'cloud';      Port = 8782 }
)

function Test-Listening($port) {
    try { (Test-NetConnection -ComputerName 127.0.0.1 -Port $port -WarningAction SilentlyContinue).TcpTestSucceeded } catch { $false }
}

function Invoke-LogRotation {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try { $item = Get-Item -LiteralPath $Path -ErrorAction Stop } catch { return }
    if ($item.Length -le $logMaxBytes) { return }
    $stamp   = Get-Date -Format 'yyyy-MM-dd-HHmm'
    $rotated = "$Path.$stamp"
    if (Test-Path -LiteralPath $rotated) { $n = 1; while (Test-Path -LiteralPath "$rotated.$n") { $n++ }; $rotated = "$rotated.$n" }
    try { Move-Item -LiteralPath $Path -Destination $rotated -ErrorAction Stop } catch { return }
    $baseName = [System.IO.Path]::GetFileName($Path)
    $dir      = [System.IO.Path]::GetDirectoryName($Path)
    Get-ChildItem -LiteralPath $dir -Filter "$baseName.*" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne $baseName } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -Skip $logRotateKeep |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
}

function Get-QualysCreds {
    param([string]$Console)
    $path = Join-Path $secretsDir "qualys-$Console.dat"
    if (-not (Test-Path $path)) { throw "Missing encrypted creds: $path. Run encrypt-qualys-creds.ps1 -Console $Console first." }
    $enc = (Get-Content $path -Raw).Trim()
    try { $ss = ConvertTo-SecureString $enc } catch { throw "Failed to decrypt $path (DPAPI is user-scoped; run as the user who encrypted it). $_" }
    [System.Net.NetworkCredential]::new('', $ss).Password | ConvertFrom-Json
}

function Start-QualysConsole {
    param([string]$Console, [int]$Port)
    $name = "qualys-$Console"
    if (Test-Listening $Port) { Write-Host "$name already listening on $Port - skipping."; return }

    $c = Get-QualysCreds -Console $Console
    $env:QUALYS_USERNAME       = $c.username
    $env:QUALYS_PASSWORD       = $c.password
    $env:QUALYS_PLATFORM       = $c.platform
    if ($c.api_url)     { $env:QUALYS_API_URL     = $c.api_url }
    if ($c.gateway_url) { $env:QUALYS_GATEWAY_URL = $c.gateway_url }
    $env:QUALYS_CONSOLE_LABEL  = $Console
    $env:QUALYS_ENABLE_DESTRUCTIVE = if ($EnableDestructive -contains $Console) { 'true' } else { 'false' }

    $logFile = Join-Path $logDir "$name.log"
    Invoke-LogRotation -Path $logFile
    Invoke-LogRotation -Path "$logFile.err"

    Start-Process -FilePath $exe `
        -ArgumentList @('--transport', 'streamable-http', '--host', '127.0.0.1', '--port', $Port, '--console-label', $Console) `
        -WindowStyle Hidden `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError "$logFile.err"

    Remove-Item Env:\QUALYS_USERNAME, Env:\QUALYS_PASSWORD, Env:\QUALYS_PLATFORM, `
                Env:\QUALYS_API_URL, Env:\QUALYS_GATEWAY_URL, Env:\QUALYS_CONSOLE_LABEL, `
                Env:\QUALYS_ENABLE_DESTRUCTIVE -ErrorAction SilentlyContinue
    $dest = if ($EnableDestructive -contains $Console) { ' [DESTRUCTIVE ENABLED]' } else { '' }
    Write-Host "$name started on 127.0.0.1:$Port$dest (log: $logFile)"
}

foreach ($cfg in $consoles) { Start-QualysConsole -Console $cfg.Name -Port $cfg.Port }
