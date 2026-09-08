#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then echo "Run this installer as root inside Kali WSL." >&2; exit 1; fi
EDGE_DIR=/etc/jysecai/edge
TLS_DIR=$EDGE_DIR/tls
install -d -o root -g jysec -m 0750 "$EDGE_DIR"
install -d -o root -g jysec -m 0750 "$TLS_DIR"

if [[ ! -s "$TLS_DIR/jysec-origin.key" || ! -s "$TLS_DIR/jysec-origin.crt" ]]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout "$TLS_DIR/jysec-origin.key" \
    -out "$TLS_DIR/jysec-origin.crt" \
    -subj "/CN=a.xs1.ccwu.cc/O=JySecAI" \
    -addext "subjectAltName=DNS:a.xs1.ccwu.cc,DNS:b.xs1.ccwu.cc,DNS:c.xs1.ccwu.cc,DNS:bossai.xs1.ccwu.cc" \
    -addext "keyUsage=digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth"
fi
chown root:jysec "$TLS_DIR/jysec-origin.key" "$TLS_DIR/jysec-origin.crt"
chmod 0640 "$TLS_DIR/jysec-origin.key" "$TLS_DIR/jysec-origin.crt"

cat >"$EDGE_DIR/nginx.conf" <<'EOF'
user jysec;
worker_processes auto;
pid /run/jysec-edge/nginx.pid;
error_log stderr warn;

events { worker_connections 2048; }

http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  access_log off;
  client_body_temp_path /run/jysec-edge/client_body;
  proxy_temp_path /run/jysec-edge/proxy;
  fastcgi_temp_path /run/jysec-edge/fastcgi;
  uwsgi_temp_path /run/jysec-edge/uwsgi;
  scgi_temp_path /run/jysec-edge/scgi;
  sendfile on;
  keepalive_timeout 65;

  map $host $known_host {
    default 0;
    a.xs1.ccwu.cc 1;
    b.xs1.ccwu.cc 1;
    c.xs1.ccwu.cc 1;
    bossai.xs1.ccwu.cc 1;
  }

  server {
    listen 18080;
    server_name a.xs1.ccwu.cc b.xs1.ccwu.cc c.xs1.ccwu.cc bossai.xs1.ccwu.cc;
    location = /gateway-healthz { access_log off; return 200 "ok\n"; }
    return 301 https://$host$request_uri;
  }

  server {
    listen 18443 ssl;
    server_name a.xs1.ccwu.cc b.xs1.ccwu.cc c.xs1.ccwu.cc bossai.xs1.ccwu.cc;
    if ($known_host = 0) { return 444; }
    ssl_certificate /etc/jysecai/edge/tls/jysec-origin.crt;
    ssl_certificate_key /etc/jysecai/edge/tls/jysec-origin.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
      proxy_pass http://127.0.0.1:8787;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto https;
      proxy_read_timeout 300s;
    }
  }
}
EOF
chmod 0640 "$EDGE_DIR/nginx.conf"
chown root:jysec "$EDGE_DIR/nginx.conf"

cat >/etc/systemd/system/jysec-edge.service <<'EOF'
[Unit]
Description=JySecAI public TLS reverse proxy
Wants=network-online.target jysec-gateway.service
After=network-online.target jysec-gateway.service
Requires=jysec-gateway.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=jysec
Group=jysec
RuntimeDirectory=jysec-edge
RuntimeDirectoryMode=0750
ExecStartPre=/usr/sbin/nginx -t -c /etc/jysecai/edge/nginx.conf
ExecStart=/usr/sbin/nginx -c /etc/jysecai/edge/nginx.conf -g "daemon off;"
ExecStartPost=/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:18080/gateway-healthz 30
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
systemctl enable --now jysec-edge.service
systemctl restart jysec-edge.service
systemctl --no-pager --full status jysec-edge.service | tail -n 14
