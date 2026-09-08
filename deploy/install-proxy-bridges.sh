#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then echo "Run this installer as root." >&2; exit 1; fi
command -v privoxy >/dev/null
PRIVOXY_GROUP=$(id -gn privoxy)
install -d -o root -g root -m 0755 /etc/privoxy/jysecai
install -d -o privoxy -g "$PRIVOXY_GROUP" -m 0750 /var/log/jysecai

ports=(12080 12081 12082 12083 12084)
socks=(11080 11081 11082 11083 11084)
for i in "${!ports[@]}"; do
  p=${ports[$i]}; s=${socks[$i]}
  install -o root -g root -m 0644 /dev/null "/etc/privoxy/jysecai/$p.conf"
  sed -i '1,$d' "/etc/privoxy/jysecai/$p.conf"
  printf '%s\n' \
    "confdir /etc/privoxy" \
    "templdir /etc/privoxy/templates" \
    "listen-address 127.0.0.1:$p" \
    "toggle 1" \
    "enable-remote-toggle 0" \
    "enable-edit-actions 0" \
    "accept-intercepted-requests 0" \
    "forward-socks5t / 127.0.0.1:$s ." \
    "logdir /var/log/jysecai" \
    "logfile privoxy-$p.log" \
    "show-on-task-bar 0" \
    "activity-animation 0" \
    "hostname outgoing" \
    >"/etc/privoxy/jysecai/$p.conf"
done

cat >/etc/systemd/system/jysec-privoxy@.service <<EOF
[Unit]
Description=JySecAI HTTP bridge for SOCKS5 port %i
Wants=network-online.target jysec-proxy-tunnel.service
After=network-online.target jysec-proxy-tunnel.service
Requires=jysec-proxy-tunnel.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=privoxy
Group=$PRIVOXY_GROUP
ExecStart=/usr/sbin/privoxy --no-daemon /etc/privoxy/jysecai/%i.conf
Restart=always
RestartSec=5
TimeoutStopSec=15
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
for p in "${ports[@]}"; do systemctl enable --now "jysec-privoxy@$p.service"; done
for p in "${ports[@]}"; do systemctl restart "jysec-privoxy@$p.service"; done
for p in "${ports[@]}"; do timeout 5 bash -c "</dev/tcp/127.0.0.1/$p"; done
systemctl --no-pager --plain --full status jysec-privoxy@12080.service | tail -n 12
