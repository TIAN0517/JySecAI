#!/usr/bin/env bash
set -u
GOMOD=$(go env GOMODCACHE)
BASE="$GOMOD/github.com/cloudwego/eino-ext/components/model/agenticopenai@v0.2.1"
rg -n 'ParamsOneOf|ToJSONSchema|Function|tools|oneOf|Parameters' "$BASE" | head -60
echo '==== openai model ===='
BASE2="$GOMOD/github.com/cloudwego/eino-ext/components/model/openai@v0.1.13"
rg -n 'ParamsOneOf|ToJSONSchema|Function|tools|Parameters' "$BASE2" | head -40
echo '==== eino schema to openai ===='
rg -n 'ToOpenAI|OpenAITool|FuncTool|tool2openai|convertTool' "$GOMOD/github.com/cloudwego/eino@"*/ 2>/dev/null | head -40
