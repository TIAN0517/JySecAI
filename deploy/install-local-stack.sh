#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then echo "Run this installer as root inside Kali WSL." >&2; exit 1; fi
ROOT=${1:-/mnt/c/Users/Administrator/Desktop/JySecAI}

bash "$ROOT/deploy/install-kali-integrations.sh" "$ROOT"
# install-jysec-core deploys the curated vuln-intel MCP and its Skill together
# with the core release, then registers it in the protected runtime config.
bash "$ROOT/deploy/install-jysec-core.sh" "$ROOT"
bash "$ROOT/deploy/install-scanner-adapter.sh" "$ROOT"
bash "$ROOT/deploy/install-jysec-platform.sh" "$ROOT"
bash "$ROOT/deploy/install-vps-proxy-tunnel.sh"
bash "$ROOT/deploy/install-proxy-bridges.sh"

systemctl --no-pager --plain --full is-active \
  jysec-core.service jysec-control-plane.service jysec-worker.service \
  jysec-scanner-adapter.service jysec-gateway.service jysec-proxy-tunnel.service \
  jysec-privoxy@12080.service jysec-privoxy@12081.service \
  jysec-privoxy@12082.service jysec-privoxy@12083.service jysec-privoxy@12084.service
