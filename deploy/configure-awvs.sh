#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this configuration helper as root." >&2
  exit 1
fi

SCANNER_ENV=${SCANNER_ENV:-/etc/jysecai/scanner-adapter.env}
PLATFORM_ENV=${PLATFORM_ENV:-/etc/jysecai/platform.env}
ADAPTER_URL=${JYSEC_ENGINE_AWVS_URL:-http://127.0.0.1:8790}
AWVS_CERT_FILE=${AWVS_CERT_FILE:-/mnt/c/ProgramData/Acunetix/certs/server.cer}

for file in "$SCANNER_ENV" "$PLATFORM_ENV"; do
  if [[ ! -f "$file" ]]; then
    echo "Required environment file is missing: $file" >&2
    exit 1
  fi
done

read_env() {
  local file=$1
  local key=$2
  sed -n "s/^${key}=//p" "$file" | head -n 1
}

set_env() {
  local file=$1
  local key=$2
  local value=$3
  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*$|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >>"$file"
  fi
}

current_url=$(read_env "$SCANNER_ENV" JYSEC_AWVS_API_URL)
current_key=$(read_env "$SCANNER_ENV" JYSEC_AWVS_API_KEY)
ca_file=$(read_env "$SCANNER_ENV" JYSEC_AWVS_CA_FILE)
tls_server_name=$(read_env "$SCANNER_ENV" JYSEC_AWVS_TLS_SERVER_NAME)

candidate_url=${AWVS_URL:-$current_url}
candidate_key=${AWVS_API_KEY:-${AWVS_API:-$current_key}}
candidate_url=${candidate_url%/}

if [[ -z "$candidate_url" || -z "$candidate_key" ]]; then
  echo "AWVS URL and API key must be configured." >&2
  exit 1
fi
if [[ "$candidate_url" != https://* ]]; then
  echo "AWVS URL must use HTTPS." >&2
  exit 1
fi

curl_args=(
  --silent
  --show-error
  --output /dev/null
  --write-out '%{http_code}'
  --max-time 20
  --header "X-Auth: ${candidate_key}"
)
if [[ -n "$ca_file" ]]; then
  if [[ ! -r "$ca_file" ]]; then
    echo "Configured AWVS CA file is not readable: $ca_file" >&2
    exit 1
  fi
  curl_args+=(--cacert "$ca_file")
fi

if status=$(curl "${curl_args[@]}" "${candidate_url}/api/v1/me" 2>/dev/null); then
  :
elif [[ -n "$ca_file" && -n "$tls_server_name" && -r "$AWVS_CERT_FILE" ]]; then
  # Acunetix can encode a numeric host as DNS SAN rather than IP SAN. Verify
  # the vendor certificate and CA explicitly, then pin its public key for the
  # live identity request instead of disabling TLS verification globally.
  openssl verify -CAfile "$ca_file" -verify_hostname "$tls_server_name" "$AWVS_CERT_FILE" >/dev/null
  public_key=$(mktemp)
  trap 'rm -f -- "$public_key"' EXIT
  openssl x509 -in "$AWVS_CERT_FILE" -pubkey -noout >"$public_key"
  status=$(curl "${curl_args[@]}" --insecure --pinnedpubkey "$public_key" "${candidate_url}/api/v1/me")
else
  echo "AWVS TLS identity verification failed." >&2
  exit 1
fi
if [[ ! "$status" =~ ^2[0-9][0-9]$ ]]; then
  echo "AWVS identity verification failed with HTTP ${status}." >&2
  exit 1
fi

if [[ ${AWVS_CHECK_ONLY:-0} == 1 ]]; then
  echo "AWVS identity verification returned HTTP ${status}."
  exit 0
fi

stamp=$(date -u +%Y%m%d%H%M%S)
cp -a "$SCANNER_ENV" "${SCANNER_ENV}.bak-${stamp}"
cp -a "$PLATFORM_ENV" "${PLATFORM_ENV}.bak-${stamp}"

scanner_changed=false
if [[ "$candidate_url" != "$current_url" ]]; then
  set_env "$SCANNER_ENV" JYSEC_AWVS_API_URL "$candidate_url"
  scanner_changed=true
fi
if [[ "$candidate_key" != "$current_key" ]]; then
  set_env "$SCANNER_ENV" JYSEC_AWVS_API_KEY "$candidate_key"
  scanner_changed=true
fi
set_env "$PLATFORM_ENV" JYSEC_ENGINE_AWVS_URL "$ADAPTER_URL"

chmod 0640 "$SCANNER_ENV" "$PLATFORM_ENV"
chown root:jysec "$SCANNER_ENV" "$PLATFORM_ENV"

if [[ "$scanner_changed" == true ]]; then
  systemctl restart jysec-scanner-adapter.service
fi
systemctl restart jysec-control-plane.service

/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:8790/healthz 60
/usr/local/sbin/jysec-wait-for-health http://127.0.0.1:8788/healthz 90

echo "AWVS is connected through ${ADAPTER_URL}; identity verification returned HTTP ${status}."
if [[ -n "$tls_server_name" ]]; then
  echo "TLS server-name verification remains pinned to ${tls_server_name}."
fi
