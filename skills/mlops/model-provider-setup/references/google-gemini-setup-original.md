# google-gemini-setup (original content — absorbed into model-provider-setup)

Google Gemini provider setup skill. Covered: API key setup, config.yaml, supported models (2.5 Pro, 2.0 Flash, 1.5 series), Gemini-specific features (native vision, long context, structured output, code execution), and pitfalls. Full original content at 8KB. Key patterns now in `model-provider-setup` section 3.

## Key preserved patterns
- GEMINI_API_KEY env var (not GOOGLE_API_KEY)
- Config: providers.gemini.api_key, default_model
- Models: gemini/gemini-2.5-pro-exp-03-25, gemini/gemini-2.0-flash
- Features: native vision, 1M context, structured output
