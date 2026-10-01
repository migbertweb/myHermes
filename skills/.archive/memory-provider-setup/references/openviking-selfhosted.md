# OpenViking Self-Hosted (Local) — Reference

## Architecture

```
┌──────────────┐     HTTP      ┌──────────────────┐
│  Hermes      │─────────────▶│  openviking-server │
│  (client)    │              │  (127.0.0.1:1933)  │
└──────────────┘              └────────┬─────────┬─┘
                                       │         │
                              ┌────────▼─┐  ┌───▼────────┐
                              │  Ollama   │  │  Local FS   │
                              │ (embed +  │  │ (workspace) │
                              │  VLM)     │  │             │
                              └───────────┘  └─────────────┘
```

## ov.conf Complete Reference

Full path: `~/.openviking/ov.conf`

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 1933,
    "root_api_key": "optional-secret-key",
    "cors_origins": ["*"]
  },
  "storage": {
    "workspace": "/home/user/.openviking/data",
    "skip_process_lock": false,
    "agfs": {
      "backend": "local",
      "timeout": 10
    },
    "vectordb": {
      "backend": "local",
      "name": "context"
    },
    "transaction": {
      "lock_timeout": 0.0,
      "lock_expire": 300.0
    }
  },
  "embedding": {
    "max_concurrent": 10,
    "max_retries": 3,
    "text_source": "content_only",
    "max_input_tokens": 4096,
    "dense": {
      "provider": "ollama",
      "api_key": "",
      "api_base": "http://127.0.0.1:11434/v1",
      "model": "nomic-embed-text",
      "dimension": 768
    }
  },
  "vlm": {
    "provider": "openai",
    "api_key": "ollama",
    "api_base": "http://127.0.0.1:11434/v1",
    "model": "guoxuter/ov_intent_analysis_sft:v1_q8",
    "timeout": 30,
    "max_retries": 2
  },
  "code": {
    "code_summary_mode": "ast"
  }
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `server.host` | Binding address. `127.0.0.1` = dev mode (no auth). `0.0.0.0` = requires `root_api_key` |
| `server.port` | TCP port (default: 1933) |
| `storage.workspace` | Absolute path to data directory |
| `embedding.dense.provider` | One of: `ollama`, `local`, `openai`, `volcengine`, `gemini`, `voyage`, `jina`, `cohere`, `minimax`, `dashscope`, `litellm`, `azure` |
| `embedding.dense.api_base` | **MUST include `/v1` suffix** when using OpenAI-compatible providers (Ollama) |
| `vlm.provider` | Same set as embedding + `openai-codex`, `kimi`, `glm` |\n| `vlm.api_base` | Same `/v1` suffix rule |\n\n---\n\n## Cloud Provider Config Examples (Drop-in Ollama Replacement)\n\nReplace local Ollama with free cloud APIs. **Net effect:** zero local RAM/CPU for embedding/VLM, faster startup, no Ollama process needed.\n\n### Gemini (embedding + VLM, both free tier)\n\nSingle API key for both components. Free tier: 60 RPM, generous daily caps. Model: `gemini-embedding-exp-03-07` (768d).\n\n```json\n{\n  \"embedding\": {\n    \"max_concurrent\": 10,\n    \"max_retries\": 3,\n    \"text_source\": \"content_only\",\n    \"dense\": {\n      \"provider\": \"gemini\",\n      \"api_key\": \"<your-gemini-api-key>\",\n      \"model\": \"gemini-embedding-exp-03-07\",\n      \"dimension\": 768\n    }\n  },\n  \"vlm\": {\n    \"provider\": \"openai\",\n    \"api_base\": \"https://generativelanguage.googleapis.com/v1beta/openai/\",\n    \"api_key\": \"<your-gemini-api-key>\",\n    \"model\": \"gemini-2.0-flash\",\n    \"timeout\": 30,\n    \"max_retries\": 2\n  }\n}\n```\n\n**Note:** Same dimension (768) as nomic-embed-text. No vector DB wipe needed — existing vectors stay compatible.\n\n### Jina embedding + Gemini VLM\n\n```json\n{\n  \"embedding\": {\n    \"dense\": {\n      \"provider\": \"jina\",\n      \"api_key\": \"<your-jina-api-key>\",\n      \"model\": \"jina-embeddings-v3\",\n      \"dimension\": 1024\n    }\n  },\n  \"vlm\": {\n    \"provider\": \"openai\",\n    \"api_base\": \"https://generativelanguage.googleapis.com/v1beta/openai/\",\n    \"api_key\": \"<your-gemini-api-key>\",\n    \"model\": \"gemini-2.0-flash\",\n    \"timeout\": 30,\n    \"max_retries\": 2\n  }\n}\n```\n\n**Note:** Jina uses 1024d — **requires wiping the vector DB** when switching from 768d. Jina free tier: 1M tokens/month, no credit card.\n\n### Migration steps from Ollama to cloud\n\n```bash\n# 1. Stop the service\nsystemctl --user stop openviking.service\n\n# 2. If changing dimensions (768 → 1024): wipe existing vectordb\nrm -rf ~/.openviking/data/vectordb/\n\n# 3. Edit ov.conf with the new cloud provider configuration\n# 4. Validate before starting\nsource ~/.hermes/hermes-agent/venv/bin/activate\nopenviking-server doctor\n\n# 5. Start the service\nsystemctl --user start openviking.service\n\n# 6. Verify\ncurl -s http://127.0.0.1:1933/ready\n```\n\nThe VLM processes re-indexing asynchronously. New memories written after the switch will use the new model automatically.\n\n### Gemini API key\n\nGet it at: https://aistudio.google.com/app/apikey\n- Free tier: no credit card needed, 60 RPM for Gemini 2.0 Flash\n- Single key works for both embedding and VLM\n\n---\n\n## Local Embedding (without Ollama)

The `provider: "local"` option uses GGUF files and requires `llama-cpp-python`:

```bash
pip install "openviking[local-embed]"
```

**Warning:** This compiles `llama-cpp-python` from source (takes 10+ minutes on moderate hardware). **Only one model is supported**: `bge-small-zh-v1.5-f16`.

If you get `EmbeddingConfigurationError: Local embedding is enabled but 'llama-cpp-python' is not installed`, install the extra:

```bash
pip install "openviking[local-embed]"
# Or just: pip install llama-cpp-python
```

## Systemd User Service (recommended)

The systemd user service ensures OpenViking starts with your session, survives logouts, and auto-restarts on failure. This is the **preferred** persistence method over shell scripts.

**Service file:** `templates/openviking.service` (in this skill). Customise paths then deploy:

```bash
mkdir -p ~/.config/systemd/user
# Copy and edit the template to match your paths
cp /path/to/template ~/.config/systemd/user/openviking.service

systemctl --user daemon-reload
systemctl --user enable --now openviking.service
systemctl --user status openviking.service
journalctl --user -u openviking.service -f   # live logs
```

**Commands for daily use:**
```bash
systemctl --user status openviking.service
systemctl --user restart openviking.service
systemctl --user stop openviking.service
```

**Pitfall — stale process lock:** If you previously ran `openviking-server` manually (from a terminal or background process), that instance holds a lockfile in the data workspace. The systemd service will fail with:

```
openviking.utils.process_lock.DataDirectoryLocked: Another OpenViking process (PID xxx)
is already using the data directory '/home/user/.openviking/data'.
```

**Fix:** Kill the stale process and restart the service:
```bash
kill <PID>
systemctl --user restart openviking.service
```

Or find and kill all leftover processes:
```bash
pkill -f openviking-server
systemctl --user restart openviking.service
```

**VLM model recommendation:** For best local extraction quality, use `guoxuter/ov_intent_analysis_sft:v1_q8` (811 MB) over `qwen2.5-coder:0.5b`. Tested options:

| Model | Size | Quality | Notes |
|-------|------|---------|-------|
| `guoxuter/ov_intent_analysis_sft:v1_q8` | 811 MB | Best local | OpenViking-specific SFT, intent analysis tuned. **Recommended.** `ollama pull guoxuter/ov_intent_analysis_sft:v1_q8` |
| `qwen2.5-coder:0.5b` | 397 MB | Basic | Minimal but functional, fastest inference |
| `gemma3:1b` | 815 MB | Moderate | Better comprehension, slower |

The `guoxuter/ov_intent_analysis_sft` models are fine-tuned for OpenViking's intent analysis pipeline. Version `v1_q8` (Q8 quant) provides the best quality-to-size ratio tested. Version `v4_q8` is also available.

## Authorization & API Key

Hermes env vars in `~/.hermes/.env`:

```bash
export OPENVIKING_ENDPOINT="http://localhost:1933"
export OPENVIKING_ACCOUNT="migbert"
export OPENVIKING_USER="migbert"
export OPENVIKING_AGENT="hermes"
export OPENVIKING_API_KEY="your-key-if-required"
```

- `OPENVIKING_ENDPOINT` — server URL
- `OPENVIKING_ACCOUNT` — top-level namespace (default: `default`)
- `OPENVIKING_USER` — user namespace (default: `default`)
- `OPENVIKING_AGENT` — agent peer ID (default: `default`)
- `OPENVIKING_API_KEY` — optional, matches `server.root_api_key` in ov.conf

## Verification

```bash
# Service health
curl -s http://127.0.0.1:1933/health
# → {"status":"ok","healthy":true,"version":"0.4.7","auth_mode":"dev"}

# Readiness (embedding + vectordb + agfs)
curl -s http://127.0.0.1:1933/ready
# → {"status":"ready","checks":{"agfs":"ok","vectordb":"ok","embedding":"ok"}}

# Hermes status
hermes memory status
# → Provider: openviking, Plugin: installed ✓, Status: available ✓
```

### Deep model check (beyond /ready)

The `/ready` endpoint only checks that the embedding model *loaded* — it won't tell you if it's hitting API rate limits, returning garbled vectors, or silently failing. For a real connectivity test:

**1. Check model usage stats:**
```bash
curl -s http://127.0.0.1:1933/api/v1/observer/models
```
Returns per-model call count, prompt/completion tokens, and last-used timestamp. If calls are stuck at 0 for the VLM despite memory extraction tasks queued, the model is unreachable or rate-limited.

**2. Check for OpenRouter rate limit errors in logs:**
```bash
journalctl --user -u openviking --no-pager | grep -iE "429|rate.?limit|RateLimitError"
```
If you see `Rate limit exceeded: free-models-per-day. Add 5 credits to unlock 1000 free model requests per day`, the free tier daily cap is hit.

**3. Probe the embedding endpoint directly:**
```bash
curl -s -X POST http://HOST:PORT/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"model":"nomic-embed-text","input":"diagnostic probe"}'
```
Expect a 200 with a `data[0].embedding` array. Timeout/failure points to misconfigured provider or unreachable API.

**4. Probe the VLM endpoint directly:**
```bash
curl -s -X POST http://HOST:PORT/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"your-vlm-model","messages":[{"role":"user","content":"respond with just OK"}],"max_tokens":10}'
```
Expect a 200 with `choices[0].message.content`. Non-200 → check API key, base URL, model name.

**5. Test search to confirm the pipeline end-to-end:**
```bash
curl -s -X POST http://127.0.0.1:1933/api/v1/search/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","limit":1}'
```
Returns memories, resources, skills. Empty result set means the index exists but has no matches — still a sign the embedding pipeline is alive.

**6. Check vector store count:**
```bash
curl -s http://127.0.0.1:1933/api/v1/debug/vector/count
```
Returns total indexed vectors. If 0 and OpenViking has been running for a while, either embedding is failing or nothing was indexed.

**7. Monitor reindex progress (after vector DB wipe):**

When you delete the vector DB (e.g. after changing embedding dimension), OpenViking auto-queues embedding tasks for all AGFS content. Track progress:

```bash
curl -s http://127.0.0.1:1933/api/v1/observer/queue
```

Look for the `Embedding` queue — it shows **Pending**, **In Progress**, **Errors**, and **Total**. A healthy reindex shows pending → 0 over time. Errors indicate model connectivity issues (check `observer/models` for frozen counts or 429s in journalctl).

The `/api/v1/content/reindex` endpoint can trigger explicit reindexing (`POST` with `{"uri":"viking://resources/"}` or `{"uri":"viking://user/default/memories/"}`), but it may time out on the first call (30s+) as the server queues work. After the timeout, check the queue — tasks should be visible. The endpoint works; the timeout is just the HTTP response, not a failure.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `OpenAI API error: 404 page not found` | Ollama api_base missing `/v1` suffix | Set `api_base` to `http://host:11434/v1` |
| `Local embedding is enabled but 'llama-cpp-python' is not installed` | Missing local embedding dep | `pip install "openviking[local-embed]"` |
| `Unknown local embedding model` | Wrong model name for local provider | Only `bge-small-zh-v1.5-f16` is supported locally |
| `requires 'api_key' to be set` | VLM provider missing API key | Use Ollama (api_key="ollama") or set real API key |
| `curl: (7) Failed to connect` | Server not listening yet | Wait 15-20s for model loading, then retry |
| `DataDirectoryLocked: Another OpenViking process (PID xxx) is already using the data directory` | Stale process holds workspace lock | Kill old PID (`kill <PID>`) or `pkill -f openviking-server`, then restart service |
| `Server refuses to start without it` | `root_api_key` missing when binding 0.0.0.0 | Add `server.root_api_key` to ov.conf or bind `127.0.0.1` |
| `EmbeddingRebuildRequiredError: Existing collection embedding metadata does not match current configuration` | Changed embedding model/provider name string in config without rebuilding vectordb | **Option A** — Delete the vectordb and let it rebuild: `rm -rf ~/.openviking/data/vectordb/`. **Option B** — Revert the model name to what was previously used (collection_meta.json stores `model` + `model_identity`; both must match). **Option C** — Do NOT set `embedding.dense.allow_metadata_override` — this is **NOT a valid config field** in v0.4.7 (will crash with `Unknown config field`). Dimension must remain the same regardless of approach. |
| `openai.APITimeoutError: Request timed out` | VLM request exceeds default timeout | Add `"timeout": 30` and `"max_retries": 2` under the `vlm` section in ov.conf |
| `429 RateLimitError: free-models-per-day` | OpenRouter free-tier daily cap (50 req/day for new accounts without credits). Affects both embedding (during reindex) and VLM (memory extraction). VLM fails first because extraction uses more calls per session. | **Option A** — Add $5+ to OpenRouter account (unlocks 1000 free model requests/day). **Option B** — Switch embedding to local Ollama `nomic-embed-text` (no rate limits) and VLM to Gemini via OpenAI-compatible endpoint (free tier: 60 RPM). **Option C** — Use local Ollama for both (nomic-embed-text + guoxuter/ov_intent_analysis_sft:v1_q8 or gemma4:31b-cloud). See Cloud Provider Config Examples section. |

## Pre-Restart Validation

Before restarting `openviking.service` after a config change, validate the config with `doctor`:

```bash
source ~/.hermes/hermes-agent/venv/bin/activate
openviking-server doctor
```

The doctor checks: Config file validity, Python version, native engine, AGFS SDK, embedding provider probe, VLM provider, Ollama connectivity, VikingBot auth, and disk space. Fix any issues before restarting the service — this prevents the rapid restart loop that leaves the server in a crash-recovery state.

## Pitfalls

### Embedding Model Name Must Be Consistent

The vectordb collection stores both `model` and `model_identity` in its metadata (`collection_meta.json`). Changing the model name string — even when pointing to exactly the same model (e.g., `nomic-embed-text` → `nomic-embed-text:latest`) — triggers `EmbeddingRebuildRequiredError` on startup. The model string must be byte-identical to what was used when the collection was created.

**Fix options (preferred order):**
1. Revert the model name to the original string (quickest, no data loss)
2. Delete `~/.openviking/data/vectordb/` and restart (loses indexed context but session JSONL files in `viking/` are preserved)

### `allow_metadata_override` is NOT a Config Field

Despite what the error message suggests, `"allow_metadata_override": true` under `embedding.dense` is **not a valid configuration key** in OpenViking v0.4.7. It causes a hard crash at startup:

```
Unknown config field 'embedding.dense.allow_metadata_override'
```

The error message mentions it as a hypothetical option, but it was either removed or planned for a future release. Do not use it.

### VLM Timeout on Slow Models

The `guoxuter/ov_intent_analysis_sft:v1_q8` model (752M, Q8 quant) runs locally via Ollama. On moderate hardware it can take 10-20s per inference. OpenViking's default VLM timeout is too short, causing `openai.APITimeoutError`. Always set explicit `timeout` (≥30) and `max_retries` (≥2) when using local Ollama VLM models.

## Ollama Setup for OpenViking

```bash
# Pull embedding model (274MB)
ollama pull nomic-embed-text

# Pull a small VLM model (optional, ~400MB)
ollama pull qwen2.5-coder:0.5b

# Verify embedding endpoint
curl -X POST http://127.0.0.1:11434/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"nomic-embed-text","input":"test"}'
```
