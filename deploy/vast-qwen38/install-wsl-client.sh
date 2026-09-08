#!/usr/bin/env bash
set -euo pipefail

SOURCE=/mnt/c/Users/Administrator/Desktop/JySecAI/deploy/vast-qwen38
KEY_DIR=/etc/jysecai/qwen38

install -d -m 0700 "$KEY_DIR"
scp -q -P 19831 \
  -i /root/.ssh/id_ed25519_qwen38 \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=accept-new \
  root@175.155.64.146:/workspace/qwen38/.api-key \
  "$KEY_DIR/api-key"
chmod 0600 "$KEY_DIR/api-key"

install -m 0644 \
  "$SOURCE/jysec-qwen38-tunnel.service" \
  /etc/systemd/system/jysec-qwen38-tunnel.service
python3 "$SOURCE/configure-jysecai-client.py" \
  --config /var/lib/jysecai/core/config.yaml \
  --api-key-file "$KEY_DIR/api-key"

systemctl daemon-reload
systemctl enable --now jysec-qwen38-tunnel.service
systemctl is-active jysec-qwen38-tunnel.service

