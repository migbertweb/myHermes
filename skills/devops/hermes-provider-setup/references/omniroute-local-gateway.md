# OmniRoute — Local AI Gateway Provider

**OmniRoute** (`https://github.com/diegosouzapw/OmniRoute`) is a free open-source AI gateway
that aggregates 250+ upstream providers (90+ free) through a single OpenAI-compatible endpoint.
Runs locally on `localhost:20128`.

## Provider Config

Always use `custom_providers:` — not `providers:` — for OmniRoute (and any gateway/proxy).

### Without API key (standard local access):

```yaml
custom_providers:
  - name: omniroute
    base_url: http://localhost:20128/v1
    # key_env omitted — local access doesn't need auth
    models:
      auto: {}
      auto/coding: {}
      auto/fast: {}
      auto/cheap: {}
      auto/smart: {}
```

### With API key via key_env (standard API-key auth):

```yaml
custom_providers:
  - name: omniroute
    base_url: http://localhost:20128/v1
    key_env: OMNIROUTE_API_KEY
    models:
      auto: {}
      auto/coding: {}
      auto/fast: {}
      auto/smart: {}
```

This is the recommended approach if your OmniRoute instance requires auth but uses `/v1` as the endpoint (not a URL-embedded key). Add `OMNIROUTE_API_KEY=sk-...` to `~/.hermes/.env`.

### With API key in URL path (VS Code / IDE endpoint):

```yaml
custom_providers:
  - name: omniroute
    base_url: http://localhost:20128/api/v1/vscode/{your-api-key}/v1
    # No key_env needed — the key is baked into the URL path
    models:
      auto: {}
      auto/coding: {}
      auto/fast: {}
      aug/claude-sonnet-4.6: {}
      oc/deepseek-v4-flash-free: {}
      # ... any model ID from the provider's /v1/models endpoint
```

## Model Discovery

OmniRoute exposes 696+ models at `{base_url}/models` in this installation. These model IDs use the format:

### Auto-routing
- `auto` — balanced default
- `auto/coding`, `auto/fast`, `auto/cheap`, `auto/smart` — routing variants

### Kiro provider (`kr/`) — Agent-optimized models
Base models:
- `kr/auto`, `kr/auto-thinking`
- `kr/deepseek-3.2`, `kr/glm-5`, `kr/minimax-m2.5`, `kr/qwen3-coder-next`

**Agentic variants** (optimized for tool calling, long context, multi-step reasoning):
- `kr/deepseek-3.2-agentic`, `kr/deepseek-3.2-thinking-agentic`
- `kr/glm-5-agentic`, `kr/glm-5-thinking-agentic`
- `kr/minimax-m2.1-agentic`, `kr/minimax-m2.1-thinking-agentic`
- `kr/minimax-m2.5-agentic`, `kr/minimax-m2.5-thinking-agentic`
- `kr/qwen3-coder-next-agentic`, `kr/qwen3-coder-next-thinking-agentic`
- `claude-haiku-4.5-agentic__provider_kr`
- `claude-sonnet-4-agentic__provider_kr`, `claude-sonnet-4.5-agentic__provider_kr`
- `claude-sonnet-4-thinking-agentic__provider_kr`, `claude-sonnet-4.5-thinking-agentic__provider_kr`
- `claude-haiku-4.5-thinking-agentic__provider_kr`

**⚠️ Los aliases `-agentic` NO funcionan en esta instalación (verificado 2026-08-01).** Devuelven:
```
[kiro/<modelo>-agentic] Kiro agentic aliases are not supported. The '-agentic' suffix did not change the upstream request; select a real Kiro model instead. (reset after 5s)
```
Usar los modelos base reales (`kiro/qwen3-coder-next`, `kiro/glm-5`, `kiro/deepseek-3.2`) — la vieja recomendación de usar `-agentic` quedó obsoleta en OmniRoute v3.8.49.

### OpenCode (`oc/`) — Free tier models
- `oc/deepseek-v4-flash-free`, `oc/minimax-m3-free`, `oc/nemotron-3-super-free`, `oc/qwen3.6-plus-free`

### Augment (`aug/`) — Premium provider
- `aug/claude-sonnet-4.6`, `aug/claude-opus-4.6`, `aug/claude-haiku-4.5`
- `aug/gpt-5.5-high`, `aug/gpt-5.4-high`
- `aug/gemini-3.1-pro`, `aug/gemini-3.0-flash`

### HuggingChat
- `huggingchat/deepseek-ai/DeepSeek-V4-Flash`, `huggingchat/deepseek-ai/DeepSeek-V4-Pro`
- `huggingchat/Qwen/Qwen3.6-35B-A3B`
- `huggingchat/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`
- `huggingchat/moonshotai/Kimi-K2.7-Code`

### TLLM
- `tllm/CLAUDE_4_6_OPUS`, `tllm/CLAUDE_4_6_SONNET`
- `tllm/GPT_5`, `tllm/GPT_5_4`, `tllm/GPT_o4_mini`
- `tllm/gemini_3_pro`, `tllm/gemini_2_5_pro`

### Other
- `pepper/pepper-1`

**List all models**: `curl {base_url}/models` (works without auth when running locally)

## Model Discovery Caveats

- **TUI model picker doesn't probe custom endpoints**: The TUI `/model` dialog uses `probe_custom_providers=False` to stay snappy. Models from OmniRoute (or any custom provider) won't appear in the TUI picker unless the provider is currently active. Workarounds:
  1. Run `hermes model` from the terminal (outside TUI) — probes all custom endpoints
  2. Switch directly via `/model custom:omniroute:<model_id>` inside TUI (bypasses the picker)
  3. List models explicitly in `models:` under the provider entry in config.yaml
- **Model count varies**: The `/v1/models` output depends on which upstream providers are configured in the OmniRoute dashboard. Add/remove upstreams there and the model list updates automatically.
- **Auto-routing models** (`auto/*`, `kr/auto`, etc.) are always available regardless of upstream config — they route to the best available upstream at request time.

## Usage

```bash
# One-shot test (no auth / local)
hermes chat --provider custom:omniroute --model auto -q 'Hello' -Q

# One-shot test (with embedded key)
hermes chat --provider custom:omniroute --model auto -q 'Hello' -Q

# Specific model
hermes chat --provider custom:omniroute --model oc/deepseek-v4-flash-free -q 'Hello' -Q

# Change mid-session
/model custom:omniroute:aug/claude-sonnet-4.6
```

## Combos (custom routing groups)

Combos are named routing groups that bundle multiple models under a single alias with a chosen strategy.

### Create a combo

```bash
omniroute combo list                          # ver combos existentes
omniroute combo create "free-coding" --strategy priority
omniroute combo switch "free-coding"          # activar como default
omniroute combo delete "free-coding"          # eliminar
```

**Strategies**: `priority` (ordered fallback), `weighted`, `round-robin`, `p2c`, `cost-optimized`, `context-optimized`, `least-used`, `auto`, `lkgp`, `fill-first`, `reset-aware`, `strict-random`.

### Asignar modelos al combo

⚠️ **El CLI solo crea el combo con su estrategia. La asignación de modelos individuales se hace exclusivamente desde el dashboard web** (`http://localhost:20128` → Combos → seleccionar combo → agregar nodos).

### Modelos gratis recomendados para un combo `free-coding`

| Prioridad | Modelo | Provider |
|---|---|---|
| 1 | `kiro/deepseek-3.2` | kiro |
| 2 | `kiro/qwen3-coder-next` | kiro |
| 3 | `ali/deepseek-v4-flash` | alibaba |
| 4 | `ali/qwen3.7-flash` | alibaba |
| 5 | `oc/deepseek-v4-flash-free` | opencode |
| 6 | `oc/qwen3.6-plus-free` | opencode |
| 7 | `huggingchat/deepseek-ai/DeepSeek-V4-Flash` | huggingchat |
| 8 | `hf/deepseek-ai/DeepSeek-V3` | huggingface |

Con estrategia `priority`, OmniRoute cae al siguiente solo si el anterior falla o está agotado.

### Usar un combo desde Hermes

```yaml
# config.yaml
model: free-coding
provider: custom:omniroute
```

O mid-session: `/model custom:omniroute:free-coding`

### Inspeccionar combos por API (sin auth)

```bash
curl http://localhost:20128/api/v1/combos | python3 -m json.tool
```

Devuelve los combos con `strategy` y `models[]` **en orden de prioridad**. Útil para verificar el orden de nodos sin entrar al dashboard (dashboard requiere login; el endpoint `/api/v1/combos` responde sin auth local).

### ⚠️ Benchmarking de velocidad: batch ≠ streaming; auto/* es volátil

Medido 2026-08-01 (OmniRoute v3.8.49):

- **`stream:false` mide generación completa; `stream:true` mide TTFT.** Para uso de agente (Hermes streama), lo que importa es TTFT + tok/s de generación, no la latencia batch.
- **Los combos `auto/*` rutearn dinámicamente por request** — un mismo combo puede caer en `claude-haiku-4.5`, `glm-5.2` o `minimax` según disponibilidad. La latencia varía muchísimo entre runs (medido: TTFT de 1.7s a 13.7s en `auto/coding:fast`, 3 corridas). Nunca juzgar un auto/combo por un solo run.
- **Combo con modelo fijo = predictibilidad**: `combo-coding` (→ `kiro/qwen3-coder-next`) dio TTFT estable 1.2-3.9s, mejor para agente que un auto/* más rápido en pico pero errático.
- **Medir latencia real por modelo del combo**: rutear directo a `kiro/<modelo>` (ej. `kiro/qwen3-coder-next`) para aislar cada upstream antes de ordenar prioridades.
- Cabeceras útiles: `x-omniroute-decision` (strategy+provider+latency_ms), `x-omniroute-model`, `x-omniroute-provider`, `x-omniroute-latency-ms`, `x-omniroute-response-cost`.
- Script de benchmark existente: `~/.hermes/scripts/benchmark_omniroute_reasoning.py` (3 corridas, promedio, headers).

### Reordenar prioridad de un combo (verificado 2026-08-01)

- El CLI **no** reasigna nodos: `omniroute combo create` solo crea con estrategia; los nodos se editan en el dashboard web (login).
- Con `strategy=priority`, OmniRoute usa **el primer modelo que responde** — poner el más rápido/confiable primero reduce latencia real del combo. Un modelo lento en 1ª posición condena todo el combo (ej. `kiro/deepseek-3.2` a 46s de generación larga vs `kiro/qwen3-coder-next` a 9s).
- Modelos rotos/lentos se detectan benchmarkeando cada nodo individual; moverlos al final o eliminarlos (ej. `alibaba/qwen3.7-flash` a 28.67s).

### Providers disponibles en esta instalación

```
alibaba     active    # Qwen, DeepSeek via Alibaba Cloud
huggingchat active    # modelos gratis via HuggingChat
huggingface active    # modelos HF directo
kiro        active    # kiro-piro, modelos agentic
longcat     active
nvidia      active    # DeepSeek, modelos NVIDIA
qwen-web    active    # Qwen vía web
mimocode    unknown
opencode    unknown
pollinations credits_exhausted
```

## Notes

- Dashboard at `http://localhost:20128` — add/manage upstream providers there
- OmniRoute proxies through to the best available upstream based on the routing strategy
- Response headers include `x-omniroute-provider` and `x-omniroute-model` showing which upstream served
- Uses streaming by default; Hermes handles SSE→text conversion automatically
- When the API key is in the URL path, you don't need `key_env` in the config — the key is part of the base_url
