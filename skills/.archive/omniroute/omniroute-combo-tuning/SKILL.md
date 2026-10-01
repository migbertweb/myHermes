---
name: omniroute-combo-tuning
description: Benchmark OmniRoute auto/* aliases for Hermes MoA combos.
version: "1.0 (2026-08-01) — first benchmark pass"
---

# OmniRoute Combo Tuning

Gateway local: `http://localhost:20128/v1` (OpenAI-compatible). `auto/*` aliases are **routing strategies** (LKGP scoring over connected upstream providers), not fixed models — `owned_by: combo`, all advertise `context_length: 1048576` + tool_calling/reasoning/thinking.

## Listing aliases

```bash
curl -s localhost:20128/v1/models | jq -r '.data[].id' | grep '^auto/' | sort -u
```

## Benchmarking latency before committing a combo

Streaming SSE: `curl -s` returns after the stream completes, so `-w '%{time_total}'` measures full response time.

```bash
for i in 1 2 3; do
  curl -s -X POST localhost:20128/v1/chat/completions \
    -H "Authorization: Bearer dummy" -H "Content-Type: application/json" \
    -d '{"model":"auto/best-fast","messages":[{"role":"user","content":"Hola"}],"max_tokens":15}' \
    -w "TIME %{time_total}s\n" -o /dev/null
done
```

- Run ≥3 times per alias — variance is HIGH (cold starts, quota, upstream switching).
- Add a per-call timeout (`-m 40`) so a stuck upstream doesn't hang the whole pass.
- Re-benchmark per day: alias latency tracks whatever upstream the scorer picks.

## Measured results (2026-08-01, p50)

| Alias | p50 | Verdict |
|---|---|---|
| `auto/best-fast` | ~3.8s | ✅ executor agents / default |
| `auto/reasoning` | ~4.8s hard, ~3.9s easy (2026-08-02) | ✅ reasoning tasks — fastest & stable (4.4-5.0s) |
| `auto/best-reasoning` | ~8.1s hard (5.6-8.2s), ~3.9s easy | ⚠️ same quality as reasoning but ~2x slower on hard prompts, high variance; prefer `auto/reasoning` |
| `auto/best-free` | 30s+ (timeout) | ❌ no |
| `auto/coding` | >45s (timeout) | ❌ no |
| `auto/chat` | >60s (timeout) | ❌ no |

⚠️ Pitfall: reasoning aliases burn max_tokens budget on `reasoning_content` — with max_tokens ≈40 the final answer comes back EMPTY (measured 4/8 runs). Keep max_tokens ≥100 for these aliases. Both `auto/reasoning` and `auto/best-reasoning` report internal model `big-pickle` in SSE chunks, so latency differences are pure routing strategy, not model choice.

## Estado 2026-08-02 (catálogo 480 modelos — se re-expandió tras el trim)

Screening de 40 modelos (1-2 runs c/u, gateway local):

| Modelo | p50 | Estado |
|---|---|---|
| `oc/nemotron-3-ultra-free` | 2.1s | ✅ estable, ok 5/5 |
| `oc/ling-3.0-flash-free` | 2.4s | ✅ estable, ok 5/5 |
| `antigravity/claude-opus-4-6-thinking` | 3.3s | ✅ funciona (2.4-4.2s); SIN sufijo -high/-low/-medium (esos dan 404) |
| `oc/mimo-v2.5-free` | 3.8s | ⚠️ intermitente (0/2 en 2º pass, 3/3 en 1º) |
| `oc/deepseek-v4-flash-free` | 4.0s | ⚠️ intermitente (1/2 → 3/3) |
| `oc/north-mini-code-free` | 4.5s | ✅ estable, ok 5/5 |
| `oc/laguna-s-2.1-free` | 6.4s | ⚠️ lento e intermitente |

Caídos o inutilizables hoy:
- **antigravity/gemini-\***: `All antigravity accounts have exhausted their quota (reset after 5m)` — intermitente por diseño, responde en 0.06-0.6s cuando hay cuota. Reintentar; no sirven para un combo que deba ser confiable.
- **antigravity/claude-sonnet-\*** y opus-\*-thinking-{high,low,medium}: `404 model_not_found` / `model_cooldown` — variantes muertas upstream.
- **oc/gemini-3.5-flash(-lite)**, oc/gpt-*, oc/glm-*, oc/kimi-\*, oc/qwen\*: `401 Missing API key` — NO son free, requieren credenciales.
- **pol/\*, pollinations/\***, **ddgw/\***, **tllm/\***: 401 sin key o stream_early_eof. **aug/\***: stream_early_eof (inestable). **mcode/mimo-auto**: 400 unsupported.

| `hf/deepseek-ai/DeepSeek-V3` | 1.4s | ✅ vivo, responde correcto (0.45-1.47s) |
| `hf/Qwen/Qwen2.5-7B-Instruct` | 0.7s | ⚠️ vivo pero 1/2 respuestas vacías — pequeño, inestable |
| `huggingface/*` (todos) | — | ❌ `No active credentials for provider: huggingface` — muertos; usar SOLO prefijo `hf/` |

Combo agentic recomendado (7, orden por velocidad): `oc/nemotron-3-ultra-free` → `oc/ling-3.0-flash-free` → `antigravity/claude-opus-4-6-thinking` (aggregator) → `oc/mimo-v2.5-free` → `oc/deepseek-v4-flash-free` → `oc/north-mini-code-free` → `oc/laguna-s-2.1-free` (fallback). Si la quota antigravity está activa, los gemini (0.1-0.6s) van al tope.

## Benchmark 2026-08-03 — kiro / nvidia / oc directos (SSE-only)

⚠️ **El gateway SIEMPRE devuelve SSE** (`data: {...}` chunks), aunque no pidas `stream:true`. Parsear con jq directo sobre la respuesta da `parse error`. Script correcto: concatenar `delta.content` de cada chunk `^data:`. Algunos modelos (ej. `opencode-zen/north-mini-code-free`) emiten `reasoning_details` antes del content — con max_tokens bajos (40) el content sale VACÍO. Usar max_tokens ≥200.

⚠️ **xargs -P 4 satura el gateway**: north-mini-code-free dio 0/3 EMPTY bajo carga paralela y 5/5 ok en serie. Benchmarks MoA deben correr seriales (P 1) o los EMPTY son falsos positivos.

p50 por modelo (3 runs seriales, max_tokens 200, prompt trivial "Hola"):

| Modelo | p50 | Notas |
|---|---|---|
| `kiro/deepseek-3.2` | 0.91s | outlier 10s en 1/3 |
| `kiro/qwen3-coder-next` | 0.95s | varianza alta (0.7-5.0s) |
| `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | 1.00s | estable, sorprendentemente rápido |
| `kiro/glm-5` | 1.10s | outlier 29s en pass paralelo |
| `opencode-zen/nemotron-3-ultra-free` | 1.42s | outlier 16s 1/3 |
| `kiro/claude-sonnet-4.5` | 1.71s | estable 1.7-1.8s |
| `opencode-zen/north-mini-code-free` | 4.92s | 3-9s, cae bajo carga paralela |
| `nvidia/z-ai/glm-5.2` | 5.03s | lento estable 4.6-6.1s, outlier 21s |
| `nvidia/deepseek-ai/deepseek-v4-pro` | 5.40s | 1.3-11.4s, muy variable |

Todos los kiro/* y nvidia/* listados responden ok 3/3 en serie (sin 401 ni 404).

Script listo: `scripts/bench_omniroute.sh` — replica este benchmark (SSE-aware, serial, max_tokens 200, 3 runs). Uso: `bash scripts/bench_omniroute.sh [modelo...]`; env: MAX_TOKENS, TIMEOUT_S, RUNS, GATEWAY.

## Antigravity provider (free Gemini/Claude) — MUCH faster than auto/*

Antigravity is an OAuth provider connected by default in OmniRoute; no API key needed. Its concrete models are free and respond in **0.03–1.8 s** vs 3.8–45 s for `auto/*` aliases. Prefer them for any MoA preset:

```bash
# list all antigravity models
curl -s localhost:20128/v1/models | jq -r '.data[].id' | grep '^antigravity/' | sort
```

Measured (2026-08-01, single call, max_tokens 20, gateway local):

| Model | Latency | Role |
|---|---|---|
| `antigravity/claude-sonnet-4-6-high` | **0.03 s** | aggregator (fastest) |
| `antigravity/claude-opus-4-6-thinking-high` | 0.81 s | reasoning reference |
| `antigravity/gemini-2.5-flash-thinking` | 0.92 s | fast reasoning ref |
| `antigravity/gemini-2.5-flash-lite` | 1.03 s | eco ref |
| `antigravity/gemini-3.6-flash-low` | 1.36 s | coding ref |
| `antigravity/gemini-3.6-flash-medium` | 1.42 s | general ref |
| `antigravity/gemini-3.6-flash-high` | 1.80 s | quality ref |

Also free: `gemini-3.5-flash-low` / `-extra-low`, `gemini-3.1-pro-low` / `-flash-lite` / `-flash-image` (vision), `gemini-pro-agent`, `gemini-3-flash-agent`. All advertise 1M context except `gpt-oss-120b-medium` (131k). `antigravity/gemini-3.1-flash-image` has `context_length: null`.

⚠️ Verification pitfall: models served by **native Hermes providers** (`opencode-zen/*`, `openrouter/*`, `nous/*`, `opencode-go/*`) are NOT in OmniRoute's `/v1/models` — a "FALTA" hit for those is expected, not an error. Only `custom`-provider models (base_url `localhost:20128/v1`) must exist there.

## MoA preset architecture (final, 3 presets, tuned 2026-08-01)

```yaml
moa:
  default_preset: default   # agentic general
  active_preset: default
  presets:
    default:                # general agentic (balanced)
      reference_models:
        - model: antigravity/gemini-3.6-flash-medium
          provider: custom
          base_url: http://localhost:20128/v1
        - model: deepseek-v4-flash-free          # native provider
          provider: opencode-zen
        - model: nvidia/nemotron-3-super-120b-a12b:free   # native provider
          provider: openrouter
      aggregator:
        provider: deepseek   # official API (api.deepseek.com), NOT opencode-go — see failures below
        model: deepseek-v4-flash
      enabled: true
      reference_max_tokens: 600
    eco:                    # simple tasks, minimal cost/latency
      reference_models:
        - model: antigravity/gemini-2.5-flash-lite
          provider: custom
          base_url: http://localhost:20128/v1
        - model: mimo-v2.5-free
          provider: opencode-zen
      aggregator:
        provider: custom
        base_url: http://localhost:20128/v1
        model: antigravity/gemini-2.5-flash-thinking
      enabled: true
      reference_max_tokens: 400
    omni:                   # heavy coding
      reference_models:
        - model: antigravity/claude-opus-4-6-thinking-high
          provider: custom
          base_url: http://localhost:20128/v1
        - model: antigravity/gemini-3.6-flash-high
          provider: custom
          base_url: http://localhost:20128/v1
        - model: antigravity/gemini-3.6-flash-low
          provider: custom
          base_url: http://localhost:20128/v1
      aggregator:
        provider: custom
        base_url: http://localhost:20128/v1
        model: antigravity/claude-sonnet-4-6-high
      enabled: true
      reference_max_tokens: 1200
```

Role assignment: fast models → parallel reference/executor workers; reasoning models (`-thinking`, claude) → aggregator/synthesizer. Slow aliases (free/chat/coding) kill the whole MoA round-trip — never put them in the loop.

## Known failures & fixes

- **Antigravity 503 `chat_admission_capacity`** on reference models: transient upstream capacity (Google/Antigravity side), NOT a config error. Retry later or switch preset. Only 1-2 of N references failing still lets the MoA complete (aggregator synthesizes from survivors).
- **`opencode-go` aggregator → `[404]: Antigravity upstream error`**: opencode-go provider became unusable for MoA aggregation. **Fix:** point the MoA aggregator at the official DeepSeek API instead:
  ```yaml
  moa:
    aggregator: {model: deepseek-v4-flash, provider: deepseek}   # + same under presets.<name>.aggregator
  ```
  Verify `deepseek-v4-flash` exists on `api.deepseek.com` (returns HTTP 200 ~1.1s, model name is real). The `deepseek` provider reads `DEEPSEEK_API_KEY` from `~/.hermes/.env`. Apply to BOTH the global `moa.aggregator` and each preset's `aggregator` — they are independent and both defaulted to opencode-go.

## Trimming the OmniRoute model list (797 → 50)

`custom_providers[0].models` in config.yaml balloons to ~800 entries (ali/alibaba duplicates, embeddings, TTS, ASR, image-gen, rerank, nvidia junk). Hermes loads them all on validation — noise. Trim to what's actually used:
- Keep: all `auto/*` routing aliases (38), `combo-coding`, `Kimi Coding`, the antigravity models referenced by MoA presets, and any other provider models in active use (e.g. `kiro/deepseek-3.2`, `kiro/glm-5`, `kiro/qwen3-coder-next`).
- Drop: `ali/`↔`alibaba/` duplicate pairs, `aug/*`, `tllm/*`, `ddgw/*`, `felo/*`, `oc/*`, `no-think/*`, embeddings/rerank/ASR/TTS/image/video models.
- After trimming, verify every `provider: custom` model referenced by MoA presets still exists in the list (script: collect preset models, diff against `models`).
- Backup config first (`config.yaml.bak.<ts>_pre-cleanup`); result ~11KB vs 47KB.

## Asignar un combo OmniRoute a un perfil Hermes

Cada perfil Hermes (`~/.hermes/profiles/<name>/config.yaml`) tiene config PROPIA — NO hereda `custom_providers` del config principal. Para que un perfil use un combo del gateway local:

```bash
hermes --profile <name> config set model.provider custom
hermes --profile <name> config set model.base_url http://localhost:20128/v1
hermes --profile <name> config set model.api_key '${OMNIROUTE_API_KEY}'
hermes --profile <name> config set model.default <combo-id>   # ej. dev-back, manager
hermes --profile <name> gateway restart                        # toma efecto al reiniciar
```

Patrón validado 2026-08-03 (4 perfiles, todos respondiendo con su combo):
| Perfil | Combo |
|---|---|
| coder-back | dev-back |
| coder-front | dev-front |
| devops-chief | manager |
| reseach | search-dev |

Verificación: `hermes --profile <name> chat -q 'Responde solo con tu nombre de modelo interno' -Q` → el combo responde con su id. Y `hermes profile list` muestra el combo como Model.

⚠️ Un perfil que apunte a opencode-zen con fallback a OpenRouter fallará con billing error si el combo custom no se aplica (el fallback se dispara antes de llegar al gateway). Reiniciar el gateway SIEMPRE tras cambiar model.* en un perfil.

## Combo Agenticus

- El combo `Agenticus` (así, con A mayúscula) existe en el gateway, 21 modelos, strategy `priority`, `enabled: true`.
- Cadena tope: `opencode-zen/deepseek-v4-flash-free` → `kiro/qwen3-coder-next` → `kiro/glm-5` → `ollama-cloud/gemma4:31b` → `hf/deepseek-ai/DeepSeek-V3` → ...
- Medido 2026-08-18: 3/3 OK, p50 **0.66s**, upstream activo que respondió en los 3 runs: `ollama-cloud/gemma4:31b` (priority 4 — los de arriba fallaron o el scorer los saltó).
- **2026-08-18: promovido a default del perfil principal** (config.yaml: `model.provider: custom`, `base_url: http://localhost:20128/v1`, `api_key: ${OMNIROUTE_API_KEY}`, `default: Agenticus`). Verificado end-to-end: `hermes chat -q ... -Q` responde `Agenticus`.
- ⚠️ Sesión TUI abierta NO toma el nuevo default (gateway embebido con modelo viejo); aplica a sesiones nuevas o con `/model`.

## Fallback Agenticus para perfiles con combo OmniRoute

Formato de `fallback_providers` para un combo OmniRoute (validado 2026-08-03 con prueba de fallo real):

```yaml
fallback_providers:
  - provider: custom
    model: Agenticus
    base_url: http://localhost:20128/v1
    key_env: OMNIROUTE_API_KEY
```

- El combo `Agenticus` (así, con A mayúscula) existe en el gateway y responde ~3.3s.
- `key_env` se resuelve vía `get_secret` (fallback_config.py `resolve_entry_api_key`); también acepta `api_key` inline o `api_key_env` como alias.
- Aplicar a: config principal (default) y cada perfil: `~/.hermes/profiles/<name>/config.yaml`.
- Editar con python replace quirúrgico (no yaml.dump — destruye comentarios). Para el default: reemplazar `fallback_providers: []`. Para perfiles sin fallback: insertar tras la línea `api_key: ${OMNIROUTE_API_KEY}`.
- **Prueba de fallback**: setear temporalmente `model.default` a un id inexistente (`hermes --profile X config set model.default modelo-inexistente-xyz`), reiniciar gateway, correr `chat -q 'Responde solo con tu nombre de modelo interno' -Q` → debe responder `Agenticus`. Restaurar default y reiniciar.
- El fallback solo se registra en logs cuando el primario falla (429/503/connection) — no ver "fallback" en gateway.log en arranque normal es esperado.

## Conflicto api_server (puerto 8642) entre default y perfiles

Síntoma: el gateway del perfil **default** muere con `status=78/CONFIG`, log: `api_server: Port 8642 already in use` (non-retryable startup conflict). Los gateways de perfiles secundarios en cambio lo parkean ("fatally misconfigured and parked... Staying alive") y siguen vivos.

Causa: todos los `.env` (default + perfiles) tienen `API_SERVER_ENABLED=true` + `API_SERVER_KEY`, así que **cada gateway intenta bindear 0.0.0.0:8642**; solo el primero lo gana.

Fix (perfiles secundarios NO bindean su propio api_server — el default se queda el listener):
```yaml
# en ~/.hermes/profiles/<name>/config.yaml
platforms:
  api_server:
    enabled: false
```
Orden: editar los 4 perfiles → `hermes --profile <p> gateway restart` (liberan 8642) → `hermes gateway start` (default toma 8642). Verificar: `ss -tlnp | grep 8642` → lo tiene el default; `hermes profile list` → default + 4 perfiles `running`.

## Editing config.yaml

`patch`/`write_file` tools are refused on `~/.hermes/config.yaml` (security guard: "Refusing to write to Hermes config file"). Edit via terminal: backup → python (exact multi-line anchor regex, or yaml.dump round-trip for big nested blocks) → verify `yaml.safe_load` + grep the surrounding block. See user-owned skills `config-backup-rotation` and `hermes-config-management` for the full procedure.
