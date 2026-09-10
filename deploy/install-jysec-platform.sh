#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

REPO_ROOT=${1:-/mnt/c/Users/Administrator/Desktop/YySecAI}
SOURCE_ROOT=$REPO_ROOT/platform
APP_ROOT=/opt/jysecai/platform
STATE_ROOT=/var/lib/jysecai/platform
ENV_FILE=/etc/jysecai/platform.env
RELEASE_ID=$(date -u +%Y%m%d%H%M%S)-$$
RELEASE_DIR=$APP_ROOT/releases/$RELEASE_ID

test -f "$SOURCE_ROOT/dist/main.js"
test -f "$SOURCE_ROOT/dist/worker/main.js"
test -f "$SOURCE_ROOT/package-lock.json"
test -f /etc/jysecai/scanner-adapter.env
command -v node >/dev/null
command -v npm >/dev/null
command -v psql >/dev/null
command -v redis-server >/dev/null
command -v nginx >/dev/null
NODE_BIN=$(command -v node)

systemctl enable --now postgresql.service redis-server.service
if ! runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='jysec'" | grep -q 1; then
  runuser -u postgres -- createuser jysec
fi
if ! runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_database WHERE datname='jysec'" | grep -q 1; then
  runuser -u postgres -- createdb --owner=jysec jysec
fi

install -d -o jysec -g jysec -m 0750 "$APP_ROOT" "$APP_ROOT/releases" "$STATE_ROOT" "$STATE_ROOT/runs"
install -d -o jysec -g jysec -m 0750 "$RELEASE_DIR" "$RELEASE_DIR/dist" "$RELEASE_DIR/public"
cp -a "$SOURCE_ROOT/dist/." "$RELEASE_DIR/dist/"
cp -a "$SOURCE_ROOT/public/." "$RELEASE_DIR/public/"
cp -a "$SOURCE_ROOT/migrations" "$RELEASE_DIR/migrations"
install -o jysec -g jysec -m 0640 "$SOURCE_ROOT/package.json" "$RELEASE_DIR/package.json"
install -o jysec -g jysec -m 0640 "$SOURCE_ROOT/package-lock.json" "$RELEASE_DIR/package-lock.json"
chown -R jysec:jysec "$RELEASE_DIR"
runuser -u jysec -- env HOME=/opt/jysecai \
  npm --prefix "$RELEASE_DIR" ci --omit=dev --ignore-scripts --no-audit --no-fund

install -d -o root -g jysec -m 0750 /etc/jysecai
if [[ ! -e "$ENV_FILE" ]]; then
  install -o root -g jysec -m 0640 /dev/null "$ENV_FILE"
fi
set_default() {
  local key=$1
  local value=$2
  if grep -q "^${key}=$" "$ENV_FILE"; then
    sed -i "s|^${key}=$|${key}=${value}|" "$ENV_FILE"
  elif ! grep -q "^${key}=" "$ENV_FILE"; then
    printf '%s=%s\n' "$key" "$value" >>"$ENV_FILE"
  fi
}
set_secret() {
  local key=$1
  if ! grep -Eq "^${key}=.{32,}$" "$ENV_FILE"; then
    sed -i "/^${key}=/d" "$ENV_FILE"
    printf '%s=%s\n' "$key" "$(openssl rand -hex 32)" >>"$ENV_FILE"
  fi
}

set_default NODE_ENV development
set_default YYSEC_HOST 127.0.0.1
set_default YYSEC_PORT 8788
set_default YYSEC_LOG_LEVEL info
set_default YYSEC_STORE postgres
set_default DATABASE_URL 'postgresql:///jysec?host=/var/run/postgresql'
set_default REDIS_URL redis://127.0.0.1:6379/0
set_default YYSEC_DEV_AUTH true
set_default YYSEC_RUNS_ROOT "$STATE_ROOT/runs"
set_default YYSEC_PUBLIC_BASE_URL http://127.0.0.1:8788
set_default YYSEC_INTERNAL_CALLBACK_BASE_URL http://127.0.0.1:8788
set_default YYSEC_ENGINE_STRIX_ENABLED false
set_default JYSECAI_BASE_URL http://127.0.0.1:6688
set_default YYSEC_ENGINE_HEXSTRIKE_URL http://127.0.0.1:8790
set_default YYSEC_ENGINE_KALI_MCP_URL http://127.0.0.1:8790
set_secret YYSEC_YWT_SECRET
set_secret YYSEC_YOB_SIGNING_SECRET
set_secret YYSEC_METRICS_TOKEN
ADAPTER_TOKEN=$(sed -n 's/^YYSEC_ENGINE_ADAPTER_TOKEN=//p' /etc/jysecai/scanner-adapter.env | head -n 1)
test ${#ADAPTER_TOKEN} -ge 32
if grep -q '^YYSEC_ENGINE_ADAPTER_TOKEN=' "$ENV_FILE"; then
  sed -i "s|^YYSEC_ENGINE_ADAPTER_TOKEN=.*$|YYSEC_ENGINE_ADAPTER_TOKEN=$ADAPTER_TOKEN|" "$ENV_FILE"
else
  printf 'YYSEC_ENGINE_ADAPTER_TOKEN=%s\n' "$ADAPTER_TOKEN" >>"$ENV_FILE"
fi
chmod 0640 "$ENV_FILE"
chown root:jysec "$ENV_FILE"

ln -sfn "$RELEASE_DIR" "$APP_ROOT/current.new"
mv -Tf "$APP_ROOT/current.new" "$APP_ROOT/current"

cat >/etc/systemd/system/jysec-control-plane.service <<EOF
[Unit]
Description=YySecAI governance control plane
Wants=network-online.target postgresql.service redis-server.service
After=network-online.target postgresql.service redis-server.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=jysec
Group=jysec
WorkingDirectory=$APP_ROOT/current
Environment=HOME=/opt/jysecai
EnvironmentFile=$ENV_FILE
ExecStart=$NODE_BIN dist/main.js
ExecStartPost=/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:8788/healthz 90
Restart=always
RestartSec=5
TimeoutStartSec=120
TimeoutStopSec=30
KillMode=mixed
UMask=0077
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
CapabilityBoundingSet=

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/jysec-worker.service <<EOF
[Unit]
Description=YySecAI scanner worker
Wants=network-online.target redis-server.service
After=network-online.target redis-server.service jysec-control-plane.service jysec-scanner-adapter.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=jysec
Group=jysec
WorkingDirectory=$APP_ROOT/current
Environment=HOME=/opt/jysecai
EnvironmentFile=$ENV_FILE
ExecStart=$NODE_BIN dist/worker/main.js
Restart=always
RestartSec=5
TimeoutStopSec=45
KillMode=mixed
UMask=0077
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
CapabilityBoundingSet=

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now jysec-control-plane.service jysec-worker.service
systemctl restart jysec-control-plane.service
systemctl restart jysec-worker.service

cat >/etc/jysecai/nginx-gateway.conf <<'EOF'
worker_processes 1;
pid /run/jysec-gateway/nginx.pid;
error_log stderr warn;

events {
  worker_connections 1024;
}

http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  client_body_temp_path /run/jysec-gateway/client_body;
  proxy_temp_path /run/jysec-gateway/proxy;
  fastcgi_temp_path /run/jysec-gateway/fastcgi;
  uwsgi_temp_path /run/jysec-gateway/uwsgi;
  scgi_temp_path /run/jysec-gateway/scgi;
  access_log off;
  sendfile on;
  keepalive_timeout 65;

  server {
    listen 127.0.0.1:8787;
    server_name localhost;

    location = /gateway-healthz {
      access_log off;
      default_type application/json;
      return 200 '{"status":"ok","service":"jysec-gateway"}\n';
    }

    location ^~ /internal/ { return 404; }
    location = /governance { return 308 /governance/; }
    location ^~ /governance/ {
      proxy_pass http://127.0.0.1:8788/;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
    location ^~ /assets/ { proxy_pass http://127.0.0.1:8788; }
    location ^~ /v1/ { proxy_pass http://127.0.0.1:8788; }
    location = /metrics { proxy_pass http://127.0.0.1:8788; }
    location = /platform-healthz { proxy_pass http://127.0.0.1:8788/healthz; }

    location / {
      proxy_pass http://127.0.0.1:6688;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-Proto $scheme;
    }
  }
}
EOF
chmod 0640 /etc/jysecai/nginx-gateway.conf
chown root:jysec /etc/jysecai/nginx-gateway.conf

cat >/etc/systemd/system/jysec-gateway.service <<'EOF'
[Unit]
Description=YySecAI local gateway
Wants=network-online.target
After=network-online.target jysec-core.service jysec-control-plane.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=jysec
Group=jysec
RuntimeDirectory=jysec-gateway
RuntimeDirectoryMode=0750
ExecStartPre=/usr/sbin/nginx -t -c /etc/jysecai/nginx-gateway.conf
ExecStart=/usr/sbin/nginx -c /etc/jysecai/nginx-gateway.conf -g "daemon off;"
ExecStartPost=/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:8787/gateway-healthz 30
Restart=always
RestartSec=5
TimeoutStartSec=45
TimeoutStopSec=15
KillSignal=SIGQUIT
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
CapabilityBoundingSet=

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now jysec-gateway.service
systemctl restart jysec-gateway.service
