#!/usr/bin/env bash
source /opt/supervisor-scripts/utils/environment.sh
set -euo pipefail

ROOT=/workspace/qwen38
MODEL_DIR=/dev/shm/qwen38
MODEL="$MODEL_DIR/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q8_K_P.gguf"
API_KEY="$(<"$ROOT/.api-key")"

mkdir -p "$MODEL_DIR"
if [[ ! -f "$MODEL" ]] || [[ "$(stat -c %s "$MODEL")" != "31457990784" ]]; then
  source /venv/main/bin/activate
  HF_XET_HIGH_PERFORMANCE=1 hf download \
    HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF \
    Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q8_K_P.gguf \
    --local-dir "$MODEL_DIR"
fi

export CUDA_VISIBLE_DEVICES=0
exec "$ROOT/llama.cpp/build/bin/llama-server" \
  --model "$MODEL" \
  --spec-type draft-mtp \
  --spec-draft-n-max 2 \
  --spec-draft-p-min 0 \
  --ctx-size 65536 \
  --parallel 2 \
  --batch-size 2048 \
  --ubatch-size 512 \
  --n-gpu-layers all \
  --split-mode none \
  --flash-attn on \
  --no-mmap \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --temp 1.0 \
  --top-k 20 \
  --top-p 0.95 \
  --min-p 0 \
  --presence-penalty 0 \
  --repeat-penalty 1.0 \
  --jinja \
  --reasoning on \
  --reasoning-effort xhigh \
  --reasoning-preserve \
  --reasoning-format deepseek \
  --api-key "$API_KEY" \
  --host 127.0.0.1 \
  --port 10300
