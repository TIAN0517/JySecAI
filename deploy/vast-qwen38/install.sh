#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspace/qwen38
SRC="$ROOT/llama.cpp"
MODEL_DIR="$ROOT/models"
MODEL="$MODEL_DIR/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q8_K_P.gguf"
REPO=https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF/resolve/main
COMMIT=4df29be4f4c3673f428170fda944a5b19f743bb8

mkdir -p "$MODEL_DIR"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --filter=blob:none https://github.com/ggerganov/llama.cpp "$SRC"
fi
git -C "$SRC" fetch --depth 1 origin "$COMMIT"
git -C "$SRC" checkout --force "$COMMIT"

curl --fail --location --retry 5 --output "$SRC/HauhauCS-FastMTP-llama.cpp.patch" \
  "$REPO/HauhauCS-FastMTP-llama.cpp.patch"
if git -C "$SRC" apply --check HauhauCS-FastMTP-llama.cpp.patch >/dev/null 2>&1; then
  git -C "$SRC" apply HauhauCS-FastMTP-llama.cpp.patch
fi

cmake -S "$SRC" -B "$SRC/build" -G Ninja \
  -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build "$SRC/build" --target llama-server -j"$(nproc)"

curl --fail --location --retry 10 --continue-at - --output "$MODEL" \
  "$REPO/$(basename "$MODEL")"
if [[ ! -s "$ROOT/.api-key" ]]; then
  umask 077
  openssl rand -hex 32 > "$ROOT/.api-key"
fi

install -m 0755 /tmp/qwen38-server.sh /opt/supervisor-scripts/qwen38-server.sh
install -m 0644 /tmp/qwen38-server.conf /etc/supervisor/conf.d/qwen38-server.conf
supervisorctl reread
supervisorctl update
supervisorctl restart qwen38-server
