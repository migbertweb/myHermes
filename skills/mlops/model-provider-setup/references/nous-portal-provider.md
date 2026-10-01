# Nous Portal Provider & Free Models

Reference for using Nous Portal (portal.nousresearch.com) as a provider in Hermes Agent — OAuth-based access to free and discounted models.

## What is Nous Portal?

Nous Portal is a subscription-based provider from Nous Research. Unlike API-key providers (DeepSeek, OpenRouter, etc.), it uses **OAuth authentication** managed through the Hermes CLI.

- **300+ models** from multiple labs
- **Free models** (like Step 3.7 Flash for 30 days)
- **Tool Gateway** — bundled web search, scraping, image generation, browser use
- **10% off token-billed providers** for subscribers

## Login & Setup

```bash
# One-shot setup: OAuth + provider config
hermes setup --portal

# Or manually log in
hermes portal login

# Check status
hermes portal info
hermes portal status

# Open subscription page in browser
hermes portal open
```

The login opens your browser for Google OAuth. Once authenticated, the `nous` provider becomes available.

**⚠️ Side effect:** `hermes portal login` automatically changes `model.provider` to `nous` and `model.default` to the Portal's default model (currently `stepfun/step-3.7-flash:free`). If you want to keep your previous provider as main, you'll need to switch back afterward with `hermes config set model.provider <original>`.

## Provider slug

Once logged in, use `nous` as the provider slug everywhere:

```yaml
# Main model
model:
  provider: nous
  default: stepfun/step-3.7-flash:free   # :free suffix is required

# MoA references
- provider: nous
  model: stepfun/step-3.7-flash:free

# Auxiliary tasks
auxiliary:
  web_extract:
    provider: nous
    model: stepfun/step-3.7-flash:free
```

## Step 3.7 Flash — Free via Portal (30 days)

StepFun's flagship agentic model, free through Nous Portal:

| Attribute | Value |
|-----------|-------|
| Architecture | 198B MoE (11B active/token) |
| Context | **256K tokens** |
| Vision | Text + image + video |
| SWE-Bench Pro | **56.3%** (beats DeepSeek V4 Flash) |
| Tool calling | 100% success rate |
| Release | May 29, 2026 |
| License | Apache 2.0 (open weights) |
| Free duration | 30 days via Nous Portal |

### Benchmark highlights

| Benchmark | Step 3.7 Flash | DeepSeek V4 Flash |
|-----------|---------------|-------------------|
| SWE-Bench Pro | 56.3% | ~51% |
| ClawEval 1.1 | **67.1** (#1) | — |
| GPQA Diamond | 80.9% | — |

### Availability across providers

| Source | Slug | Price |
|--------|------|-------|
| **Nous Portal** (free) | `stepfun/step-3.7-flash` | **Free** (30 days) |
| **OpenRouter** (paid) | `stepfun/step-3.7-flash` | ~$0.0002/M prompt, ~$0.00115/M completion |
| **OpenCode Zen** | `stepfun/step-3.7-flash` (if available) | Check OpenCode Zen catalog |

> **Note:** The `:free` suffix variant (`stepfun/step-3.7-flash:free`) does NOT exist on OpenRouter — that slug returns a 402 error. The free version is only available through Nous Portal.

## Comparison Table: Free Model Sources

| Source | Auth | Models | Rate limits | Best for |
|--------|------|--------|-------------|----------|
| **Nous Portal** | OAuth | Step 3.7 Flash (free), 300+ paid | Depends on plan | Free agentic model for 30 days |
| **OpenRouter** (`:free`) | API key | 26+ free models | 20 req/min, 200 req/day | MoA references, vision, aux tasks |
| **OpenCode Zen** | API key | 6+ free models (dsv4-flash-free, mimo-free, etc.) | Moderate | MoA agentic references, aggregation |

## Using Portal models in MoA

```yaml
moa:
  presets:
    portal:
      reference_models:
        - provider: nous
          model: stepfun/step-3.7-flash:free
        - provider: opencode-zen
          model: nemotron-3-ultra-free
      aggregator:
        provider: nous
        model: stepfun/step-3.7-flash:free
      enabled: true
      reference_max_tokens: 600
```

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `hermes portal info` shows "not logged in" | Never authenticated | Run `hermes portal login` |
| `provider: nous` returns auth error | OAuth token expired | Re-run `hermes portal login` |
| Model returns 404 | Model name wrong or not available via Portal | Check `hermes portal info` for available models |
| Free model stopped working | 30-day promo ended | Switch to paid version via Portal or another provider |
