# OpenRouter Free-Tier Diagnostic Reference

Session reproduction of the `"No allowed providers are available for the selected model"` error.

## Error Pattern

```
HTTP 404: No allowed providers are available for the selected model.

Metadata:
  available_providers:  ["google-ai-studio", "open-inference"]
  requested_providers: ["groq", "openai", "alibaba"]
```

The `requested_providers` list is ALWAYS `["groq", "openai", "alibaba"]` regardless of:
- Whether you pass a `provider` field in the request body
- What provider slugs you specify in `provider.only` or `provider.order`
- Which model you request
- Whether you use the `:free` suffix

This means the restriction is at the API key level, not the request level.

## Key Diagnostic Endpoint

```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer ***
```

Response:
```json
{
  "data": {
    "is_free_tier": true,       // THE KEY FLAG
    "usage": 0,
    "limit": null,
    "limit_remaining": null,
    "byok_usage": 0,
    "is_management_key": false,
    "is_provisioning_key": false
  }
}
```

## Full Test Script

```python
#!/usr/bin/env python3
"""Test OpenRouter model availability."""
import urllib.request, urllib.error, json, os

with open(os.path.expanduser('~/.hermes/.env')) as f:
    key = ''
    for line in f:
        if line.startswith('OPENROUTER_API_KEY'):
            key = line.split('=', 1)[1].strip().strip("'\"")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

def test(model_name, provider=None):
    body = {
        "model": model_name,
        "messages": [{"role": "user", "content": "say hi"}],
        "max_tokens": 5,
    }
    if provider:
        body["provider"] = provider

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        if "choices" in data:
            return f"OK: {data['choices'][0]['message']['content']}"
        return json.dumps(data)[:100]
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        msg = err.get("error", {}).get("message", "")[:120]
        meta = err.get("error", {}).get("metadata", {})
        return f"FAIL: {msg}" + (f" | avail: {meta.get('available_providers', [])[:4]}" if meta else "")
```

## Test Results (Free-Tier Key — March 2026)

| Model | Result | Available Providers |
|-------|--------|-------------------|
| `google/gemma-4-31b-it:free` | FAIL | google-ai-studio, open-inference |
| `google/gemma-4-31b-it` | FAIL | venice, deepinfra, siliconflow, ... |
| `google/gemma-4-26b-a4b-it:free` | FAIL | google-ai-studio |
| `nvidia/nemotron-3-super-120b-a12b:free` | FAIL | nvidia |
| `moonshotai/kimi-k2.6:free` | FAIL | crucible |
| `qwen/qwen3-coder:free` | FAIL | venice |
| `poolside/laguna-xs.2:free` | FAIL | poolside |
| `liquid/lfm-2.5-1.2b-thinking:free` | FAIL | liquid |
| `openai/gpt-oss-120b:free` | FAIL | open-inference |
| `z-ai/glm-4.5-air:free` | FAIL | z-ai |
| `deepseek/deepseek-chat:free` | FAIL | No endpoints found |
| `openrouter/free` (catch-all) | FAIL | liquid, poolside, venice, open-inference |

**Every single free model fails** because none of the actual serving providers (`google-ai-studio`, `venice`, `nvidia`, etc.) are in the free-tier allowed set (`groq`, `openai`, `alibaba`).

## Root Cause

OpenRouter changed their free-tier policy. Previously, `:free` models would route through any provider offering the model at $0. Now, free-tier API keys are hard-restricted to only `groq`, `openai`, and `alibaba`. Since none of these providers serve the models that have `:free` variants, **no model works with a free-tier key**.

## Fix

1. **Add credits** to the OpenRouter account. Even $1 upgrades the key from free-tier and enables full provider routing. Most models cost fractions of a cent per million tokens.
2. **Remove the `:free` suffix** after adding credits — use the base model slug.
3. Alternatively, **switch providers** to OpenCode Zen, Google AI Studio direct, or local inference.
