# OmniRoute auto/* latency — measured 2026-08-01

Benchmark rápido (1 run, prompt trivial "Di hola en una palabra", max_tokens=20, stream=false,
vía `curl http://localhost:20128/v1/chat/completions`). Latencia total incluye warmup de
primer request tras arranque del gateway (Next.js: primer hit compila, puede tardar más).

| Modelo | Latencia | Nota |
|---|---|---|
| auto/coding:fast | 3.45s | más rápido medido |
| auto | 3.90s | default balanceado |
| auto/cheap | 3.93s | prioriza costo, casi igual |
| auto/best-fast | 4.00s | mejor calidad de la línea fast |
| auto/best-coding-fast | 6.46s | |
| auto/pro-fast | 6.50s | modelo mayor |
| auto/best-free | 6.59s | free tier |
| auto/fast | 8.29s | el nombre engaña — fue el peor hoy |

## Lectura

- Los combos `auto/*` son routing dinámico: la latencia varía según qué upstream esté sano
  en el momento. Un run no es concluyente — para decidir entre combos, correr 3+ veces.
- Script listo: `~/.hermes/scripts/benchmark_omniroute_reasoning.py` (benchmarkea
  `auto/reasoning*` con 3 corridas y ranking). Adaptar MODELS para comparar los `fast`.
- Los headers `x-omniroute-provider` / `x-omniroute-model` (que revelan el upstream real)
  no siempre aparecen en respuestas con `curl -D -`; si se necesitan, capturar con
  `-s -D /tmp/h.txt -o /tmp/b.json` y leer los archivos por separado.
- Primer request tras arrancar OmniRoute puede tardar mucho (compilación Next.js / esbuild).
  Usar `-m 60` de timeout y reintentar antes de declarar el gateway caído.
