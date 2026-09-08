#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

HEX_ROOT=/opt/jysecai/hexstrike-ai
KALI_ROOT=/opt/jysecai/MCP-Kali-Server

test -x "$HEX_ROOT/hexstrike-env/bin/python"
test -x "$KALI_ROOT/mcp-env/bin/python"

# The upstream MCP bridge uses the v1 FastMCP import path. MCP SDK 2.x removed it.
if ! "$KALI_ROOT/mcp-env/bin/python" -c 'from mcp.server.fastmcp import FastMCP' 2>/dev/null; then
  "$KALI_ROOT/mcp-env/bin/pip" install --disable-pip-version-check --no-input 'mcp>=1,<2'
fi

# Upstream /health shells out to `which` once per advertised tool. Because only
# successful checks are cached, every missing optional tool is executed again by
# the one-minute watchdog and is incorrectly included in command-failure
# telemetry. Use Python's in-process lookup instead and map product/package names
# to the executables they actually install.
HEX_SERVER="$HEX_ROOT/hexstrike_server.py"
if grep -q 'result = execute_command(f"which {tool}", use_cache=True)' "$HEX_SERVER"; then
  backup="$HEX_SERVER.bak-jysec-healthcheck"
  if [[ ! -e $backup ]]; then
    cp -p "$HEX_SERVER" "$backup"
  fi

  sed -i \
    '/^    tools_status = {}$/,/^    all_essential_tools_available = all(tools_status\[tool\] for tool in essential_tools)$/c\
    # Health checks must not execute commands or affect execution telemetry.\
    # Some inventory labels are package/product names rather than executables.\
    tool_commands = {\
        "metasploit": "msfconsole",\
        "exploit-db": "searchsploit",\
    }\
    tools_status = {\
        tool: shutil.which(tool_commands.get(tool, tool)) is not None\
        for tool in dict.fromkeys(all_tools)\
    }\
\
    all_essential_tools_available = all(tools_status[tool] for tool in essential_tools)' \
    "$HEX_SERVER"
fi

# psutil's one-second blocking sample made every watchdog request take at least
# one second. A health endpoint only needs the latest non-blocking CPU sample.
sed -i 's/psutil\.cpu_percent(interval=1)/psutil.cpu_percent(interval=None)/g' "$HEX_SERVER"

# Both upstream Flask entrypoints default to all interfaces without authentication.
# Keep the APIs local to the WSL host while JySecAI talks to them over localhost.
for source_file in "$HEX_ROOT/hexstrike_server.py" "$KALI_ROOT/kali-server/kali_server.py"; do
  if ! grep -q 'os.environ.get("API_HOST"' "$source_file"; then
    sed -i 's/app.run(host="0.0.0.0",/app.run(host=os.environ.get("API_HOST", "127.0.0.1"),/' "$source_file"
  fi
done

install -d -o jysec -g jysec -m 0750 "$KALI_ROOT/tmp"

cat >/usr/local/sbin/jysec-wait-for-health <<'EOF'
#!/usr/bin/env bash
set -u
url=$1
attempts=${2:-60}
for ((attempt = 1; attempt <= attempts; attempt += 1)); do
  if curl --fail --silent --show-error --max-time 5 "$url" >/dev/null; then
    exit 0
  fi
  sleep 1
done
echo "Health endpoint did not become ready: $url" >&2
exit 1
EOF
chmod 0755 /usr/local/sbin/jysec-wait-for-health

cat >/etc/systemd/system/jysec-hexstrike.service <<EOF
[Unit]
Description=JySecAI HexStrike API
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0
ConditionFileIsExecutable=$HEX_ROOT/hexstrike-env/bin/python

[Service]
Type=simple
User=jysec
Group=jysec
WorkingDirectory=$HEX_ROOT
Environment=HOME=/opt/jysecai
Environment=API_HOST=127.0.0.1
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games
ExecStart=$HEX_ROOT/hexstrike-env/bin/gunicorn --bind 127.0.0.1:8888 --workers 1 --threads 8 --timeout 0 --access-logfile - --error-logfile - hexstrike_server:app
ExecStartPost=/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:8888/health 90
Restart=always
RestartSec=5
TimeoutStartSec=180
TimeoutStopSec=30
KillMode=mixed
UMask=0077
LimitNOFILE=65536
LimitNPROC=4096
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/jysec-kali-api.service <<EOF
[Unit]
Description=JySecAI MCP Kali Tools API
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0
ConditionFileIsExecutable=$KALI_ROOT/mcp-env/bin/python

[Service]
Type=simple
User=jysec
Group=jysec
WorkingDirectory=$KALI_ROOT/tmp
Environment=HOME=/opt/jysecai
Environment=API_HOST=127.0.0.1
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games
ExecStart=$KALI_ROOT/mcp-env/bin/gunicorn --bind 127.0.0.1:5000 --workers 1 --threads 8 --timeout 0 --access-logfile - --error-logfile - --pythonpath $KALI_ROOT/kali-server 'kali_server:create_app()'
ExecStartPost=/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:5000/health 60
Restart=always
RestartSec=5
TimeoutStartSec=120
TimeoutStopSec=30
KillMode=mixed
UMask=0077
LimitNOFILE=65536
LimitNPROC=4096
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

cat >/usr/local/sbin/jysec-healthcheck <<'EOF'
#!/usr/bin/env bash
set -u

check_service() {
  local unit=$1
  local url=$2
  if ! curl --fail --silent --show-error --max-time 20 "$url" >/dev/null; then
    logger --tag jysec-healthcheck "$unit failed $url; restarting"
    systemctl restart "$unit"
    return 1
  fi
}

check_unit() {
  local unit=$1
  if systemctl is-enabled --quiet "$unit" 2>/dev/null && ! systemctl is-active --quiet "$unit"; then
    logger --tag jysec-healthcheck "$unit is not active; restarting"
    systemctl restart "$unit"
    return 1
  fi
}

check_tcp() {
  local unit=$1
  local host=$2
  local port=$3
  if systemctl is-enabled --quiet "$unit" 2>/dev/null && ! timeout 3 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
    logger --tag jysec-healthcheck "$unit TCP $host:$port failed; restarting"
    systemctl restart "$unit"
    return 1
  fi
}

result=0
check_service jysec-hexstrike.service http://127.0.0.1:8888/health || result=1
check_service jysec-kali-api.service http://127.0.0.1:5000/health || result=1
if systemctl is-enabled --quiet jysec-scanner-adapter.service 2>/dev/null; then
  check_service jysec-scanner-adapter.service http://127.0.0.1:8790/healthz || result=1
fi
for service_url in \
  "jysec-core.service http://127.0.0.1:8080/" \
  "jysec-control-plane.service http://127.0.0.1:8788/healthz" \
  "jysec-gateway.service http://127.0.0.1:8787/gateway-healthz"; do
  read -r unit url <<<"$service_url"
  if systemctl is-enabled --quiet "$unit" 2>/dev/null; then
    check_service "$unit" "$url" || result=1
  fi
done
check_unit jysec-proxy-tunnel.service || result=1
for port in 12080 12081 12082 12083 12084; do
  check_tcp "jysec-privoxy@$port.service" 127.0.0.1 "$port" || result=1
done
exit "$result"
EOF
chmod 0755 /usr/local/sbin/jysec-healthcheck

cat >/etc/systemd/system/jysec-healthcheck.service <<'EOF'
[Unit]
Description=JySecAI scanner backend health check
After=jysec-hexstrike.service jysec-kali-api.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/jysec-healthcheck
EOF

cat >/etc/systemd/system/jysec-healthcheck.timer <<'EOF'
[Unit]
Description=Check JySecAI scanner backends every minute

[Timer]
OnBootSec=90
OnUnitActiveSec=60
RandomizedDelaySec=10
Persistent=true
Unit=jysec-healthcheck.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now jysec-hexstrike.service jysec-kali-api.service jysec-healthcheck.timer
systemctl restart jysec-hexstrike.service jysec-kali-api.service
