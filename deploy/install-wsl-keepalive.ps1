[CmdletBinding()]
param(
    [string]$Distribution = "kali-linux",
    [string]$TaskName = "JySecAI Kali WSL Autostart"
)

$ErrorActionPreference = "Stop"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principalCheck = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principalCheck.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run this installer from an elevated PowerShell session."
}

$wsl = (Get-Command wsl.exe -ErrorAction Stop).Source
$action = New-ScheduledTaskAction `
    -Execute $wsl `
    -Argument "-d $Distribution -u root --exec /bin/sleep infinity"
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity.Name
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal `
    -UserId $identity.Name `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description "Keeps Kali WSL alive so JySecAI systemd services remain available; Task Scheduler restarts it after failure." `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 2
$task = Get-ScheduledTask -TaskName $TaskName
if ($task.State -ne "Running") {
    throw "The WSL keepalive task did not enter the Running state (state: $($task.State))."
}

Write-Output "WSL keepalive task is running for $Distribution."
