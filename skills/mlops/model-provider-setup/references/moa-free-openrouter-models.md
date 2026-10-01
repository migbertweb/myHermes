# Free OpenRouter Models for MoA References

Reference for adding a free OpenRouter model as an additional MoA reference for perspective diversity alongside opencode-zen or paid references.

## Why Add a Free OpenRouter Reference

MoA benefits from model diversity. If both your references use the same provider (e.g., two opencode-zen references), they may produce correlated outputs. Adding a model from a different provider — even a free one — introduces independent reasoning that the aggregator can synthesize.

## Top Picks for MoA References (Jul 2026)

MoA references don't need tool support — they only receive the conversation text and return analysis. Speed matters more than raw quality since the turn waits for the slowest reference.

| Model ID (OpenRouter) | Context | Quality* | Notes |
|-----------------------|---------|----------|-------|
| `xiaomi/mimo-v2-flash:free` | 262K | High | 309B MoE (15B active). #1 open-source on SWE-bench. Strong reasoning/coding. **Best pick** |
| `google/gemma-4-31b-it:free` | 262K | High | Vision+tools. Quality score 65. Good generalist |
| `nvidia/nemotron-3-super-120b-a12b:free` | 1.0M | Good | Huge context (1M). Tools. Quality score 60 |
| `openai/gpt-oss-120b:free` | 131K | Medium | OpenAI. Tools. Quality score 55 |
| `qwen/qwen3-coder:free` | 1.0M | Medium | Coding-focused. 1M context |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1.0M | Good | Strong reasoning. Tools |
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256K | Medium | Lightweight. Fast responses |

*\*Quality scores from CostGoat/theozard benchmarks.*

## MiMo-V2-Flash:free — Deep Dive

Xiaomi MiMo-V2-Flash is a Mixture-of-Experts model (309B total / 15B active). Hybrid attention architecture, hybrid-thinking toggle, 262K context. Free on OpenRouter via `:free` suffix.

- **SWE-bench Verified**: #1 open-source globally
- **Comparable to**: Claude Sonnet 4.5 at ~3.5% the cost (but here it's free)
- **Good for**: Reasoning, coding, agent scenarios — excellent diversity vs opencode-zen models

## Configuration Example

Adding MiMo-V2-Flash as a third reference alongside existing opencode-zen references:

```yaml
moa:
  default_preset: default
  presets:
    default:
      reference_models:
        - provider: opencode-zen
          model: deepseek-v4-flash
        - provider: opencode-zen
          model: deepseek-v4-flash
        - provider: openrouter              # new — free perspective
          model: xiaomi/mimo-v2-flash:free   # free tier
      aggregator:
        provider: opencode-zen
        model: deepseek-v4-flash
      reference_max_tokens: 600
      max_tokens: 4096
      enabled: true
```

## Rate Limits

OpenRouter free tier:
- **20 requests/minute** per model
- **200 requests/day** per model
- No credit card required

For MoA references this is usually fine — each call is short (capped by `reference_max_tokens`). If you hit a 429, the aggregator still gets whatever the other two references returned. MoA does not abort on individual reference failures.

## Complete Free Model List (26 models, Jul 2026)

Full prize list from CostGoat (updated Jul 4, 2026):

| Model | Provider | Context | Capabilities |
|-------|----------|---------|-------------|
| google/gemma-4-31b-it:free | Google | 262K | Vision, Tools |
| nvidia/nemotron-3-super-120b-a12b:free | NVIDIA | 1.0M | Tools |
| openai/gpt-oss-120b:free | OpenAI | 131K | Tools |
| google/gemma-4-26b-a4b-it:free | Google | 262K | Vision, Tools |
| qwen/qwen3-coder:free | Qwen | 1.0M | Tools |
| openai/gpt-oss-20b:free | OpenAI | 131K | Tools |
| nvidia/nemotron-3-nano-30b-a3b:free | NVIDIA | 256K | Tools |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | NVIDIA | 256K | Vision, Tools |
| qwen/qwen3-next-80b-a3b-instruct:free | Qwen | 262K | Tools |
| nvidia/nemotron-nano-12b-v2-vl:free | NVIDIA | 128K | Vision, Tools |
| meta-llama/llama-3.3-70b-instruct:free | Meta | 131K | Tools |
| nvidia/nemotron-nano-9b-v2:free | NVIDIA | 128K | Tools |
| nvidia/nemotron-3-ultra-550b-a55b:free | NVIDIA | 1.0M | Tools |
| poolside/laguna-xs-2.1:free | poolside | 262K | Tools |
| poolside/laguna-xs.2:free | poolside | 262K | Tools |
| poolside/laguna-m.1:free | poolside | 262K | Tools |
| cohere/north-mini-code:free | cohere | 256K | Tools |
| openrouter/free (router) | OpenRouter | 200K | Vision, Tools |
| nousresearch/hermes-3-llama-3.1-405b:free | Nous | 131K | — |
| liquid/lfm-2.5-1.2b-thinking:free | LiquidAI | 33K | Tools, Reasoning |

Source: https://costgoat.com/pricing/openrouter-free-models

## Pitfalls

- **`:free` suffix is required**: `xiaomi/mimo-v2-flash` without `:free` routes as paid
- **Rate limit != model quality**: Top free models rotate. Check OpenRouter's model page for latest availability
- **No tool schema**: MoA references get conversation text only (no system prompt, no tool-call transcript), so tool-support claims on model cards don't matter for reference role
- **Credit balance**: If you have credits on your OpenRouter account and call the model without `:free`, it will route to the paid endpoint