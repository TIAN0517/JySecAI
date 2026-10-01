$root = 'C:\Users\Administrator\Desktop\JySecAI'
$out = Join-Path $root 'logs\boot.out.log'
$err = Join-Path $root 'logs\boot.err.log'
$proc = Start-Process -FilePath (Join-Path $root 'jysecai.exe') -WorkingDirectory $root -ArgumentList '--config','config.yaml' -Wait -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
Write-Output ("EXIT=" + $proc.ExitCode)
