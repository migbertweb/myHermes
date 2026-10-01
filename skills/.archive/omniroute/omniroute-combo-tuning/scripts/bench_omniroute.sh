#!/bin/bash
# Benchmark OmniRoute model latency (SSE-aware, serial).
# Usage: ./bench_omniroute.sh [model1 model2 ...]   (defaults: kiro/nvidia/oc direct models)
# Env overrides: MAX_TOKENS=200 TIMEOUT_S=40 RUNS=3 GATEWAY=http://localhost:20128/v1
#
# Facts discovered 2026-08-03 (do NOT regress these):
#  1. The gateway ALWAYS streams SSE chunks (data: {...}) even without stream:true.
#     Parsing the body with plain jq gives "parse error". Must grep '^data:' lines
#     and concatenate .choices[0].delta.content.
#  2. Models that emit reasoning_details first (e.g. opencode-zen/north-mini-code-free)
#     return EMPTY final content when max_tokens is low (40). Use >=200.
#  3. Run SERIAL (xargs -P 1). Parallel load (xargs -P 4) saturates the gateway and
#     produces false EMPTY results — a model that is 5/5 OK alone can show 0/3 EMPTY
#     under concurrent calls.
set -u

MAX_TOKENS="${MAX_TOKENS:-200}"
TIMEOUT_S="${TIMEOUT_S:-40}"
GATEWAY="${GATEWAY:-http://localhost:20128/v1}"
RUNS="${RUNS:-3}"

if [ $# -gt 0 ]; then
  MODELS=("$@")
else
  MODELS=(
    "kiro/claude-sonnet-4.5"
    "kiro/deepseek-3.2"
    "kiro/glm-5"
    "kiro/qwen3-coder-next"
    "nvidia/z-ai/glm-5.2"
    "nvidia/deepseek-ai/deepseek-v4-pro"
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b"
    "opencode-zen/nemotron-3-ultra-free"
    "opencode-zen/north-mini-code-free"
  )
fi

bench_one() {
  local model="$1"
  local times=""
  local ok=0
  for ((i=1; i<=RUNS; i++)); do
    local out t text
    out=$(curl -s -m "$TIMEOUT_S" -X POST "$GATEWAY/chat/completions" \
      -H "Authorization: Bearer dummy" -H "Content-Type: application/json" \
      -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Hola, responde en una palabra.\"}],\"max_tokens\":$MAX_TOKENS}" \
      -w $'\n__TIME__%{time_total}' 2>/dev/null)
    t=$(echo "$out" | grep -o '__TIME__[0-9.]*' | head -1 | sed 's/__TIME__//')
    text=$(echo "$out" | grep '^data:' | sed 's/^data: //' | jq -r '.choices[0].delta.content // empty' 2>/dev/null | tr -d '\n')
    if [ -z "$t" ]; then
      times="$times TIMEOUT"
    elif [ -z "$text" ]; then
      times="$times EMPTY"
    else
      times="$times ${t}s"
      ok=$((ok+1))
    fi
  done
  echo "$model | ok=$ok/$RUNS |$times"
}

export RUNS MAX_TOKENS TIMEOUT_S GATEWAY
export -f bench_one
printf '%s\n' "${MODELS[@]}" | xargs -P 1 -I {} bash -c 'bench_one "$1"' _ {}
