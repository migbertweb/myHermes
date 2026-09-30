#!/usr/bin/env bash
# Benchmark providers using hermes chat with timeout-driven measurement
set -e

PROMPT="Escribe exactamente 3 líneas sobre la teoría de la relatividad en español explicada para niños. No agregues nada más."

echo "=========================================="
echo "  BENCHMARK: opencode-go vs deepseek"
echo "=========================================="

for provider in "opencode-go" "deepseek"; do
  echo ""
  echo "⏳ Probando $provider..."

  START=$(date +%s.%N)
  
  # Run in background with a named pipe to feed /exit after response
  # Use -Q for quiet mode, capture output
  OUTPUT=$(timeout 60 python3 -c "
import subprocess, time, sys
p = subprocess.Popen(
    ['hermes', 'chat', '-q', '$PROMPT', '--provider', '$provider', '-Q'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(2)  # Let it start
p.stdin.write('/exit\n')
p.stdin.flush()
try:
    stdout, stderr = p.communicate(timeout=50)
    print(stdout, end='')
except subprocess.TimeoutExpired:
    p.kill()
    stdout, stderr = p.communicate()
    print(stdout, end='')
" 2>/dev/null) || true
  
  END=$(date +%s.%N)
  DURATION=$(echo "$END - $START" | bc -l 2>/dev/null || echo "?")
  
  # Extract response (last non-empty line before status messages)
  RESPONSE=$(echo "$OUTPUT" | grep -v '^\[' | grep -v '^Query:' | grep -v 'Initializing' | grep -v '^─' | grep -v '^╭' | grep -v '^╰' | grep -v '^\|' | grep -v '^\$' | grep -v '^ ' | grep -v '^$' | tail -5)
  
  echo "   Tiempo: ${DURATION}s"
  echo "   Respuesta: ${RESPONSE:0:120}..."

# Extract response content between the box
  CONTENT=$(echo "$OUTPUT" | sed -n '/│/{s/.*│ *//;s/ *│.*//;p;}' | head -5)
  if [ -n "$CONTENT" ]; then
    echo ""
    echo "$CONTENT"
  fi
done

echo ""
echo "=========================================="
echo "  LISTO - compara tiempos arriba"
echo "=========================================="
