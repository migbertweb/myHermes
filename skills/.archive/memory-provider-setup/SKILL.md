---
name: memory-provider-setup
description: >-
  Configure, activate, and troubleshoot external memory providers in Hermes
  Agent. Covers Honcho (self-hosted and cloud), Holographic (local), Hindsight,
  Mem0, OpenViking, RetainDB, ByteRover, and Supermemory. Absorbs the logic of
  picking between reasoning-based vs. simple-vector backends.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [memory, honcho, holographic, hindsight, mem0, mnemosyne, openviking, retaindb, byterover, supermemory]
    supersedes: []
---

# Memory Provider Setup (Umbrella)

Hermes Agent ships with 9 external memory provider plugins that give the agent
persistent, cross-session knowledge. Only **one** external provider can be
active at a time — the built-in MEMORY.md / USER.md always runs alongside it.

## Quick Start

```bash
hermes memory setup              # interactive picker + configuration
hermes memory status             # check what's active
hermes memory off                # disable external provider
```

Or set manually in `~/.hermes/config.yaml`:

```yaml
memory:
  provider: honcho      # or holographic, hindsight, mem0, mnemosyne, openviking, retaindb, byterover, supermemory
```

## Manual Configuration (when wizard is unavailable)

When the interactive `hermes memory setup` wizard can't be used (SSH without TTY, automation scripts, broken CLI deps), configure providers manually:

### Holographic (manual)

```bash
# 0. Ensure `rich` is in the Hermes venv (required by `hermes config set`)
uv pip install --python /path/to/hermes/venv/bin/python rich

# 1. Set the provider
hermes config set memory.provider holographic

# 2. Ensure numpy is in the Hermes venv (for HRR vector similarity)
uv pip install --python /home/piro/.hermes/hermes-agent/venv/bin/python numpy

# 3. (Optional) Configure plugin settings under plugins.hermes-memory-store in config.yaml
#    db_path: path to SQLite db (default: $HERMES_HOME/memory_store.db)
#    auto_extract: true (Saves user preferences/decisions automatically at session end)
#    default_trust: 0.3-1.0
#    hrr_dim: 102 la (HRR vector dimensions)
#
#    PITFALL: If config.yaml has duplicate 'enabled: []' keys under plugins, some tools may fail.
#    Check that plugins.enabled is a single list.

# 4. Start a new session (/reset) to activate
```

Holographic requires no external services, no Docker, no API keys. The SQLite database is created automatically on first access.


### Hindsight (manual — any mode)

```bash
# Cloud mode
hermes config set memory.provider hindsight
uv pip install --python /path/to/hermes/venv "hindsight-client>=0.4.22"
# Set HINDSIGHT_API_KEY in ~/.hermes/.env
# Set HINDSIGHT_MODE=cloud in ~/.hermes/.env (or config via ~/.hermes/hindsight/config.json)

# Local embedded mode (WARNING: ~3GB download due to torch + CUDA)
hermes config set memory.provider hindsight
uv pip install --python /path/to/hermes/venv hindsight-all
# Configure ~/.hermes/hindsight/config.json with mode, llm_provider, llm_api_key, llm_model
```

## How It Works

When a memory provider is active, Hermes automatically:

1. **Injects provider context** into the system prompt
2. **Prefetches relevant memories** before each turn (background, non-blocking)
3. **Syncs conversation turns** after each response
4. **Extracts memories on session end**
5. **Mirrors built-in memory writes** to the external provider
6. **Adds provider-specific tools** (search, profile, conclude, etc.)

The abstract base is `agent/memory_provider.py` (`MemoryProvider` ABC) with
lifecycle hooks: `initialize()`, `prefetch()`, `sync_turn()`, `get_tool_schemas()`,
`handle_tool_call()`, `shutdown()`. Optional hooks include `on_turn_start()`,
`on_session_end()`, `on_session_switch()`, `on_memory_write()`, and
`on_delegation()`.

## Available Providers Overview

| Provider | Self-Hosted | Reasoning | Infrastructure | Best For |
|----------|-------------|-----------|----------------|----------|
| **Honcho** | ✅ Docker (PG+Redis+worker) | ✅ Dialectic reasoning | Heavy (PG+pgvector+Redis+LLM API) | Multi-agent, deep user modeling |
| **Holographic** | ✅ SQLite | ❌ | Light (SQLite + numpy) | Simple semantic search, no servers |
| **Hindsight** | ✅ 3 modes | ✅ KG + reflect | Medium (emb. PG ~200MB) | Entity resolution, cross-session synthesis |
| **Mem0** | ⚠️ API key | ✅ Yes | Medium (cloud API) | Turnkey reasoning memory |
| **OpenViking** | ✅ Self-hosted (JSON config) | ✅ Yes | High (56+ deps: tree-sitter ×10 langs, numpy, LevelDB, OpenTelemetry, file parsers — ~300 MB RSS even with cloud embeddings) | Local memory extraction, RAGFS filesystem, vector search, tiered loading |
| **Mnemosyne** | ✅ SQLite (pip install) | ✅ Local LLM (optional) | Low (~50 MB core, ~800 MB with fastembed, ~1.5 GB with local LLM) | **Hermes plugin**, auto-context injection, 23 tools, knowledge graph, memory banks |
| **RetainDB** | ⚠️ API key | ❌ | Medium (cloud API) | Simple persistence |
| **ByteRover** | ❌ Requires API key | ❌ | Cloud API | Ephemeral recall |
| **Supermemory** | ❌ Requires API key | ❌ | Cloud API | — |

## Choosing a Provider

1. **Want local-only, no dependencies?** → Holographic (SQLite + vector embeddings, no server)
2. **Want full reasoning / user modeling?** → Honcho (self-hosted) or Mem0 (cloud)
3. **Need multi-agent isolation?** → Honcho (peer-based separation)
4. **Cloud-only is fine?** → Mem0, OpenViking, or RetainDB
5. **Want Hermes-first-class plugin with auto-context injection?** → Mnemosyne (pipx install, 25 tools, knowledge graph, no servers)
6. **Unsure, start small?** → Holographic, Mnemosyne core, or built-in, migrate later

## Architecture Pattern for Self-Hosted Providers

Self-hosted providers (Honcho) follow a two-process architecture:

```
┌─────────────┐     ┌────────────────┐     ┌──────────────┐
│  Hermes     │────▶│  Provider API  │────▶│  Database     │
│  (client)   │     │  (FastAPI)     │     │  (PG+pgvector)│
└─────────────┘     └───────┬────────┘     └──────────────┘
                            │
                    ┌───────▼────────┐
                    │  Worker        │
                    │  (deriver)     │←── LLM API calls
                    └────────────────┘
```

- **API** handles synchronous reads/writes (messages, sessions, peers)
- **Worker** processes asynchronous reasoning (derivation, summarization, dreaming)
- **Database** stores structured data + vector embeddings

## RAM Reality Check — OpenViking vs Holographic

OpenViking is the server-based option with vector search and tiered loading.
Holographic is the embedded option — SQLite, no daemon, zero server RAM.

| Provider | Baseline RAM | Daemon | Disk (data) | Auto-inject | Semantic search |
|----------|-------------|--------|-------------|-------------|-----------------|
| **OpenViking** | ~300 MB RSS / ~430 MB cgroup | systemd user service | ~95 MB + 1.6 GB venv | Yes (tiered L0→L1→L2) | Yes (via cloud embeddings) |
| **Holographic** | ~0 MB (no process) | None | ~10-50 MB SQLite | No (tools-only) | FTS5 + HRR (no semantic without numpy) |

Even with cloud embeddings (OpenRouter/Gemini — zero local model), OpenViking server
consumes ~300 MB RSS because the process loads all dependencies at startup:
- Tree-sitter parsers (10 language grammars) ~80-150 MB
- numpy ~30-40 MB
- LevelDB vector store cache (53 MB on disk) ~50-80 MB
- File parsers (pdf, docx, xlsx, epub, etc.) ~30-50 MB
- OpenTelemetry SDK ~10-20 MB
- Uvicorn/FastAPI/httpx ~25-30 MB
- Python runtime ~15-20 MB

**There is no config option to disable unused parsers or lighten the server.**
OpenViking does not have a "minimal mode". If ~300 MB RSS is too much for your
setup, the options are:
1. Accept it — 300 MB is normal for a full-featured context server
2. Systemd MemoryMax — risky, may OOM-kill the process
3. **Migrate to Holographic** — the only truly lightweight self-hosted option

The vectordb uses **LevelDB** (not FAISS). Files are `.ldb` format in
`{workspace}/vectordb/context/store/`. On-disk size of the vector store
for ~15 memories is about 53 MB.

### OpenViking (self-hosted local)

```bash
# 1. Set provider
hermes config set memory.provider openviking

# 2. Install package (in Hermes venv)
source ~/.hermes/hermes-agent/venv/bin/activate
pip install openviking

# 3. Set env vars in ~/.hermes/.env
#    OPENVIKING_ENDPOINT=http://localhost:1933
#    OPENVIKING_ACCOUNT=migbert
#    OPENVIKING_USER=migbert
#    OPENVIKING_AGENT=hermes

# 4. Create server config at ~/.openviking/ov.conf (JSON format!)
```

**Config format is JSON, NOT YAML.** Create `~/.openviking/ov.conf`:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 1933
  },
  "storage": {
    "workspace": "/home/user/.openviking/data",
    "agfs": { "backend": "local" },
    "vectordb": { "backend": "local" }
  },
  "embedding": {
    "dense": {
      "provider": "ollama",
      "api_base": "http://127.0.0.1:11434/v1",
      "model": "nomic-embed-text",
      "dimension": 768
    }
  },
  "vlm": {
    "provider": "openai",
    "api_base": "http://127.0.0.1:11434/v1",
    "api_key": "ollama",
    "model": "guoxuter/ov_intent_analysis_sft:v1_q8",
    "timeout": 30,
    "max_retries": 2
  }
}
```

**Embedding options (from zero-RAM cloud to heaviest local):**

| Option | Setup | RAM | Notes |
|--------|-------|-----|-------|
| **Gemini** (cloud, free) | API key from Google AI Studio | ~0 (remote) | Free tier: 60 RPM, generous daily caps. Model: `gemini-embedding-exp-03-07` (768d). Same dim as nomic-embed-text — compatible with existing vectors. |
| **Jina** (cloud, free) | API key from jina.ai | ~0 (remote) | Free tier: 1M tokens/month, no CC. Model: `jina-embeddings-v3` (1024d). Needs vector DB wipe when switching from 768d. |
| Ollama + nomic-embed-text | `ollama pull nomic-embed-text` | ~300MB (ollama) + 274MB (model) | Lightest local option, pull is fast |
| Local (bge-small-zh-v1.5-f16) | `pip install "openviking[local-embed]"` | ~200MB | Requires `llama-cpp-python` build (slow compile) |
| Remote API (OpenAI/Volcengine) | API key config | ~0 (remote) | Paid API key required |

**Full provider list:** OpenViking also supports `cohere`, `voyage`, `azure`, `dashscope`, `minimax`, `litellm` for embedding. See [OpenViking configuration docs](https://github.com/volcengine/OpenViking/blob/main/docs/en/guides/01-configuration.md).

**VLM options:** OpenViking uses the VLM for automatic memory extraction (profiling, entities, summarization). Options:
- **Gemini** (cloud, free) — `provider: "openai"` with `api_base: https://generativelanguage.googleapis.com/v1beta/openai/`, model `gemini-2.0-flash`. Same Google AI Studio key as Gemini embedding. Vision-capable. Free tier.
- **Ollama** with a small model (`qwen2.5-coder:0.5b`, `gemma3:1b`) — local but RAM/CPU intensive
- **OpenAI/Volcengine** — paid but higher quality
- **OpenAI Codex** — via `openviking-server init` wizard (imports existing auth)

**Ollama api_base MUST include `/v1` suffix** — OpenViking uses the OpenAI-compatible client internally which appends `/embeddings` to the base URL.

**Server startup:**
```bash
# Start server (reads ~/.openviking/ov.conf by default)
openviking-server

# Or with explicit config
openviking-server --config ~/.openviking/ov.conf

# Verify
curl http://127.0.0.1:1933/health    # liveness
curl http://127.0.0.1:1933/ready     # readiness (checks embedding + vectordb)
```

The server takes 15-20 seconds to fully initialize (model loading). The `/ready` endpoint is the definitive health check — it validates embedding, vectordb, and AGFS.

**Pre-restart validation:** After changing `ov.conf`, always run `openviking-server doctor` before restarting the service. The doctor checks config validity, embedding probe, VLM connectivity, and Ollama status — catching issues that would otherwise cause a crash-restart loop (e.g. model name mismatch, VLM timeout misconfiguration).

**Auth modes:**
- `127.0.0.1` binding → dev mode (no API key required)
- `0.0.0.0` binding → requires `server.root_api_key` in config (server refuses to start without it)

**Activation:** Provider takes effect on next session (`/reset`). Existing conversations won't use it.

**Persistence:** The server process dies when the terminal session ends. For permanent operation, set up the systemd user service (see `templates/openviking.service`). Place it at `~/.config/systemd/user/openviking.service`, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now openviking.service
systemctl --user status openviking.service
```

For logs: `journalctl --user -u openviking.service -f`

**Diagnostic quick-start:** When models aren't responding but the server shows healthy, run through the **Deep model check** in `references/openviking-selfhosted.md` — observer models endpoint → journalctl for 429 → direct embedding/VLM probes → search test → vector count. This separates a running server from a working model pipeline.

**Pitfall — Data directory lock:** If a stale `openviking-server` process (e.g. from a previous terminal session) still holds the lock on the workspace directory, the service will fail at startup with `DataDirectoryLocked: Another OpenViking process (PID xxx) is already using the data directory`. Kill the stale PID first before starting the service.

**Pitfall — Model name change breaks startup:** OpenViking stores the embedding model identity in `collection_meta.json` at `~/.openviking/data/vectordb/context/collection_meta.json`. Changing the model name string (e.g. `nomic-embed-text` → `nomic-embed-text:latest`) triggers `EmbeddingRebuildRequiredError: Existing collection embedding metadata does not match current configuration`. Even when dimension (768) is identical. 

**Fix options (in order of preference):**
1. Revert the model name to the original string — Ollama resolves `latest` by default, so `:latest` is redundant.
2. If metadata is already corrupted, stop the server and delete the entire `vectordb/context/` directory (`rm -rf ~/.openviking/data/vectordb/context/`). It will rebuild on next startup.
3. `embedding.dense.allow_metadata_override` does NOT exist as a config field in OpenViking v0.4.7 — do not add it to ov.conf. The error message in the logs suggests it, but it causes `Unknown config field` and startup failure. See note below for the correct way.

**Note on `allow_metadata_override`:** The `EmbeddingRebuildRequiredError` message suggests setting `embedding.allow_metadata_override=true` to keep existing vectors when only provider/model changed. However in OpenViking v0.4.7 this is NOT a valid config field. If dimension hasn't changed, the safest fix is to revert the model name. If you need to change models with a different dimension, delete the context collection and let it rebuild from scratch. The error is a guard against dimension mismatch — if dimension truly changed, deletion is the only safe option.

**VLM model recommendation:** For best local extraction quality, use `guoxuter/ov_intent_analysis_sft:v1_q8` (811 MB) over `qwen2.5-coder:0.5b`. See the reference file for a comparison table.

**Note on pulling large Ollama models:** `ollama pull guoxuter/ov_intent_analysis_sft:v1_q8` is ~811 MB and can exceed the default 2-minute foreground timeout. Use `terminal(background=true, notify_on_complete=true)` for the pull instead, or set a generous timeout.

See `references/openviking-selfhosted.md` for full ov.conf reference and troubleshooting.

### OpenViking — Clean Removal / Decommission

When migrating away from OpenViking (e.g. switching to Mnemosyne, Holographic, or going back to built-in), do a thorough cleanup that preserves memory data for potential recovery:

```bash
# 1. Stop and disable the service
systemctl --user stop openviking.service
systemctl --user disable openviking.service
rm -f ~/.config/systemd/user/openviking.service
systemctl --user daemon-reload

# 2. Backup data before removing (data dir is ~166 MB typical)
cp -a ~/.openviking ~/.openviking.bak.$(date +%Y%m%d_%H%M%S)

# 3. Uninstall Python packages from Hermes venv
~/.hermes/hermes-agent/venv/bin/pip uninstall -y openviking openviking-sdk

# 4. Switch Hermes config back to built-in memory (or to new provider)
hermes config set memory.provider ''

# 5. Verify no residual processes
systemctl --user status openviking  # "could not be found"
ps aux | grep openviking             # empty
```

**What's preserved:**
- `~/.openviking/` (data + config) — left intact, can be re-enabled later
- `~/.openviking.bak.*/` — timestamped backup for recovery
- Hermes falls back to built-in MEMORY.md/USER.md file system

**What's removed:**
- systemd service unit and symlink
- `openviking` + `openviking-sdk` packages from Hermes venv
- `memory.provider` entry in config.yaml (set to `''`)

**To restore later:** reverse the process — reinstall packages, restore ov.conf, recreate systemd unit, restart service, set `memory.provider: openviking`.

> **Pitfall — Don't skip `hermes config set memory.provider ''`:** if you remove OpenViking but leave `provider: openviking` in config.yaml, Hermes throws errors on every session start looking for the missing provider plugin. Always clear the provider field after uninstalling.

### Mnemosyne Setup

Mnemosyne is a first-class Hermes plugin: SQLite-based, zero servers, zero API keys for embeddings. Uses **BAAI/bge-small-en-v1.5** via fastembed (384d, local). Optional local LLM for consolidation sleep.

**Key properties:**
- ~50 MB core RAM (with fastembed ~800 MB, with local LLM ~1.5 GB)
- 25 tools via Hermes plugin (remember, recall, forget, sleep, stats, graph, scratchpad, shared, canonical, etc.)
- SQLite with FTS5 + vector search (sqlite-vec)
- BEAM 4-tier architecture (working, episodic, semantic, procedural)
- Memory banks for per-project isolation
- Knowledge graph (triples + graph traversal)
- Auto-context injection via hooks (on_turn_start, on_session_end, on_memory_write)
- No external API dependencies for embedding — fully local

#### Installation

**Recommended (pipx):**
```bash
export PIPX_DEFAULT_BACKEND=uv
pipx install mnemosyne-hermes
```

**When pipx is not available — standalone venv:** If `pipx` is not installed and the user denies installing it, use a standalone venv + direct install into the Hermes venv:

```bash
# 1. Create a standalone venv (pip wants one for the download)
python3 -m venv ~/.hermes/mnemosyne-venv
~/.hermes/mnemosyne-venv/bin/pip install mnemosyne-hermes

# 2. This creates ~/.hermes/plugins/mnemosyne symlink BUT points at the
#    wrong Python interpreter. Install mnemosyne into the Hermes venv:
~/.hermes/hermes-agent/venv/bin/pip install mnemosyne-hermes

# 3. Register the plugin in Hermes
export HERMES_HOME=~/.hermes
~/.hermes/hermes-agent/venv/bin/mnemosyne-hermes install --force

# 4. Verify the import works
~/.hermes/hermes-agent/venv/bin/python -c "import mnemosyne; print(mnemosyne.__version__)"
# → 3.11.1
```

**Pitfall — Hermes uses a different Python than your system Python:**
Hermes' venv (at `~/.hermes/hermes-agent/venv/`) uses a uv-managed Python (e.g. cpython-3.11). Installing mnemosyne-hermes in your system Python or a standalone venv won't make it importable from Hermes. You MUST run `pip install mnemosyne-hermes` inside the Hermes venv (`~/.hermes/hermes-agent/venv/bin/pip`). The `mnemosyne-hermes install --force` auto-bootstrap may fail with `externally-managed-environment` — that's expected. The fix is the manual pip install into the Hermes venv as shown above.

#### Configuration

```bash
hermes config set memory.provider mnemosyne

# Keep built-in MEMORY.md enabled (the doc recommends this):
hermes config set memory.memory_enabled true
hermes config set memory.user_profile_enabled true

# Provider-specific settings use nested keys:
hermes config set memory.mnemosyne.profile_isolation false
```

**Result in `~/.hermes/config.yaml`:**
```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  provider: mnemosyne
  mnemosyne:
    profile_isolation: false
```

**Nested config keys:** All keys under `memory.mnemosyne` in the config doc use the dotted path `hermes config set memory.mnemosyne.<key>`. Example: `auto_sleep`, `sleep_threshold`, `vector_type`, `ignore_patterns`. See `~/.hermes/skills/devops/memory-provider-setup/references/mnemosyne-setup.md` for the full provider config reference.

#### Plugin Enablement

After installing, the Mnemosyne plugin shows as "not enabled" in `hermes plugins list`. It must be explicitly enabled:

```bash
hermes plugins enable mnemosyne
# → "Plugin mnemosyne enabled. Takes effect on next session."

# Optional — allow tool override if Mnemosyne needs to intercept built-in tools:
hermes plugins enable mnemosyne --allow-tool-override
```

**Pitfall — Do NOT run `hermes tools disable memory`:** The `memory` toolset gates BOTH the built-in `memory` tool AND all Mnemosyne tools. Disabling it removes every memory tool from your model. The correct approach is `hermes config set memory.provider mnemosyne` + `hermes plugins enable mnemosyne` — no toolset toggling needed.

#### Verification

```bash
# Check plugin is registered
hermes plugins list | grep mnemosyne

# Check tools are available
hermes tools list | grep mnemosyne_   # should show 25 tools

# Smoke test
hermes mnemosyne stats

# The config takes effect on NEXT session (not the current one)
# Start a new session with /reset to activate
```

#### Additional Environment Variables (optional)

Set these in `~/.hermes/.env` to customise storage paths:

```bash
MNEMOSYNE_DATA_DIR=~/.hermes/mnemosyne/data
MNEMOSYNE_VEC_TYPE=int8          # float32, int8, bit
MNEMOSYNE_AUTO_SLEEP_ENABLED=true
MNEMOSYNE_LLM_ENABLED=true       # requires LLM API key (optional)
```

See `references/mnemosyne-setup.md` for the full env var reference.

### Hindsight Modes (3-way)

Hindsight has three distinct modes with different resource profiles:

| Mode | Description | Dependencies | RAM | Setup Command |
|------|-------------|-------------|-----|---------------|
| **cloud** | API at api.hindsight.vectorize.io | hindsight-client only | ~5-20 MB | `hermes memory setup` → Cloud |
| **local_embedded** | Embedded daemon (PG + torch/CUDA + LLM) | hindsight-all (~3GB download, ~6GB installed) — pulls PyTorch + full CUDA stack even when using API-only LLMs like Gemini | ~200-400 MB | `hermes memory setup` → Local Embedded |
| **local_external** | Existing Hindsight server | hindsight-client only | ~5-20 MB | `hermes memory setup` → Local External |

**Supported LLM providers for local_embedded mode:**

| Provider | Default Model |
|----------|--------------|
| openai | gpt-4o-mini |
| anthropic | claude-haiku-4-5 |
| **gemini** | **gemini-2.5-flash** |
| groq | openai/gpt-oss-120b |
| openrouter | qwen/qwen3.5-9b |
| minimax | MiniMax-M2.7 |
| ollama | gemma3:12b |
| lmstudio | local-model |
| openai_compatible | your-model-name |

Config stored in `$HERMES_HOME/hindsight/config.json` (profile-scoped). The
setup wizard installs deps via `uv pip install` and prompts for LLM provider
choice, API key, and model. The daemon auto-starts with Hermes and shuts down
after `idle_timeout` (default: 300s).

**Tools exposed:** `hindsight_retain` (store + extract entities/KG), `hindsight_recall`
(multi-strategy retrieval), `hindsight_reflect` (cross-memory LLM synthesis).

### Hindsight local_embedded Gemini setup example

```bash
hermes memory setup hindsight
# Pick "Local Embedded"
# Select "gemini" as LLM provider
# Enter your Gemini API key
# Default model: gemini-2.5-flash
```

## Holographic Details

Holographic is the lightest self-hosted provider — SQLite-only, no servers, ~20-50 MB RAM.

**Tools:**
- `fact_store` — 9 actions: add, search, probe, related, reason, contradict, update, remove, list
- `fact_feedback` — helpful/unhelpful ratings that train trust scores (critical for improving recall quality)

**Key features:**
- **FTS5 full-text search** — SQLite-native keyword search with BM25-style ranking
- **HRR vectors** (with numpy) — Holographic Reduced Representations for semantic similarity. Deterministic SHA-256 encoding, cross-platform reproducible. Without numpy, falls back to FTS5 + Jaccard similarity.
- **Entity resolution** — auto-extracts named entities from fact content via patterns (capitalized phrases, quoted strings, "AKA"). Stored in entities + fact_entities join table.
- **Trust scoring** — facts start at 0.5, rise/lower with feedback, filtered at 0.3 threshold
- **Temporal decay** — optional half-life-based decay for aged facts
- **Auto-Extraction** — optionally scans conversation history at session end to store user preferences and decisions automatically.

**Config:** Under `plugins.hermes-memory-store` in config.yaml. No API keys needed, no Docker, no external services.


**DB:** Single SQLite file at `$HERMES_HOME/memory_store.db`. Schema includes facts, entities, fact_entities, and FTS5 virtual table. Created automatically on first access.

### Holographic — Post-Setup Verification

After configuring Holographic and starting a new session (`/reset` or new
conversation), verify it's working:

```bash
# 1. Check the SQLite DB was created
ls -la ~/.hermes/memory_store.db

# 2. Verify the schema (should have facts, entities, fact_entities, facts_fts)
sqlite3 ~/.hermes/memory_store.db ".tables"

# 3. Import a test fact and search for it (in a Hermes session)
#    Say: "fact_store action=add content='El servidor tiene 4 nucleos'"
#    Then: "fact_store action=search query='nucleos'"

# 4. If you installed numpy for HRR vectors, verify it's loadable
python3 -c "import numpy; print(f'numpy {numpy.__version__}')"
```

**Known tool timeouts:** `hermes memory status` may hang/take >15s on this
hardware — this is a CLI quirk, not a Holographic issue. Use the SQLite
file presence and fact_store tool tests above instead.

See `references/holographic-internals.md` for full schema, retrieval pipeline, and trust math.

## Tools Providers Expose

Most reasoning providers expose these tool shapes:

| Pattern | Purpose | Examples |
|---------|---------|----------|
| `{provider}_profile` | Read/update peer/user card | honcho_profile |
| `{provider}_search` | Semantic/hybrid search | honcho_search |
| `{provider}_context` | Full session context | honcho_context |
| `{provider}_reasoning` | LLM-synthesized answer | honcho_reasoning |
| `{provider}_conclude` | Create/delete conclusions | honcho_conclude |

## Pitfalls (General)

- Only one external provider at a time — the tool schema would bloat otherwise
- Self-hosted providers **still need LLM API keys** for reasoning/embeddings. Self-hosting means you control the data, not the AI
- The agent prompt gets heavier with each provider's injected context — monitor token usage
- Provider takes effect on **next session** (`/reset`), not mid-conversation
- `hermes memory setup` writes config to `$HERMES_HOME/{provider}.json` (profile-local) — the format varies per provider
- Always verify connectivity: `hermes memory status` will show provider health

### Honcho Docker build on low-RAM servers

Honcho's `docker compose build` runs `uv sync` inside `python:3.13-slim-bookworm`,
compiling native Python deps. On servers with **< 4 GB RAM** (tested on 3.3 GB):

- **The build DOES eventually complete** — it took ~2–3 hours on a 4-core/3.3GB
  machine. BuildKit caches aggressively, so reruns are faster.
- **Each image is ~1.73 GB** (api and deriver). Expect ~3.5 GB of Docker images.
- **Steady-state RAM usage** for the full stack (PG + Redis + API + Deriver)
  is ~900 MB – 1.4 GB. During `uv sync` the build peaks at ~1.5 – 1.8 GB.
- **The build does NOT OOM** on 3.3 GB RAM with 4 GB swap, but it is very slow.
  If you need it faster, build on a stronger machine and push the image.

Workaround for faster builds: increase swap before building:

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Then build with limited parallelism:
```bash
DOCKER_BUILDKIT=1 docker compose build --parallel 1
```

If you decide Honcho is too heavy for your server, do a thorough cleanup (see
"### Docker cleanup after failed/abandoned projects" below).

See `references/provider-comparison.md` for detailed resource numbers
for all providers.

### Docker cleanup after failed/abandoned projects

When a self-hosted provider project is abandoned (e.g. build fails, outgrows
server RAM), do a thorough cleanup:

```bash
cd /path/to/project
docker compose down -v      # stop + remove containers + volumes
docker images | grep <name>  # check for residual images
docker volume ls --filter name=<name>
docker network ls --filter name=<name>
docker builder prune --all --force  # purge build cache
rm -rf /path/to/project      # remove cloned repo
```

Verify nothing remains:
```bash
docker ps -a                # no containers
docker images               # no images
docker volume ls            # no volumes
```

Also check the project workspace itself is gone:
```bash
ls -la ~/project_name       # should be "No such file or directory"
```

If working directory was the deleted project, cd to ~/ first before further
shell commands to avoid "getcwd: cannot access parent directories" errors.

### uv pip install --upgrade can break the venv

When running `uv pip install --upgrade <package>` with a large dependency tree
(hindsight-all, etc.), an interrupted download/resolution can leave the venv in
a broken state — packages that existed before may be missing afterward because
uv re-resolves the full dependency tree and only atomically commits at the end.
If the process is killed mid-download, the partial resolution state may remove
packages.

**Symptoms:** `hermes` CLI crashes with `ModuleNotFoundError` for previously
working packages (e.g. `rich`).

**Fix:** Reinstall the missing package directly:
```bash
uv pip install --python /path/to/hermes/venv <missing_package>
```

**Prevention:** For large installs on constrained hardware, prefer
`pip install` (no --upgrade) or install only the subset of packages needed
(e.g. `hindsight-client` instead of `hindsight-all`).

Hermes has built-in context compression (`compression.threshold: 0.5`,
`target_ratio: 0.2`) that auto-trims conversation history. It operates
independently of the memory provider. Even with no external provider,
compression already saves ~50% of context tokens. Memory providers are
_additive_ — they inject relevant facts without re-inserting full history.
You get the best token economy by combining both.

## Provider Comparison Reference

For detailed resource requirements, token-saving mechanisms, RAM estimates,
build workarounds, and a decision tree for constrained hardware, see:

`references/provider-comparison.md`

## Reference Files & Templates

- `references/honcho-selfhosted.md` — Full self-hosting guide for Honcho (Docker, auth, Hermes integration, architecture)
- `references/provider-comparison.md` — Resource comparison, RAM estimates, token-saving mechanisms, decision tree for constrained hardware
- `references/holographic-internals.md` — Holographic SQLite schema, retrieval pipeline, trust scoring math, HRR vector details, tool reference
- `references/openviking-selfhosted.md` — Full ov.conf reference, systemd user service, Ollama integration, **cloud provider config examples (Gemini/Jina)**, troubleshooting, migration steps from Ollama to cloud
- `references/mnemosyne-setup.md` — Mnemosyne Hermes plugin installation (with standalone venv workaround), configuration reference, env vars, tool list, pitfalls, **3-layer population guide (canonical → triples → general memories)**, migration from OpenViking, and first-run behaviour
- `templates/openviking.service` — Systemd user service unit for persistent OpenViking server
