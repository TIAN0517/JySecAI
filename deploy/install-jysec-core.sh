#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

REPO_ROOT=${1:-/mnt/c/Users/Administrator/Desktop/JySecAI}
APP_ROOT=/opt/jysecai/core
STATE_ROOT=/var/lib/jysecai/core
CONFIG_FILE=$STATE_ROOT/config.yaml
RELEASE_ID=$(date -u +%Y%m%d%H%M%S)-$$
RELEASE_DIR=$APP_ROOT/releases/$RELEASE_ID

test -f "$REPO_ROOT/go.mod"
test -f "$REPO_ROOT/config.example.yaml"
test -f "$REPO_ROOT/deploy/configure-core.py"
id jysec >/dev/null
command -v go >/dev/null
command -v python3 >/dev/null

install -d -o jysec -g jysec -m 0750 \
  "$APP_ROOT" "$APP_ROOT/releases" "$STATE_ROOT" "$STATE_ROOT/home" \
  "$STATE_ROOT/tmp" "$STATE_ROOT/workspace" "$STATE_ROOT/chat_uploads"
install -d -o jysec -g jysec -m 0750 /opt/jysecai/.cache/go-build /opt/jysecai/go/pkg/mod
chown -R jysec:jysec /opt/jysecai/.cache /opt/jysecai/go
install -d -o jysec -g jysec -m 0750 "$RELEASE_DIR"

cleanup_failed_release() {
  if [[ ! -L "$APP_ROOT/current" || $(readlink -f "$APP_ROOT/current") != "$RELEASE_DIR" ]]; then
    rm -rf -- "$RELEASE_DIR"
  fi
}
trap cleanup_failed_release EXIT

(
  cd "$REPO_ROOT"
  runuser -u jysec -- env \
    HOME=/opt/jysecai \
    GOPATH=/opt/jysecai/go \
    GOMODCACHE=/opt/jysecai/go/pkg/mod \
    GOCACHE=/opt/jysecai/.cache/go-build \
    GOPROXY=https://proxy.golang.org,direct \
    CGO_ENABLED=1 \
    go build -buildvcs=false -trimpath -ldflags='-s -w' -o "$RELEASE_DIR/jysec-core" ./cmd/server
)

for path in web tools agents roles skills knowledge_base mcp-servers; do
  test -d "$REPO_ROOT/$path"
  cp -a "$REPO_ROOT/$path" "$RELEASE_DIR/$path"
done
install -o jysec -g jysec -m 0640 "$REPO_ROOT/requirements.txt" "$RELEASE_DIR/requirements.txt"
chown -R jysec:jysec "$RELEASE_DIR"

if [[ ! -x "$APP_ROOT/venv/bin/python" ]]; then
  runuser -u jysec -- python3 -m venv "$APP_ROOT/venv"
fi
runuser -u jysec -- env HOME=/opt/jysecai \
  "$APP_ROOT/venv/bin/pip" install --disable-pip-version-check --no-input \
  --requirement "$RELEASE_DIR/requirements.txt"

ln -sfn "$RELEASE_DIR" "$APP_ROOT/current.new"
mv -Tf "$APP_ROOT/current.new" "$APP_ROOT/current"

NEW_INSTALL=()
if [[ ! -f "$CONFIG_FILE" ]]; then
  install -o jysec -g jysec -m 0600 "$REPO_ROOT/config.example.yaml" "$CONFIG_FILE"
  NEW_INSTALL=(--new-install)
else
  cp -a "$CONFIG_FILE" "$CONFIG_FILE.backup"
fi
python3 "$REPO_ROOT/deploy/configure-core.py" \
  "$CONFIG_FILE" "$APP_ROOT/current" "${NEW_INSTALL[@]}"
chown jysec:jysec "$CONFIG_FILE"
chmod 0600 "$CONFIG_FILE"

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

cat >/etc/systemd/system/jysec-core.service <<EOF
[Unit]
Description=JySecAI operations console
Wants=network-online.target jysec-hexstrike.service jysec-kali-api.service
After=network-online.target jysec-hexstrike.service jysec-kali-api.service
StartLimitIntervalSec=0
ConditionFileIsExecutable=$APP_ROOT/current/jysec-core

[Service]
Type=simple
User=jysec
Group=jysec
WorkingDirectory=$APP_ROOT/current
Environment=HOME=$STATE_ROOT/home
Environment=TMPDIR=$STATE_ROOT/tmp
Environment=VIRTUAL_ENV=$APP_ROOT/venv
Environment=PYTHONUNBUFFERED=1
Environment=PATH=$APP_ROOT/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games
ExecStart=$APP_ROOT/current/jysec-core --http -config $CONFIG_FILE
ExecStartPost=/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:6688/ 120
Restart=always
RestartSec=5
TimeoutStartSec=180
TimeoutStopSec=45
KillMode=mixed
UMask=0077
LimitNOFILE=65536
LimitNPROC=8192
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

systemctl daemon-reload
systemctl enable --now jysec-core.service
systemctl restart jysec-core.service
trap - EXIT
