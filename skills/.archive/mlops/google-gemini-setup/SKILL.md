---
name: google-gemini-setup
description: Configure Google Gemini as a model provider in Hermes Agent — both API key (AI Studio) and OAuth (Cloud Code Assist) paths.
---

# Google Gemini Setup for Hermes Agent

Google Gemini has **two** provider options in Hermes, each with different auth, quota, and capabilities.

| Provider | Auth | Backend | Free tier quota | Context limit |
|----------|------|---------|-----------------|---------------|
| `gemini` | API key (`GOOGLE_API_KEY`) | AI Studio | Very limited daily (RPM + TPM) | Up to 1M tokens |
| `google-gemini-cli` (aliases: `gemini-cli`, `gemini-oauth`) | OAuth (PKCE, browser-based) | Cloud Code Assist | Better free tier (~5 RPM) | Up to 1M tokens |

## Option 1: API Key (`gemini`)

### Setup

```bash
# 1. Set the env var in ~/.hermes/.env
GOOGLE_API_KEY=your_key_here
# or: GEMINI_API_KEY=your_key_here (alias)

# 2. Verify Hermes detects it
hermes auth list
# Should show: gemini (1 credentials): #1 GOOGLE_API_KEY api_key env:GOOGLE_API_KEY

# 3. Switch to this provider (interactive)
hermes model
# Or set in config.yaml:
#   model:
#     default: gemini-2.0-flash
#     provider: gemini
```

### Configuration in config.yaml

```yaml
model:
  default: gemini-2.0-flash        # or gemini-2.5-flash, gemini-3-flash-preview, etc.
  provider: gemini
  context_length: 1048576           # explicit 1M context override (optional but recommended)
providers:
  gemini:
    base_url: https://generativelanguage.googleapis.com/v1beta
    # or use OpenAI-compatible endpoint:
    # base_url: https://generativelanguage.googleapis.com/v1beta/openai
```

### Pitfalls

- **429 quota errors ≠ expired key.** The free AI Studio tier has aggressive daily limits (requests per minute AND tokens per minute). A 429 response means quota exhausted, not an invalid key. Wait for daily reset or enable billing.
- **Quota exhaustion shows as "limit: 0"** in the error body. Verify with a direct curl test:
  ```bash
  curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
    -H "x-goog-api-key: $GOOGLE_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"contents":[{"parts":[{"text":"hi"}]}]}'
  ```
- **Free tier models** (`gemini-2.0-flash`, `gemini-2.5-flash`) have the quota limits. Pro models require billing enabled.
- **Base URL matters:** The standard endpoint (`/v1beta`) uses the native Gemini API. The OpenAI-compatible endpoint (`/v1beta/openai`) works but has different behavior for thinking/reasoning config.

## Option 2: OAuth (`google-gemini-cli`) — RECOMMENDED

Uses Google Cloud Code Assist API via OAuth PKCE flow. **No external CLI needed** — Hermes has the flow built into `agent/google_oauth.py`.

### Setup

```bash
# 1. Run the OAuth flow (opens browser)
hermes auth add google-gemini-cli

# This will:
# - Start a local HTTP server on a random port
# - Open your browser to accounts.google.com for auth
# - Store tokens in ~/.hermes/auth/google_oauth.json (chmod 600)
# - Register the credential in Hermes' auth pool

# 2. Verify
hermes auth list google-gemini-cli

# 3. Switch to this provider
# In config.yaml:
#   model:
#     default: gemini-2.5-flash
#     provider: google-gemini-cli
#     context_length: 1048576
```

### Aliases

All of these resolve to the same provider:
```
google-gemini-cli   # canonical
gemini-cli          # alias
gemini-oauth        # alias
google-oauth        # alias
google-gemini-cli   # alias
```

So `hermes auth add gemini-cli` works the same as `hermes auth add google-gemini-cli`.

### How the OAuth flow works

1. Hermes generates a PKCE challenge (S256 code verifier)
2. Opens browser to `accounts.google.com/o/oauth2/v2/auth` with the public Google Gemini CLI client ID
3. After authorization, Google redirects to `localhost` with an auth code
4. Hermes' local HTTP server captures the code
5. Code is exchanged for access + refresh tokens
6. Tokens stored in `~/.hermes/auth/google_oauth.json` in the packed format:
   ```json
   {
     "refresh": "refreshToken|projectId|managedProjectId",
     "access": "ya29...",
     "expires": 1744848000000,
     "email": "user@example.com"
   }
   ```
7. Credential registered in Hermes' auth pool for runtime resolution

### Configuration in config.yaml

```yaml
model:
  default: gemini-2.5-flash
  provider: google-gemini-cli
  context_length: 1048576         # explicit override for 1M context
providers:
  google-gemini-cli:
    base_url: cloudcode-pa://google   # internal scheme; resolved to https://cloudcode-pa.googleapis.com
```

> **Note:** The `base_url: cloudcode-pa://google` is a Hermes-internal marker scheme. `run_agent.py` detects it and constructs a `GeminiCloudCodeClient` instead of the standard OpenAI SDK client.

### Token refresh

Tokens are refreshed automatically ~60s before expiry (`GEMINI_OAUTH_ACCESS_TOKEN_REFRESH_SKEW_SECONDS`). The refresh flow:
1. Reads `~/.hermes/auth/google_oauth.json`
2. POSTs the refresh token to `oauth2.googleapis.com/token`
3. Updates the file with new access token + expiry
4. If refresh fails, prompts the user to re-auth

### Free tier rate limits

Code Assist free tier is ~5 RPM for Flash models. The built-in `GeminiCloudCodeClient` (in `agent/gemini_cloudcode_adapter.py`) handles 429s with **server-guided retry**:
- Parses `retryDelay` from Google's error response body
- Falls back to regex on error message (`"reset after 38s"`)
- Default fallback: 12s
- Max 3 retries per request
- Logs: `INFO: Code Assist 429, retrying in 44.0s (attempt 1/3)`

## Model availability by provider

Not all Google models work with both providers. Cloud Code Assist (`google-gemini-cli`) **only serves Gemini models** — Gemma models return HTTP 404.

| Model | `gemini` (API key, AI Studio) | `google-gemini-cli` (OAuth, Code Assist) |
|-------|:-:|:-:|
| gemini-3-flash-preview | ✅ | ✅ |
| gemini-3.5-flash | ✅ | ✅ (GA-gated) |
| gemini-3-pro-preview | ✅ | ✅ |
| gemini-3.1-pro-preview | ✅ | ✅ |
| gemini-2.5-flash | ✅ | ❌ |
| gemini-2.5-pro | ✅ | ❌ |
| gemma-4-31b-it | ✅ | ❌ |
| gemma-4-26b-it | ✅ | ❌ |
| gemma-3-* | ✅ | ❌ |

**Key takeaway:** Cloud Code Assist has a curated model list hardcoded in `hermes_cli/models.py`. It does not expose a `/models` endpoint. If a model isn't in the list, it won't work with `google-gemini-cli`. For Gemma models, use the `gemini` (API key) provider, OpenRouter (`google/gemma-4-31b-it:free`), or OpenCode Zen.

## Verifying Gemini is working

```bash
# Quick test
hermes chat -q "say hi in one sentence"

# Test tool calling (exercises thoughtSignature replay for thinking models)
hermes chat -q "use the memory tool to remember 'test' then tell me what you remembered"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 429 / "Quota exceeded" | Free tier daily limit hit | Wait for reset, enable billing, or switch to OAuth provider (different quota pool) |
| 401 Unauthorized (OAuth) | Access token expired, refresh failed | `hermes auth add google-gemini-cli` to re-auth |
| 401 Unauthorized (API key) | Invalid or revoked key | Check key at https://aistudio.google.com/app/apikey |
| 400 / "missing thought_signature" | Thinking-mode replay issue | The GeminiCloudCodeClient handles this via module-level `_SIGNATURE_CACHE` |
| "provider not found" | Wrong provider name in config | Use `gemini` (API key) or `google-gemini-cli` (OAuth) |
| "needs OAuth setup" | Provider set to `google-gemini-cli` but not authenticated | Run `hermes auth add google-gemini-cli` first |

## Related

- The `hermes model` interactive picker lists Gemini options. Run it directly (not via subprocess) since it needs a TTY.
- For Google Workspace APIs (Gmail, Calendar, Drive), use the `google-workspace-setup` skill.
