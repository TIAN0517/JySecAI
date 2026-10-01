$ErrorActionPreference = "SilentlyContinue"
$workdir = "C:\Users\Administrator\Desktop\JySecAI"

# kill any old instance first
Get-Process | Where-Object { $_.ProcessName -match '^(jysecai|server|__go_build)' } | Stop-Process -Force
Start-Sleep -Seconds 1

# build first so the long-running process is a stable exe (go run would leave a temp child)
go build -o tmp\jysecai-server.exe ./cmd/server
if (-not (Test-Path "$workdir\tmp\jysecai-server.exe")) { Write-Output "BUILD-FAIL"; exit 1 }
Write-Output "build ok"

$log = "$workdir\tmp\server_run.log"
$err  = "$workdir\tmp\server_run.err.log"
$proc = Start-Process -FilePath "$workdir\tmp\jysecai-server.exe" `
    -ArgumentList "--config","config.yaml" `
    -WorkingDirectory $workdir `
    -RedirectStandardOutput $log -RedirectStandardError $err `
    -PassThru -WindowStyle Hidden
Write-Output ("server pid=" + $proc.Id)

# wait for HTTPS 6688
$listening = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if ($proc.HasExited) { Write-Output ("server EXITED code=" + $proc.ExitCode); break }
    $t = New-Object Net.Sockets.TcpClient
    if ($t.ConnectAsync("127.0.0.1", 6688).Wait(500) -and $t.Connected) { $listening = $true; $t.Close(); break }
    $t.Close()
}
Write-Output ("PORT-6688: " + $(if ($listening) { "LISTENING" } else { "NOT-LISTENING" }))

# HTTPS probe (self-signed, skip cert verify) via curl.exe
if ($listening) {
    & "C:\Windows\System32\curl.exe" -k -s -o NUL -w "HTTPS / -> %{http_code}`n" https://127.0.0.1:6688/ --max-time 10
}

# show boot log
Write-Output "`n===== server log (first 40 lines) ====="
if (Test-Path $log) { Get-Content $log | Select-Object -First 40 }
if (Test-Path $err) {
    $e = Get-Content $err | Select-Object -First 20
    if ($e) { Write-Output "`n===== stderr ====="; $e }
}
