# Hermes Built-in Provider Resolution

Detailed reference for how Hermes resolves built-in API-key providers, the two-tier architecture, and the dual-alias gap that causes auxiliary tasks to silently fail.

## Two-Tier Provider Architecture

Hermes has two completely different provider configuration paths:

### Tier 1: Built-in PROVIDER_REGISTRY

Registered in the `PROVIDER_REGISTRY` dict at `hermes_cli/auth.py` line ~169.

**Characteristics:**
- Hardcoded provider ID, base URL, auth type, and API key env var(s)
- Activated by setting `model.provider` to the provider slug (e.g. `opencode-zen`)
- No entry needed under `config.yaml → providers:` — the registry is in code
- `auth_type` can be `api_key`, `oauth_device_code`, `oauth_external`, or `external_process`

**Example entry (line ~361):**
```python
"opencode-zen": ProviderConfig(
    id="opencode-zen",
    name="OpenCode Zen",
    auth_type="api_key",
    inference_base_url="https://opencode.ai/zen/v1",
    api_key_env_vars=("OPENCODE_ZEN_API_KEY",),
    base_url_env_var="OPENCODE_ZEN_BASE_URL",
),
```

### Tier 2: Custom Named Providers

Defined by the user under `config.yaml → providers:`. Each entry has explicit `base_url`, optional `api_key_env`, and `models` list. No hardcoded URLs.

**When to use which:**
- Built-in registry → for providers Hermes ships with (opencode-zen, gemini, zai, deepseek, etc.) — just set `model.provider + env var`
- Custom named → for self-hosted, local, or non-standard endpoints (llama.cpp, Ollama, custom OpenAI-compatible services)

## Alias Normalization — Two Separate Dicts

### 1. Main-chat alias dict (`hermes_cli/auth.py`, line ~1536)

Used by `resolve_provider(requested)` — the CLI and primary session resolver. Full coverage of all provider aliases.

```python
_PROVIDER_ALIASES = {
    "opencode": "opencode-zen", "zen": "opencode-zen",
    "go": "opencode-go",
    "claude": "anthropic",
    "google": "gemini", "google-gemini": "gemini",
    "grok": "xai",
    "glm": "zai", "z-ai": "zai", "zhipu": "zai",
    "kimi": "kimi-coding", "moonshot": "kimi-coding",
    "aws": "bedrock",
    "hf": "huggingface",
    # ... full list in source
}
```

### 2. Auxiliary-route alias dict (`agent/auxiliary_client.py`, line ~184)

Used by `_normalize_aux_provider()` — the auxiliary client routing path. **Smaller set — notably missing:**

```python
_PROVIDER_ALIASES = {
    "google": "gemini",
    "grok": "xai",
    "glm": "zai",
    "kimi": "kimi-coding",
    "claude": "anthropic",
    # ... NO opencode → opencode-zen
    # ... NO go → opencode-go
    # ... NO kilocode, arcee, deepseek, stepfun, hf aliases
}
```

Missing aliases in the aux dict:
- `opencode` → `opencode-zen`
- `zen` → `opencode-zen`
- `go` → `opencode-go`
- `kilocode` → `kilocode`
- `hf` → `huggingface`
- `deepseek` → `deepseek`
- `stepfun` → `stepfun`
- `arcee` → `arcee`

## When the Dual-Alias Gap Hits

The main chat session always works because `resolve_provider()` in `hermes_cli/auth.py` normalizes through its complete alias dict before checking `PROVIDER_REGISTRY`. The session's `self.provider` ends up as the canonical slug (e.g. `opencode-zen`).

Auxiliary tasks (compression, vision, web extract, title generation, session search, curator, etc.) call `_resolve_auto()` → `resolve_provider_client()`. The provider name flows through `_normalize_aux_provider()` with the **smaller** alias dict.

### Does it actually fail?

**It depends on whether the runtime override is set.**

When an auxiliary task runs **inside an active session** (e.g. compression during a chat turn), the `main_runtime` dict from `_current_main_runtime()` carries the already-resolved provider (e.g. `opencode-zen`). In this case, `runtime_provider` is already canonical → works fine.

When an auxiliary task runs **outside a session** or without runtime context (standalone title generation, curator background tick, monitor, some cron-job contexts, certain session-search paths), `_read_main_provider()` reads raw from `config.yaml → model.provider` → gets the alias (e.g. `opencode`) → the smaller aux alias dict does NOT normalize it → `resolve_provider_client("opencode", ...)` → "opencode" not in `PROVIDER_REGISTRY` → returns `(None, None)` → task silently fails.

## Root Cause Fix

The permanent fix is to add the missing aliases to `agent/auxiliary_client.py` line ~184:

```python
_PROVIDER_ALIASES = {
    # ... existing entries ...
    "opencode": "opencode-zen",
    "zen": "opencode-zen",
    "go": "opencode-go",
    "kilocode": "kilocode",
    "hf": "huggingface",
    "deepseek": "deepseek",
    "stepfun": "stepfun",
    "arcee": "arcee",
}
```

Or better, remove the duplicate dict entirely and import from `hermes_cli.auth`.

## Workaround (No Source Edit)

Use the **canonical slug** in `model.provider`, never a short alias:

```bash
hermes config set model.provider opencode-zen     # NOT "opencode"
hermes config set model.provider kimi-coding      # NOT "kimi"
hermes config set model.provider opencode-go      # NOT "go"
```

This works because the canonical name is in `PROVIDER_REGISTRY` directly and needs no alias normalization. Both main and auxiliary paths find it.

## Source File Locations

| File | Line | What |
|------|------|------|
| `hermes_cli/auth.py` | ~169 | `PROVIDER_REGISTRY` dict — all built-in providers |
| `hermes_cli/auth.py` | ~1513 | `resolve_provider()` — main resolution entry point |
| `hermes_cli/auth.py` | ~1536 | Full `_PROVIDER_ALIASES` dict |
| `agent/auxiliary_client.py` | ~184 | Smaller `_PROVIDER_ALIASES` aux dict **<-- the gap** |
| `agent/auxiliary_client.py` | ~218 | `_normalize_aux_provider()` — uses the smaller dict |
| `agent/auxiliary_client.py` | ~1876 | `_read_main_provider()` — reads raw `model.provider` from config |
| `agent/auxiliary_client.py` | ~3580 | `_resolve_auto()` — full auto-detection chain |
| `agent/auxiliary_client.py` | ~3842 | `resolve_provider_client()` — central provider client router |
| `agent/auxiliary_client.py` | ~4286 | `PROVIDER_REGISTRY.get(provider)` — the lookup that returns None for unresolved aliases |
| `run_agent.py` | ~1039 | `_current_main_runtime()` — provides session runtime with resolved provider |
