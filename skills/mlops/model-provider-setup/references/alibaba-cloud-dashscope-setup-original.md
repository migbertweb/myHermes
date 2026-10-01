# alibaba-cloud-dashscope-setup (original content — absorbed into model-provider-setup)

Alibaba Cloud DashScope provider setup skill. Covered: API key setup, config.yaml, supported models (Qwen Max/Plus/Turbo, QwQ preview), and pitfalls (mainland China registration, model naming differences, whitelist requirements). Full original content at 3KB. Key patterns now in `model-provider-setup` section 4.

## Key preserved patterns
- DASHSCOPE_API_KEY env var
- Config: providers.dashscope.api_key, default_model
- Models: dashscope/qwen-max, dashscope/qwen-plus, dashscope/qwen-turbo
- Pitfall: mainland China phone for registration
