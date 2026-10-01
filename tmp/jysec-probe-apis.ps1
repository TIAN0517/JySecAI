$ErrorActionPreference = 'Continue'
function Probe($name, $url) {
  try {
    $r = & curl.exe -k -sS -o NUL -w '%{http_code}' --connect-timeout 4 --max-time 12 $url
    Write-Output ("{0}={1}" -f $name, $r)
  } catch {
    Write-Output ("{0}=ERR" -f $name)
  }
}
Probe 'home' 'https://127.0.0.1:6688/'
Probe 'config' 'https://127.0.0.1:6688/api/config'
Probe 'conversations' 'https://127.0.0.1:6688/api/conversations?limit=5'
Probe 'projects' 'https://127.0.0.1:6688/api/projects'
Probe 'hitl' 'https://127.0.0.1:6688/api/hitl/pending?page=1&pageSize=5'
Probe 'tasks' 'https://127.0.0.1:6688/api/agent-loop/tasks'
Probe 'workflows' 'https://127.0.0.1:6688/api/workflows'
Probe 'skills' 'https://127.0.0.1:6688/api/skills'
Probe 'vulns' 'https://127.0.0.1:6688/api/vulnerabilities'
Probe 'assets' 'https://127.0.0.1:6688/api/assets'
Probe 'recon' 'https://127.0.0.1:6688/api/recon/runs'
Probe 'mcp' 'https://127.0.0.1:6688/api/mcp/tools'
Probe 'c2' 'https://127.0.0.1:6688/api/c2/listeners'
Probe 'gov' 'http://127.0.0.1:8787/governance/'
Probe 'govroot' 'http://127.0.0.1:8787/'
