# OpenCode + Hermes API Server

Reproduction details and debugging steps for the custom SSE event
compatibility issue when OpenCode uses Hermes' OpenAI-compatible API
server as its LLM backend.

## Symptom

OpenCode CLI or VSCodium extension fails with:

```
Type validation failed: Value: {"tool":"browser_navigate","emoji":"🌐",
  "label":"<url>","toolCallId":"call_<id>","status":"running"}
Error message: [{ "code": "invalid_union", "errors": [
  [{ "expected": "array", "code": "invalid_type", "path": ["choices"],
     "message": "Invalid input: expected array, received undefined" }],
  [{ "expected": "object", "code": "invalid_type", "path": ["error"],
     "message": "Invalid input: expected object, received undefined" }]
]}]
```

## Cause

Hermes' API server (`gateway/platforms/api_server.py`) emits custom
`hermes.tool.progress` SSE events when `stream: true` is set. These
events carry the format:

```json
{"tool":"browser_navigate","emoji":"🌐","label":"<label>",
 "toolCallId":"call_...","status":"running"}
```

The SSE wire format is:

```
event: hermes.tool.progress
data: {"tool":"browser_navigate","emoji":"🌐",...}
```

OpenCode's SSE parser reads ALL `data:` lines — including those from
custom events — and validates them against the OpenAI
`chat.completion.chunk` schema, which requires a `choices` array or
an `error` object. The tool-progress payload has neither, so validation
fails.

## Root code

- **SSE emitter:** `gateway/platforms/api_server.py` lines 1822–1846
  (`_on_tool_start` callback) and lines 1848–1862 (`_on_tool_complete`)
- **Default config:** `gateway/display_config.py` line 137 — the
  `api_server` platform inherits `_TIER_HIGH` defaults including
  `tool_progress: "all"`
- **Resolution order:** `gateway/display_config.py` lines 144–206
  (`resolve_display_setting`)

## Fix

### 1. Config entry (always required)

Set `tool_progress: off` for the `api_server` platform in
`~/.hermes/config.yaml`:

```yaml
display:
  platforms:
    # ... existing platforms (telegram, discord, etc.)
    api_server:
      tool_progress: off
```

**⚠️ YAML pitfall:** DO NOT add `platforms:` as a separate top-level key
in the `display:` section. YAML spec says duplicate keys resolve to the
last occurrence, so a second `platforms:` will overwrite the first one.
Always merge the `api_server` entry into the existing `platforms:` block
where `telegram`/`discord` etc. are already defined.

### 2. Code patches (required unless upstream includes them)

The streaming code in `api_server.py` does NOT read
`resolve_display_setting` by default — it unconditionally wires up
callbacks that emit `hermes.tool.progress` events. Two patches:

#### Patch A: `gateway/display_config.py` — set default to `off`

In `_PLATFORM_DEFAULTS`, change the `api_server` entry:

```python
# Before:
"api_server": {**_TIER_HIGH, "tool_preview_length": 0},

# After:
"api_server": {**_TIER_HIGH, "tool_preview_length": 0, "tool_progress": "off"},
```

#### Patch B: `gateway/platforms/api_server.py` — respect the setting

In `_handle_chat_completions`, inside the `if stream:` block (early in
the closure setup, before `_on_delta`), add a config check:

```python
from gateway.run import _load_gateway_config as _lgc
from gateway.display_config import resolve_display_setting as _rds
_show_tool_progress = _rds(_lgc(), "api_server", "tool_progress") != "off"
```

Then pass the callbacks conditionally to `_run_agent`:

```python
# Before:
tool_start_callback=_on_tool_start,
tool_complete_callback=_on_tool_complete,

# After:
tool_start_callback=_on_tool_start if _show_tool_progress else None,
tool_complete_callback=_on_tool_complete if _show_tool_progress else None,
```

The `None` values are safe — the agent checks
`if agent.tool_start_callback:` before calling it.

## Verification

After applying the fix, use curl to verify the SSE stream is clean:

```bash
API_KEY=$(grep '^API_SERVER_KEY=' ~/.hermes/.env | cut -d= -f2)
curl -s -N -X POST http://localhost:8642/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"say hello"}],"stream":true}' \
  | grep -c 'hermes.tool.progress'
# Expected: 0

# Also check the full stream looks like valid OpenAI chunks:
curl -s -N -X POST http://localhost:8642/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"what time is it"}],"stream":true}' \
  | head -20
# Every data: line should have "choices":[{...}] with a "delta" field
# No event: hermes.tool.progress lines
```

Expected clean output — only standard `data:` with `choices[].delta` and
a final `data: [DONE]`:

## Affected clients

| Client | Streaming | Custom events parsed? |
|--------|-----------|-----------------------|
| OpenCode CLI | Yes | Broken — reads all data lines |
| VSCodium ACP Client | No | N/A (uses ACP, not SSE) |
| Open WebUI | Yes | Works — recognises `hermes.tool.progress` |
| curl / raw HTTP | Yes | N/A — no validation |
