# OmniRoute — Combo Debugging & Tuning (2026-08)

Cómo inspeccionar y afinar combos de OmniRoute sin tocar el dashboard a ciegas. Verificado en
instalación local (puerto 20128, OmniRoute v3.8.49).

## Leer la configuración de un combo (sin login)

El endpoint `GET /api/v1/combos` responde **sin autenticación** y devuelve la config completa:
nombre, estrategia y lista ordenada de nodos (`kind`, `model`, `providerId`).

```bash
curl -s http://localhost:20128/api/v1/combos | python3 -m json.tool
```

Útil porque `omniroute combo list` solo muestra nombre/estrategia/enabled, y NO existe
`combo show/info` — la asignación de nodos es exclusiva del dashboard web
(`localhost:20128` → login → Combos → combo → reordenar → guardar).

## Semántica de la estrategia `priority`

Con `priority`, OmniRoute usa el **primer nodo que responde sano**. Si el nodo #1 es lento
(modelo de razonamiento pesado), TODA request paga esa latencia aunque el nodo #2 responda en 1s.
Benchmark individual de nodos > benchmark del combo (el combo solo muestra al ganador).

## Benchmark de latencia por nodo

Prompt trivial + `max_tokens` chico, medir tiempo total:

```bash
for m in "kiro/deepseek-3.2" "kiro/glm-5" "kiro/qwen3-coder-next" "alibaba/qwen3.7-flash"; do
  t0=$(date +%s.%N)
  curl -s -m 90 http://localhost:20128/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"di hola\"}],\"max_tokens\":20,\"stream\":false}" >/dev/null
  t1=$(date +%s.%N)
  echo "$m: $(echo "$t1 $t0" | awk '{printf "%.2fs", $1-$2}')"
done
```

Un run corto mide TTFT, no generación completa. Para estimar velocidad de generación usar un
prompt de coding real con `max_tokens` ~300 y mirar `x-omniroute-latency-ms`.

## Headers de diagnóstico (revelan el routing real)

Capturar con `curl -s -D /tmp/h.txt -o /tmp/b.json ...`:

- `x-omniroute-provider` / `x-omniroute-model` — qué upstream/modelo sirvió
- `x-omniroute-latency-ms` — latencia upstream real (TTFT + generación)
- `x-omniroute-decision` — ej: `strategy=priority; provider=kr; latency_ms=46471`
- `x-omniroute-response-cost` — costo del request en USD
- `x-omniroute-tokens-in/out` — tokens reales contados por el gateway

## ⚠️ Inflado de system prompt en combos (costo/latencia oculto)

Al llamar un combo con un prompt de 15-30 tokens, `usage.prompt_tokens` puede reportar
**4.6-6.6K tokens**. El combo inyecta un system prompt masivo configurado en el dashboard.
Consecuencias: cada request paga contexto invisible (~6.5K tok) y el TTFT se alarga. Verificar
siempre: si `prompt_tokens` >> tamaño real del prompt, el combo tiene system prompt gigante.

## Modelos `auto/*` — son combos dinámicos, la latencia varía

Los `auto/*` (auto, auto/fast, auto/best-fast, auto/coding:fast, auto/cheap, ...) son combos de
routing: eligen upstream según salud del momento. Un run no es concluyente — el mismo modelo
puede medir 3.5s una vez y 8.3s después según qué upstream responda. Para elegir entre ellos,
benchmarkear varias corridas (ver `~/.hermes/scripts/benchmark_omniroute_reasoning.py` como base).

## Snapshot de salud de nodos (2026-08-01, instalación local)

| Nodo | Latencia (prompt corto) | Nota |
|---|---|---|
| kiro/qwen3-coder-next | 1.01s | especialista coding, más rápido |
| kiro/glm-5 | 1.21s | rápido |
| antigravity/gpt-oss-120b-medium | 1.16s | rápido |
| huggingface/deepseek-ai/DeepSeek-V3 | 1.69s | bien |
| kiro/deepseek-3.2 | 2.48s corto / **46s gen larga** | lento en output grande |
| opencode/deepseek-v4-flash-free | 2.26s | output vacío en 1 test — sospechoso |
| antigravity/gemini-3.1-flash-lite | 2.64s | aceptable |
| alibaba/qwen3.7-flash | **28.67s** | roto/lento (memoria ya lo marcaba) |

Conclusión de la sesión: el combo `combo-coding` tenía como nodo #1 `kiro/deepseek-3.2`
(46s en generación larga) — reordenar para poner los rápidos primero (`qwen3-coder-next`,
`glm-5`) y mandar alibaba al final o eliminarlo mejora la respuesta percibida sin cambiar
modelos.
