---
name: openrouter-setup
description: "Configure, diagnose, and troubleshoot OpenRouter as a model provider for Hermes Agent. Covers free-tier limitations, BYOK (bring-your-own-key) provider configuration, credential setup, routing restrictions, and model availability."
category: mlops
tags: [openrouter, provider, configuration, troubleshooting, free-tier, byok, routing]
version: 1.0.0
---

# OpenRouter Setup for Hermes Agent

OpenRouter is a unified API gateway for 200+ LLMs. This skill covers configuring it as a Hermes provider and diagnosing common issues.

## Configuration

```bash
# Set the provider and model
hermes config set model.provider openrouter
hermes config set model.default "google/gemma-4-31b-it:free"

# Or use the interactive picker
hermes model
```

The API key goes in `~/.hermes/.env`:
```
OPENROUTER_API_KEY=sk-or-...
```

## Provider Routing Preferences

OpenRouter supports routing preferences sent via `provider` field in the request body:

```yaml
# In config.yaml under provider_routing:
provider_routing:
  only: []           # Only use these providers
  ignore: []         # Skip these providers
  order: []          # Preferred order to try providers
  sort: null         # Sorting strategy
  require_parameters: false
  data_collection: null
```

Hermes passes these via `extra_body.provider` in OpenRouter API requests.

## Free-Tier Limitations

OpenRouter API keys with free tier (`is_free_tier: true`) have **severe routing restrictions**:

1. **Restricted providers**: Free-tier keys can ONLY route through `groq`, `openai`, and `alibaba`.
2. **Most `:free` models fail**: Even models with `:free` suffix and $0 pricing are served through providers like `google-ai-studio`, `venice`, `deepinfra`, `nvidia`, etc. — none of which are accessible to free-tier keys.
3. **BYOK doesn't bypass**: Configuring bring-your-own-key providers in OpenRouter's settings does NOT override the free-tier key restriction.

### Diagnosis

To check if an API key is free-tier:

```python
import urllib.request, json
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/auth/key",
    headers={"Authorization": "Bearer <your_key>"}
)
data = json.loads(urllib.request.urlopen(req).read())
print(data["data"]["is_free_tier"])  # True = restricted
```

### Interpreting Error Metadata

When OpenRouter returns HTTP 404 with `"No allowed providers are available for the selected model"`, the error metadata contains:

```json
{
  "available_providers": ["venice", "deepinfra", "siliconflow", ...],
  "requested_providers": ["groq", "openai", "alibaba"]
}
```

- `available_providers`: Providers that CAN serve this model
- `requested_providers`: What the client (or key tier) restricted to

If `requested_providers` is always `["groq", "openai", "alibaba"]` regardless of what you pass in the `provider` field, the API key is free-tier restricted.

## Solutions When Free-Tier Models Don't Work

### 1. Add Credits to OpenRouter
Even a small amount ($1–$5) upgrades the key from free-tier and unlocks full provider routing. The model costs are typically very low (e.g., `google/gemma-4-31b-it` at ~$0.12/1M tokens).

After adding credits:
- Remove the `:free` suffix from model names (use `google/gemma-4-31b-it` instead of `google/gemma-4-31b-it:free`)
- Or use `openrouter/free` catch-all model (routes to any available free endpoint)

### 2. Use a Different Provider
Switch to a provider that offers free or cheap model access:
- **OpenCode Zen**: Already configured as the user's preferred provider
- **Google AI Studio directly**: Direct API access without OpenRouter's routing restrictions
- **Local inference** via Ollama or llama.cpp

### 3. Raw API Test (Diagnostic Script)

Use this script to test model availability directly against OpenRouter's API:

See `references/diagnostic-openrouter-free-tier.md` for a full reproduction script and example output.

## Known Provider Slugs

When using `provider.only` or `provider.order`, use OpenRouter's internal provider slugs (lowercase, hyphenated):

```
google-ai-studio, open-inference, venice, deepinfra, siliconflow,
novita, parasail, chutes, phala, together, wandb, groq, openai,
alibaba, nvidia, crucible, poolside, liquid, z-ai
```

## Pitfalls

- **`:free` suffix on non-OpenRouter providers**: The `:free` suffix is OpenRouter-specific syntax. Using it with other providers (e.g. Nous Portal) will fail with model-not-found errors. Hermes warns about this.
- **Free-tier BYOK illusion**: Adding your own API keys in OpenRouter provider settings does NOT bypass free-tier key routing restrictions. The key itself must be upgraded.
- **Requested providers override**: Even if you pass `provider.only` or `provider.order` in the request body, a free-tier key will still restrict to `groq/openai/alibaba`. OpenRouter silently ignores your preference.
- **Model availability changes**: OpenRouter frequently adds/removes models and changes provider routing. Always verify model availability in their catalog: `GET https://openrouter.ai/api/v1/models`
