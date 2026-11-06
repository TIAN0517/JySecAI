#!/usr/bin/env bash
set -u
f=/home/bossjy/.hermes/hermes-agent/agent/auxiliary_client.py
wc -l "$f"
rg -n '_build_codex_client|Invalid schema|chat.completions|def ' "$f" | head -60
# find related modules
rg -n 'Invalid schema for function' /home/bossjy/.hermes/hermes-agent -g '*.py' | head -20
rg -n 'oneOf|ParamsOneOf|ToOpenAI|openai.*tool' /home/bossjy/go/pkg/mod/github.com/cloudwego/eino@v0.9.14/schema/*.go 2>/dev/null | head -40
