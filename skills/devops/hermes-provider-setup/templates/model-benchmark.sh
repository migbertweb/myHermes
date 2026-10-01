#!/usr/bin/env bash
# Benchmark multiple OmniRoute auto/* models
# Edit MODELOS array to change which models to test
set -euo pipefail

API="http://localhost:20128/v1/chat/completions"
KEY="${OMNIROUTE_API_KEY:?Variable OMNIROUTE_API_KEY no definida}"

MODELOS=(
  "auto/best-coding"
  "auto/coding:fast"
  "auto/best-reasoning"
  "auto/coding:free"
)

PROMPT=$(cat <<'EOF'
Write a Python function that finds the second largest number
in a list without using sort() or external libraries.
Include a usage example.
EOF
)

echo "=============================="
echo "  OmniRoute Model Benchmark"
echo "=============================="
echo

for modelo in "${MODELOS[@]}"; do
  printf '%s\n' "--- $modelo ---"

  inicio_ms=$(date +%s%3N)

  tmp_out=$(mktemp)
  tmp_code=$(mktemp)

  curl -s --max-time 120 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $KEY" \
    -d "$(jq -nc --arg model "$modelo" --arg prompt "$PROMPT" '{
      model: $model,
      messages: [{role: "user", content: $prompt}],
      max_tokens: 512,
      stream: false
    }')" \
    "$API" > "$tmp_out" 2>/dev/null; echo "$?" > "$tmp_code"

  fin_ms=$(date +%s%3N)
  total_ms=$(( fin_ms - inicio_ms ))
  exit_code=$(cat "$tmp_code")

  body=$(cat "$tmp_out")
  rm -f "$tmp_out" "$tmp_code"

  if [ "$exit_code" != "0" ]; then
    echo "  curl exit code $exit_code (timeout/network)"
    echo "  ${total_ms}ms"
    echo
    continue
  fi

  if echo "$body" | jq -e '.error' >/dev/null 2>&1; then
    echo "  Error: $(echo "$body" | jq -r '.error.message // "unknown"')"
    echo "  ${total_ms}ms"
    echo
    continue
  fi

  content=$(echo "$body" | jq -r '.choices[0].message.content // "no content"')
  model_name=$(echo "$body" | jq -r '.model // "?"')
  usage=$(echo "$body" | jq -c '.usage // {}')

  p=$(echo "$usage" | jq -r '.prompt_tokens // "?"')
  c=$(echo "$usage" | jq -r '.completion_tokens // "?"')
  t=$(echo "$usage" | jq -r '.total_tokens // "?"')

  echo "  ${total_ms}ms | resolved: $model_name | tokens: ${p}-${c} (${t})"
  echo "  --- response ---"
  echo "$content" | head -12
  lines=$(echo "$content" | wc -l)
  [ "$lines" -gt 12 ] && echo "  ... ($((lines - 12)) more lines)"
  echo
done

echo "=============================="
echo "  Done"
echo "=============================="
