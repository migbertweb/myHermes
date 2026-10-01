# OpenCode Provider Config via OmniRoute

Generate an `opencode.json` from the OmniRoute model catalog so OpenCode CLI can use OmniRoute models.

## Setup

### 1. Export API key in shell rc

Add to `~/.zshrc` (or equivalent):

```bash
export OMNIROUTE_API_KEY="sk-..."
```

Source it: `source ~/.zshrc`

### 2. Generate config

```bash
omniroute setup-opencode
```

Fetches live `/v1/models` catalog from OmniRoute and writes `~/.config/opencode/opencode.json`.

## Filter models with `--only`

Full catalog can be 700+ models. Filter with comma-separated substrings:

```bash
# Solo auto-routing + combos
omniroute setup-opencode --only auto,combo

# Solo coding
omniroute setup-opencode --only coding

# Free models
omniroute setup-opencode --only free
```

## API key security

The generator replaces the `omniroute` provider's key with `{env:OMNIROUTE_API_KEY}`. **Other providers** (viernes, ollama, etc.) may get plain-text keys.

Verify after generation:

```bash
python3 -c "
import json
with open('/home/migbert/.config/opencode/opencode.json') as f:
    d = json.load(f)
for name, prov in d.get('provider', {}).items():
    opts = prov.get('options', {})
    if 'apiKey' in opts and not opts['apiKey'].startswith('{env:'):
        print(f'SECURITY: {name} has plain-text apiKey')
"
```

Fix plain-text keys:

```bash
python3 -c "
import json
with open('/home/migbert/.config/opencode/opencode.json') as f:
    d = json.load(f)
for name, prov in d.get('provider', {}).items():
    opts = prov.get('options', {})
    if 'apiKey' in opts and not opts['apiKey'].startswith('{env:'):
        opts['apiKey'] = '{env:OMNIROUTE_API_KEY}'
with open('/home/migbert/.config/opencode/opencode.json', 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
"
```

## Known bug: limit.output missing

The OmniRoute generator (`src/lib/cli-helper/config-generator/opencode.ts`) has a logic bug: when a model has context_length but no max_output_tokens, the `limit` block is created with only context — no output. OpenCode requires limit.output.

### Quick fix on generated JSON:

```bash
python3 -c "
import json
with open('/home/migbert/.config/opencode/opencode.json') as f:
    d = json.load(f)
fixed = 0
for prov in d.get('provider', {}).values():
    for model in prov.get('models', {}).values():
        limit = model.get('limit')
        if limit is not None and 'output' not in limit:
            limit['output'] = 8192
            fixed += 1
with open('/home/migbert/.config/opencode/opencode.json', 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
print(f'Fixed {fixed} models')
"
```

### Permanent fix in generator source:

In `/home/migbert/.npm-global/lib/node_modules/omniroute/src/lib/cli-helper/config-generator/opencode.ts`, replace:

```ts
if (typeof userOutput === "number" || typeof catalogOutput === "number") {
  limit.output = ...
}
```

with:

```ts
limit.output = output;
```

## Provider health check

Combos with dead providers fail silently. Always check provider status:

```bash
curl -s http://localhost:20128/api/providers \
  -H "Authorization: Bearer $OMNIROUTE_API_KEY" \
  | python3 -c "
import json,sys
d = json.load(sys.stdin)
conns = d if isinstance(d, list) else d.get('connections', [])
for c in conns:
    name = c.get('name','?')
    prov = c.get('provider','?')
    err = c.get('lastError','none')
    status = c.get('testStatus','?')
    bo = c.get('backoffLevel',0)
    print(f'{name} ({prov}): status={status}, backoff={bo}, error={err[:80] if err else \"ok\"}')
"
```

### Status signals

| Status | Meaning | Impact |
|--------|---------|--------|
| credits_exhausted | Sin credito/balance | Modelo no funciona |
| forbidden (403) | Sin suscripcion al modelo | No responde |
| backoff > 0 | En espera por rate limit | Latencia/fallos |
| active + no error | Funciona | Confiable |

A combo with N models via one connection is fragile — if that connection dies, all N die together.

## Auto model resolution

OmniRoute auto/* models resolve dynamically per request:

| Model ID | Optimiza para | Notas |
|----------|---------------|-------|
| auto/best-coding | Calidad de codigo | Falla si providers prioritarios estan caidos |
| auto/coding:fast | Baja latencia | Falla si modelos rapidos sin creditos |
| auto/best-reasoning | Razonamiento | Suele ser el mas estable |
| auto/coding:free | Costo cero | Funciona con opencode free tier |

If auto/best-coding or auto/coding:fast fail with "Maximum combo retry limit reached", providers like kiro/alibaba are dead.

**Prefer auto/best-reasoning or auto/coding:free** when kiro/alibaba are down.

## Benchmarking models

Use `templates/model-benchmark.sh` to test multiple models with same prompt:

```bash
bash ~/.hermes/skills/devops/hermes-provider-setup/templates/model-benchmark.sh
```

Edit the MODELOS array at top to change which models to test. Measures total response time, shows resolved model, token usage, and first lines of response.

## Auto vs custom combos

| Feature | auto/* | Custom combo |
|---------|--------|-------------|
| Failover | Automatico entre providers activos | Depende de estrategia |
| Contexto | 1M tokens | Depende del combo |
| Mantenimiento | Cero | Manual |
| Health-aware | Si | No (nodos fijos) |

**Prefer auto/*** for general use.
