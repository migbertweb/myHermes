# Provider Pricing Comparison

Reference for comparing AI API provider costs when choosing or evaluating providers for Hermes Agent. Captures pricing models, per-token costs, and cost-per-session calculations.

> **Context:** Prices verified June 2026 from official docs. Always re-check before committing to a provider.

---

## Pricing Models

There are two fundamental pricing models for AI APIs:

| Model | How it works | Examples | Key trait |
|---|---|---|---|
| **Prepaid (Pay-as-you-go)** | Recargas saldo, se descuenta por token usado. Sin cargo mensual. | DeepSeek, Google Gemini (paid tier), OpenRouter, OpenCode Zen | Balance no expira, reembolsable |
| **Subscription** | Pago mensual fijo por acceso a modelos con límites | OpenCode Go ($5→$10/mes) | Gasto predecible, pero limitado |

### Prepaid — detalles clave (de la FAQ oficial de DeepSeek)

- **"Your topped-up balance will not expire."** — El saldo no caduca.
- **"Unused balances are refundable."** — Reembolsable si no se usa.
- Se descuenta por token: `expense = tokens × price`.
- Mínimo de recarga típico: ~$2-5 USD (verifica en platform.deepseek.com).

### OpenCode Zen — prepago con curaduría

- $20 prepago (+$1.23 fee de tarjeta) = $21.23 total.
- Recarga automática cuando saldo < $5 (configurable, desactivable).
- Modelos gratuitos incluidos: DeepSeek V4 Flash Free, MiMo Free, Big Pickle, etc.
- Modelos curados y verificados por el equipo de OpenCode.

### OpenCode Go — suscripción mensual

- $5 el primer mes, luego $10/mes.
- Incluye: DeepSeek V4 Flash/Pro, Qwen3.7 Max, Kimi K2.7, GLM-5.2, MiMo, MiniMax.
- **NO incluye Claude ni GPT.**
- Límites generosos pero no ilimitados.

---

## Precios por 1M tokens (USD)

Datos recopilados de las páginas oficiales de precios (Junio 2026).

### DeepSeek (API directa — api.deepseek.com)

| Modelo | Input (cache miss) | Input (cache hit) | Output | Concurrencia |
|---|---|---|---|---|
| **DeepSeek V4 Flash** | **$0.14** | **$0.035** | **$0.28** | 2,500 |
| DeepSeek V4 Pro | $0.435 | $0.10875 | $0.87 | 500 |

- Cache hit = 75% off miss price (DeepSeek official policy: $0.14 × 0.25 = $0.035).
- Contexto: 1M tokens, Max output: 384K tokens.
- Soporta tool calls, JSON output, FIM, thinking mode.

> **⚠️ Warning: Hermes-provisioned keys have DIFFERENT cache pricing.**
> If you use a Hermes-provided DeepSeek API key (e.g. through the desktop app's built-in key), the cache hit price may be dramatically lower than DeepSeek's official $0.035/M. For example, Hermes' negotiated cache hit for flash has been observed at **$0.0028/M** — 12.5x cheaper than DeepSeek direct. This is **NOT** standard DeepSeek API pricing. When evaluating whether to switch from a Hermes-managed key to your own DeepSeek direct key, always recalculate at the official $0.035/M cache hit price. The difference can flip a cost-benefit analysis: what costs ~$5-6/mo via Hermes may cost ~$15-25/mo via DeepSeek direct at similar volume.

### Google Gemini (ai.google.dev/pricing)

| Modelo | Input | Output | Cache hit |
|---|---|---|---|
| **Gemini 2.5 Flash-Lite** | **$0.10** | **$0.40** | $0.01 |
| Gemini 2.5 Flash | $0.30 | $2.50 | $0.03 |
| Gemini 3 Flash | $0.50 | $3.00 | $0.05 |
| Gemini 2.5 Pro | $1.25 | $10.00 | $0.125 |
| Gemini 3.5 Flash | $1.50 | $9.00 | $0.15 |

- Free tier disponible: límites generosos, contenido usado para mejorar productos.
- Batch API: 50% descuento sobre precio estándar.

### OpenCode Zen (opencode.ai/zen)

Mismos precios que los proveedores directos para algunos modelos, markup en otros.

| Modelo | Input | Output | Cache hit |
|---|---|---|---|
| **DeepSeek V4 Flash** | **$0.14** | **$0.28** | $0.028 |
| DeepSeek V4 Pro | $1.74 | $3.48 | $0.145 |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $0.30 |
| Claude Opus 4.8 | $5.00 | $25.00 | $0.50 |
| Gemini 3.5 Flash | $1.50 | $9.00 | $0.15 |
| GPT 5.4 Mini | $0.75 | $4.50 | $0.075 |
| Qwen3.7 Max | $2.50 | $7.50 | $0.50 |
| MiniMax M2.7 | $0.30 | $1.20 | $0.06 |

- Modelos gratuitos: DeepSeek V4 Flash Free, MiMo-V2.5 Free, Big Pickle, etc.
- 4.4% + $0.30 fee de tarjeta en cada transacción (trasladado al costo).

### OpenRouter (openrouter.ai)

- **Pay-as-you-go** con 5.5% de platform fee sobre el precio del modelo.
- DeepSeek V4 Flash via OpenRouter ≈ $0.1477 input / $0.2954 output.
- Free tier: 25+ modelos gratuitos, 50 req/día.
- Más de 400 modelos disponibles. Ideal para switchear entre providers.
- **Sin cache hit pricing** — siempre paga el precio completo.

### Ollama (local)

- **Gratis.** Sin costo de API.
- Requiere hardware: GPU con 24GB+ para modelos competitivos (Qwen 3.5 70B, etc.).
- Modelos locales no compiten con cloud para tareas de agente complejas.

---

## Costo por sesión de Hermes Agent

El cálculo práctico: ¿cuánto cuesta CADA conversación/turno en Hermes?

### Fórmula

```
costo_sesión = (tokens_in × precio_in) + (tokens_out × precio_out)
```

### Estimación por tipo de uso

| Tipo de sesión | Input típico | Output típico | DeepSeek V4 Flash | Claude Sonnet 4.6 (Zen) |
|---|---|---|---|---|
| Consulta simple | 4K | 1K | **$0.00084** | $0.027 |
| Sesión normal de agente | 15K | 5K | **$0.00350** | $0.120 |
| Sesión pesada (gran contexto) | 50K | 10K | **$0.00980** | $0.300 |
| Análisis de código grande | 200K | 20K | **$0.03360** | $1.200 |

### DeepSeek V4 Flash: duración estimada de $10

| Ritmo de uso | Sesiones/día | $10 dura |
|---|---|---|
| Ligero (unas docenas de consultas) | ~20 | **~3-4 meses** |
| Moderado (uso de agente varias horas) | ~50 | **~2 meses** |
| Power user (Hermes full-time, muchas automatizaciones) | ~150+ | **~2-3 semanas** |

### Lo que NO está incluido en estos cálculos

- **Cache hits**: DeepSeek direct ofrece cache hit a $0.035/M (4x más barato que miss). Sin embargo, Hermes-provisioned keys pueden tener cache hits tan baratos como $0.0028/M (50x vs miss). (system prompts, contextos similares), el costo real es mucho menor.
- **Context caching**: Gemini cobra $1.00/1M tokens/hora por almacenamiento en caché.
- **Fallos y reintentos**: algunos providers cobran aunque la llamada falle.
- **Costos de auxiliary tasks**: Hermes usa modelos secundarios para compresión, visión, títulos de sesiones, etc.
- **MoA (Mixture of Agents)**: cada ciclo MoA ejecuta N referencias + 1 agregador = 3 llamadas pagadas por turno con el preset `eco`. Si el agregador es `deepseek-v4-pro` (OpenRouter, ~$0.44/M input), el costo por turno MoA puede ser 10-50x mayor que una consulta simple. Ver `references/moa-cost-optimization.md` para rutear referencias y agregador a modelos gratuitos de opencode-zen.

---

## Estrategias de ahorro

1. **DeepSeek V4 Flash como daily driver** — calidad excelente para coding agents al menor costo del mercado.
2. **Gemini free tier como auxiliary** — ya configurado, sin costo para tareas secundarias.
3. **DeepSeek directo, no via intermediario** — OpenRouter añade 5.5%, OpenCode-Zen tiene markup en modelos no-DeepSeek.
4. **Modelos caros solo cuando se necesitan** — Claude/GPT para tareas complejas, DeepSeek para el día a día.
5. **Cache hit de DeepSeek direct** — contexto repetido (system prompts, skills) se beneficia del precio 4x menor ($0.035/M vs $0.14/M). Con Hermes-provisioned keys, el ahorro puede ser 50x ($0.0028/M vs $0.14/M).
6. **Batch API de Gemini** — 50% descuento si las tareas pueden ser asíncronas.

---

## Matriz de decisión rápida

| Si quieres... | Elige... |
|---|---|
| Máximo valor para coding agents | DeepSeek Direct API (prepago) |
| Algo gratis que ya tienes configurado | Google Gemini (free tier) |
| Acceso a Claude sin múltiples APIs | OpenCode Zen ($20 prepago) |
| Gasto mensual predecible | OpenCode Go ($10/mes) |
| Switchear entre 400+ modelos | OpenRouter (pay-as-you-go + 5.5%) |
| Privacidad total, sin costo API | Ollama local (requiere GPU) |
