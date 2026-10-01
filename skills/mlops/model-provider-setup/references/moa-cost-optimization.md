# MoA (Mixture of Agents) Cost Optimization

Reference for reducing MoA costs in Hermes by routing reference and aggregator calls through free-tier opencode-zen models instead of paid OpenRouter calls.

---

## How MoA Consumes Tokens

Each MoA cycle makes **N+1 API calls** per user turn:
- **N reference models** — each generates a diverse perspective on the query
- **1 aggregator model** — combines/selects the best output from references

The Hermes `eco` preset (default: `moa.default_preset: eco`) uses 2 references + 1 aggregator = **3 paid calls per turn**.

## Default eco Preset — Cost Breakdown

```yaml
# ~/.hermes/config.yaml — default eco preset
moa:
  default_preset: eco
  presets:
    eco:
      reference_models:
        - provider: openrouter          # paid — deepseek/deepseek-v4-flash
          model: deepseek/deepseek-v4-flash
        - provider: openrouter          # paid — minimax/minimax-m3
          model: minimax/minimax-m3
      aggregator:
        provider: openrouter            # paid — deepseek/deepseek-v4-pro (expensive!)
        model: deepseek/deepseek-v4-pro
      reference_max_tokens: 600
      max_tokens: 4096
```

| Role | Model | Cost (input/Mtok) | Cost per turn (est.) |
|------|-------|-------------------|---------------------|
| Reference 1 | DeepSeek V4 Flash (OpenRouter) | ~$0.15 | $0.01-0.04 |
| Reference 2 | MiniMax M3 (OpenRouter) | ~$0.20 | $0.01-0.04 |
| Aggregator | DeepSeek V4 Pro (OpenRouter) | ~$0.44 | **$0.10-0.50+** |
| **Total per MoA turn** | | | **$0.12-0.58+** |

A heavy session (30+ turns) with MoA eco can cost **$3.60-17.40+** just for MoA calls alone.

## Optimization: Switch to opencode-zen Free Models

Switch references and aggregator to opencode-zen's free-tier models. The main operator (conversation model) stays on OpenRouter.

### Available Free Models (opencode-zen)

| Model Slug | Notes |
|------------|-------|
| `deepseek-v4-flash-free` | Same architecture as paid Flash, free tier |
| `mimo-v2.5-free` | MiMo v2.5 — good reference diversity |
| `nemotron-3-ultra-free` | Nemotron 3 Ultra — strong aggregator quality |
| `north-mini-code-free` | Lightweight coding ref |
| `minimax-m3-free` | Free tier of MiniMax M3 |
| `qwen3.6-plus-free` | Free tier of Qwen 3.6 Plus |

### Recommended Config

```yaml
moa:
  default_preset: eco
  presets:
    eco:
      enabled: true
      reference_models:
        - provider: opencode-zen          # free
          model: deepseek-v4-flash-free
        - provider: opencode-zen          # free
          model: mimo-v2.5-free
      aggregator:
        provider: opencode-zen            # free
        model: deepseek-v4-flash-free     # flash is enough for aggregation
      reference_max_tokens: 600
      max_tokens: 4096
```

**Why flash for aggregator?** V4 Pro as aggregator is overkill for most queries — it's combining short (600 tok) reference outputs. Flash handles this fine and is free on opencode-zen.

| After | Cost |
|-------|------|
| 3 calls via opencode-zen free | **$0.00** |

### Alternative Aggregator Choices

| Model | Notes |
|-------|-------|
| `deepseek-v4-flash-free` | Balanced — recommended default |
| `mimo-v2.5-free` | Works when references are diverse |
| `nemotron-3-ultra-free` | Better reasoning, still free |
| `gemini-3-flash` | opencode-zen default aux model, good quality |

## Additional Cost Savings

### web_extract auxiliary (optional)

The `auxiliary.web_extract` task also calls OpenRouter `deepseek/deepseek-v4-flash` by default. Switch to free:

```yaml
auxiliary:
  web_extract:
    provider: opencode-zen
    model: deepseek-v4-flash-free
    timeout: 360
```

### Compression auxiliary (auto)

`auxiliary.compression` with `provider: auto` falls back to the main provider (OpenRouter). To save:

```yaml
auxiliary:
  compression:
    provider: opencode-zen
    model: deepseek-v4-flash-free
    timeout: 120
```

## Requirements

1. `OPENCODE_ZEN_API_KEY` set in `~/.hermes/.env`
2. `opencode-zen` is a built-in provider (no `providers:` entry needed in config.yaml)
3. Free-tier models may have rate limits — acceptable for MoA auxiliary tasks

## Pitfalls

- **Free-tier rate limits**: If MoA cycles too fast, you may hit OpenCode Zen free-tier caps. The eco preset with `reference_max_tokens: 600` keeps each call lightweight.
- **Aggregator quality**: If free-tier aggregator gives worse results than V4 Pro, switch to `nemotron-3-ultra-free` which has stronger reasoning.
- **Provider alias**: Must use canonical slug `opencode-zen`, not the alias `opencode` — otherwise auxiliary resolution silently fails (see `references/builtin-provider-resolution.md`).
- **Main operator stays paid**: This optimization only affects MoA calls. The main conversation model still costs via its configured provider.
