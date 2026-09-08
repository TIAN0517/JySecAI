#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

VPS_HOST=${1:-202.160.76.223}
KEY_FILE=${2:-/etc/jysecai/ssh/proxy_tunnel_ed25519}
KNOWN_HOSTS=${3:-/etc/jysecai/ssh/vps_known_hosts}

test -s "$KEY_FILE"
test -s "$KNOWN_HOSTS"
command -v ssh >/dev/null
install -d -o root -g root -m 0700 /etc/jysecai/ssh
chmod 0600 "$KEY_FILE"
install -d -o root -g root -m 0750 /etc/jysecai
install -o root -g root -m 0640 /dev/null /etc/jysecai/proxy-tunnel.env
if ! grep -q '^JYSEC_VPS_HOST=' /etc/jysecai/proxy-tunnel.env; then
  printf 'JYSEC_VPS_HOST=%s\n' "$VPS_HOST" >>/etc/jysecai/proxy-tunnel.env
fi
if ! grep -q '^JYSEC_PROXY_KEY=' /etc/jysecai/proxy-tunnel.env; then
  printf 'JYSEC_PROXY_KEY=%s\n' "$KEY_FILE" >>/etc/jysecai/proxy-tunnel.env
fi
if ! grep -q '^JYSEC_PROXY_KNOWN_HOSTS=' /etc/jysecai/proxy-tunnel.env; then
  printf 'JYSEC_PROXY_KNOWN_HOSTS=%s\n' "$KNOWN_HOSTS" >>/etc/jysecai/proxy-tunnel.env
fi
chmod 0640 /etc/jysecai/proxy-tunnel.env
chown root:jysec /etc/jysecai/proxy-tunnel.env

cat >/etc/systemd/system/jysec-proxy-tunnel.service <<'EOF'
[Unit]
Description=JySecAI VPS SOCKS5 loopback tunnel
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
Group=root
EnvironmentFile=/etc/jysecai/proxy-tunnel.env
ExecStart=/usr/bin/ssh -N -T -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o TCPKeepAlive=yes -o StrictHostKeyChecking=yes -o IdentitiesOnly=yes -o UserKnownHostsFile=${JYSEC_PROXY_KNOWN_HOSTS} -i ${JYSEC_PROXY_KEY} -L 127.0.0.1:11080:127.0.0.1:11080 -L 127.0.0.1:11081:127.0.0.1:11081 -L 127.0.0.1:11082:127.0.0.1:11082 -L 127.0.0.1:11083:127.0.0.1:11083 -L 127.0.0.1:11084:127.0.0.1:11084 jysec-tunnel@${JYSEC_VPS_HOST}
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=15
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
CapabilityBoundingSet=

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now jysec-proxy-tunnel.service
systemctl restart jysec-proxy-tunnel.service
for port in 11080 11081 11082 11083 11084; do
  for _ in $(seq 1 20); do
    if timeout 2 bash -c "</dev/tcp/127.0.0.1/$port" 2>/dev/null; then break; fi
    sleep 1
  done
  timeout 2 bash -c "</dev/tcp/127.0.0.1/$port" 2>/dev/null
done
systemctl --no-pager --full status jysec-proxy-tunnel.service | tail -n 12
