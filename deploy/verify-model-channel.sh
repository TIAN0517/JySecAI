#!/usr/bin/env bash
set -euo pipefail

config_file=${1:-/opt/jysecai/config.yaml}
channel=$(awk '/^[[:space:]]*default_channel:/ {print $2; exit}' "$config_file")
read_channel_value() {
  local key=$1
  awk -v channel="$channel" -v key="$key" '
    $0 ~ "^    " channel ":" {in_channel=1; next}
    in_channel && $0 ~ "^    [^ ]" {exit}
    in_channel && $1 == key ":" {sub("^[[:space:]]*" key ":[[:space:]]*", ""); gsub(/^"|"$/, ""); print; exit}
  ' "$config_file"
}

base_url=$(read_channel_value base_url)
api_key=$(read_channel_value api_key)
model=$(read_channel_value model)
test_url=${base_url%/}/chat/completions
response_file=$(mktemp)
trap 'rm -f "$response_file"' EXIT

status=$(curl --silent --show-error --output "$response_file" --write-out '%{http_code}' \
  --max-time 90 \
  --header "Authorization: Bearer $api_key" \
  --header 'Content-Type: application/json' \
  --data "$(printf '{\"model\":%s,\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: model-ok\"}],\"max_tokens\":16,\"stream\":false}' "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$model")")" \
  "$test_url")

python3 - "$status" "$channel" "$model" "$response_file" <<'PY'
import json
import sys

status, channel, model, path = sys.argv[1:]
try:
    payload = json.load(open(path, encoding="utf-8"))
except Exception:
    payload = {}
content = ""
try:
    content = payload["choices"][0]["message"]["content"]
except Exception:
    content = ""
print(json.dumps({
    "http_status": int(status),
    "channel": channel,
    "configured_model": model,
    "responded": bool(content.strip()),
    "response_preview": content.strip()[:120],
}, ensure_ascii=False))
PY
