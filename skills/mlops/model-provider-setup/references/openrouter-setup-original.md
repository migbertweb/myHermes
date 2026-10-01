# openrouter-setup (original content — absorbed into model-provider-setup)

OpenRouter provider setup skill. Covered: API key setup, config.yaml configuration, supported models, rate limits, and troubleshooting. Full original content at 6KB. Key patterns now in `model-provider-setup` section 1.

## Key preserved patterns
- OPENROUTER_API_KEY env var
- Config: providers.openrouter.api_base, api_key, default_model
- test with `hermes test openrouter/...`
- Model naming: openrouter/provider/model-name
