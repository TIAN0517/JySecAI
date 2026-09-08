param([switch]$Install)
$ErrorActionPreference = 'Stop'
$ListenAddress = '52.128.238.210'
$Distro = 'kali-linux'

function Get-WslIp {
  $raw = (wsl.exe -d $Distro -- hostname -I).Trim()
  if ([string]::IsNullOrWhiteSpace($raw)) { throw 'Kali WSL IP unavailable' }
  return ($raw -split '\s+')[0]
}

function Sync-PortProxy {
  $ip = Get-WslIp
  foreach ($pair in @(@(80,18080), @(443,18443))) {
    netsh interface portproxy delete v4tov4 listenaddress=$ListenAddress listenport=$pair[0] | Out-Null
    netsh interface portproxy add v4tov4 listenaddress=$ListenAddress listenport=$pair[0] connectaddress=$ip connectport=$pair[1] | Out-Null
  }
}

if ($Install) {
  if (-not (Get-NetFirewallRule -DisplayName 'JySecAI HTTP edge' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName 'JySecAI HTTP edge' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress $ListenAddress -LocalPort 80 -Profile Any | Out-Null
  }
  if (-not (Get-NetFirewallRule -DisplayName 'JySecAI HTTPS edge' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName 'JySecAI HTTPS edge' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress $ListenAddress -LocalPort 443 -Profile Any | Out-Null
  }
  $task = 'JySecAI WSL Edge Portproxy'
  $action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -RestartCount 999 -RestartInterval (New-TimeSpan -Seconds 10)
  Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null
  Start-ScheduledTask -TaskName $task
  exit 0
}

while ($true) {
  try { Sync-PortProxy } catch { }
  Start-Sleep -Seconds 30
}
