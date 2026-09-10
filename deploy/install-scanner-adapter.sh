#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

REPO_ROOT=${1:-/mnt/c/Users/Administrator/Desktop/JySecAI}
SOURCE_ROOT=$REPO_ROOT/platform
APP_ROOT=/opt/jysecai/platform-adapter
ENV_DIR=/etc/jysecai
ENV_FILE=$ENV_DIR/scanner-adapter.env
RELEASE_ID=$(date -u +%Y%m%d%H%M%S)-$$
RELEASE_DIR=$APP_ROOT/releases/$RELEASE_ID

test -f "$SOURCE_ROOT/package.json"
test -f "$SOURCE_ROOT/package-lock.json"
test -f "$SOURCE_ROOT/dist/scanner-adapter/main.js"
id jysec >/dev/null
command -v node >/dev/null
command -v npm >/dev/null
NODE_BIN=$(command -v node)

NODE_MAJOR=$(node -p 'Number(process.versions.node.split(".")[0])')
if (( NODE_MAJOR < 24 )); then
  echo "Node.js 24 or newer is required." >&2
  exit 1
fi

install -d -o jysec -g jysec -m 0750 "$APP_ROOT" "$APP_ROOT/releases"
install -d -o root -g jysec -m 0750 "$ENV_DIR"
install -d -o jysec -g jysec -m 0750 "$RELEASE_DIR" "$RELEASE_DIR/dist"

cleanup_failed_release() {
  if [[ ! -L "$APP_ROOT/current" || $(readlink -f "$APP_ROOT/current") != "$RELEASE_DIR" ]]; then
    rm -rf -- "$RELEASE_DIR"
  fi
}
trap cleanup_failed_release EXIT

install -o jysec -g jysec -m 0640 "$SOURCE_ROOT/package.json" "$RELEASE_DIR/package.json"
install -o jysec -g jysec -m 0640 "$SOURCE_ROOT/package-lock.json" "$RELEASE_DIR/package-lock.json"
cp -a "$SOURCE_ROOT/dist/." "$RELEASE_DIR/dist/"
chown -R jysec:jysec "$RELEASE_DIR/dist"

runuser -u jysec -- env HOME=/opt/jysecai \
  npm --prefix "$RELEASE_DIR" ci --omit=dev --ignore-scripts --no-audit --no-fund

if [[ ! -e "$ENV_FILE" ]]; then
  install -o root -g jysec -m 0640 /dev/null "$ENV_FILE"
fi
chmod 0640 "$ENV_FILE"
chown root:jysec "$ENV_FILE"

set_default() {
  local key=$1
  local value=$2
  if grep -q "^${key}=$" "$ENV_FILE"; then
    sed -i "s|^${key}=$|${key}=${value}|" "$ENV_FILE"
  elif ! grep -q "^${key}=" "$ENV_FILE"; then
    printf '%s=%s\n' "$key" "$value" >>"$ENV_FILE"
  fi
}

set_default JYSEC_LOG_LEVEL info
set_default JYSEC_SCANNER_ADAPTER_HOST 127.0.0.1
set_default JYSEC_SCANNER_ADAPTER_PORT 8790
set_default JYSEC_HEXSTRIKE_API_URL http://127.0.0.1:8888
set_default JYSEC_KALI_API_URL http://127.0.0.1:5000
set_default JYSEC_SCANNER_MAX_CONCURRENT_PER_ENGINE 2
set_default JYSEC_SCANNER_REQUEST_TIMEOUT_SECONDS 300
set_default JYSEC_SCANNER_MAX_RETRIES 3
set_default JYSEC_PROXY_POOL 'vps-221|socks5h://127.0.0.1:11080|http://127.0.0.1:12080|202.160.76.221;vps-173|socks5h://127.0.0.1:11081|http://127.0.0.1:12081|202.160.76.173;vps-169|socks5h://127.0.0.1:11082|http://127.0.0.1:12082|202.160.76.169;vps-168|socks5h://127.0.0.1:11083|http://127.0.0.1:12083|202.160.76.168;vps-167|socks5h://127.0.0.1:11084|http://127.0.0.1:12084|202.160.76.167'

if ! grep -Eq '^JYSEC_ENGINE_ADAPTER_TOKEN=.{32,}$' "$ENV_FILE"; then
  sed -i '/^JYSEC_ENGINE_ADAPTER_TOKEN=/d' "$ENV_FILE"
  printf 'JYSEC_ENGINE_ADAPTER_TOKEN=%s\n' "$(openssl rand -hex 32)" >>"$ENV_FILE"
fi

ln -sfn "$RELEASE_DIR" "$APP_ROOT/current.new"
mv -Tf "$APP_ROOT/current.new" "$APP_ROOT/current"

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

cat >/etc/systemd/system/jysec-scanner-adapter.service <<EOF
[Unit]
Description=JySecAI scanner integration adapter
Wants=network-online.target jysec-hexstrike.service jysec-kali-api.service
After=network-online.target jysec-hexstrike.service jysec-kali-api.service
StartLimitIntervalSec=0
ConditionFileIsExecutable=$NODE_BIN

[Service]
Type=simple
User=jysec
Group=jysec
WorkingDirectory=$APP_ROOT/current
Environment=HOME=/opt/jysecai
Environment=NODE_ENV=production
EnvironmentFile=$ENV_FILE
ExecStart=$NODE_BIN dist/scanner-adapter/main.js
ExecStartPost=/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:8790/healthz 60
Restart=always
RestartSec=5
TimeoutStartSec=60
TimeoutStopSec=30
KillMode=mixed
UMask=0077
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=full
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectClock=true
ProtectHostname=true
LockPersonality=true
RestrictSUIDSGID=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now jysec-scanner-adapter.service
systemctl restart jysec-scanner-adapter.service
trap - EXIT
