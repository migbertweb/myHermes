# Mnemosyne Setup — Reference

## Version

- `mnemosyne-memory` 3.14.0
- `mnemosyne-hermes` 0.5.0

## Architecture

```
┌────────────────────┐
│  Hermes Agent      │
│  (venv)            │──── SQLite ───▶ ~/.hermes/mnemosyne/data/memory.db
│                    │         ┌─────────────────────────────┐
│  mnemosyne plugin  │         │  fastembed (BAAI/bge-small) │
│  (25 tools)        │         │  FTS5 + sqlite-vec          │
└────────────────────┘         │  BEAM tiers (W/EP/SP/PR)    │
                               │  Knowledge graph            │
                               └─────────────────────────────┘
```

Zero servers. Zero API keys for embeddings. Single SQLite file.

## Installation Workflow (when pipx is unavailable)

This is the complete sequence used in a real migration from OpenViking.

### Clean old provider (OpenViking)

```bash
# Stop + disable service
systemctl --user stop openviking.service
systemctl --user disable openviking.service
rm -f ~/.config/systemd/user/openviking.service
systemctl --user daemon-reload

# Backup data
cp -a ~/.openviking ~/.openviking.bak.$(date +%Y%m%d_%H%M%S)

# Uninstall packages from Hermes venv
~/.hermes/hermes-agent/venv/bin/pip uninstall -y openviking openviking-sdk

# Clear config
hermes config set memory.provider ''

# Verify nothing remains
systemctl --user status openviking      # "could not be found"
ps aux | grep openviking                 # empty
ss -tlnp | grep 1933                     # empty
which openviking                          # not found
~/.hermes/hermes-agent/venv/bin/pip list 2>/dev/null | grep openvi  # empty
```

### Install Mnemosyne into Hermes venv

```bash
# Option A: pipx (the doc recommendation)
export PIPX_DEFAULT_BACKEND=uv
pipx install mnemosyne-hermes

# Option B: standalone venv → Hermes venv (when pipx unavailable/denied)
python3 -m venv ~/.hermes/mnemosyne-venv
~/.hermes/mnemosyne-venv/bin/pip install mnemosyne-hermes
~/.hermes/hermes-agent/venv/bin/pip install mnemosyne-hermes
export HERMES_HOME=~/.hermes
~/.hermes/hermes-agent/venv/bin/mnemosyne-hermes install --force

# Verify
~/.hermes/hermes-agent/venv/bin/python -c "import mnemosyne; print(mnemosyne.__version__)"
# → 3.14.0
```

### Configure Hermes

```bash
hermes config set memory.provider mnemosyne
hermes config set memory.memory_enabled true
hermes config set memory.user_profile_enabled true
hermes config set memory.mnemosyne.profile_isolation false
```

Result in `~/.hermes/config.yaml`:
```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  provider: mnemosyne
  mnemosyne:
    profile_isolation: false
```

### Enable the plugin

```bash
hermes plugins enable mnemosyne
# Optional tool override grant:
hermes plugins enable mnemosyne --allow-tool-override
```

### Verify

```bash
hermes plugins list | grep mnemosyne     # should be "enabled"
hermes tools list | grep mnemosyne_      # 25 tools
hermes mnemosyne stats                   # memory stats
hermes mnemosyne doctor                  # PII-safe diagnostics (not 'diagnose')
```

## Hermes Provider Config Reference

These keys live under `memory.mnemosyne` in `~/.hermes/config.yaml`.
Set with `hermes config set memory.mnemosyne.<key> <value>`.

| Key | Default | Description |
|-----|---------|-------------|
| `auto_sleep` | `False` | Auto-run sleep() when working memory exceeds threshold |
| `sleep_threshold` | `50` | Working memory count before auto-sleep triggers |
| `vector_type` | `int8` | Vector storage type (float32, int8, bit) |
| `ignore_patterns` | `[]` | Regex patterns to filter from memory storage |
| `profile_isolation` | `False` | Per-profile memory isolation via Mnemosyne banks |
| `shared_surface_path` | `data/shared/mnemosyne.db` | SQLite path for shared surface memories |
| `shared_surface_read` | `False` | Merge shared-surface results into private bank recall |
| `skip_contexts` | `cron,flush,subagent,background,skill_loop` | Agent contexts to skip Mnemosyne init |
| `sync_roles` | `['user', 'assistant']` | Conversation roles to autosave in sync_turn() |

## Environment Variables (full reference)

### Storage & Data
| Variable | Default | Description |
|----------|---------|-------------|
| `MNEMOSYNE_DATA_DIR` | `~/.hermes/mnemosyne/data` | Directory for database, logs, models |
| `MNEMOSYNE_HOME` | `~/.hermes/mnemosyne` | Override home directory |
| `MNEMOSYNE_SHARED_DB_PATH` | `data/shared/mnemosyne.db` | Shared surface memory DB path |
| `MNEMOSYNE_BLOB_DIR` | — | Directory for blob storage |
| `MNEMOSYNE_AUTO_MIGRATE` | `1` | Auto-migrate DB schema on startup |

### Memory Tiers & Eviction
| Variable | Default | Description |
|----------|---------|-------------|
| `MNEMOSYNE_WM_MAX_ITEMS` | `10000` | Max working memory items |
| `MNEMOSYNE_WM_TTL_HOURS` | `24` | Working memory TTL |
| `MNEMOSYNE_EP_LIMIT` | `50000` | Max episodic memories per recall |
| `MNEMOSYNE_SP_MAX` | `1000` | Max scratchpad entries |
| `MNEMOSYNE_RECENCY_HALFLIFE` | `168` | Recency decay halflife in hours (1 week) |
| `MNEMOSYNE_TEMPORAL_HALFLIFE_HOURS` | `24` | Temporal weighting halflife |
| `MNEMOSYNE_SLEEP_BATCH` | `5000` | Batch size for sleep consolidation |

### Auto Sleep
| Variable | Default | Description |
|----------|---------|-------------|
| `MNEMOSYNE_AUTO_SLEEP_ENABLED` | `false` | Enable automatic sleep consolidation |
| `MNEMOSYNE_SESSION_END_TIMEOUT` | `15` | Max seconds for session-end sleep |
| `MNEMOSYNE_AUTO_SLEEP_TIMEOUT` | `5` | Max seconds for auto-sleep cycle |
| `MNEMOSYNE_SHUTDOWN_DRAIN_TIMEOUT` | `2` | Max seconds to drain LLM queue on shutdown |

### Embeddings (fastembed — local, no API key needed)
| Variable | Default | Description |
|----------|---------|-------------|
| `MNEMOSYNE_VEC_TYPE` | `int8` | Vector storage format (int8, float32, float16, binary) |
| `MNEMOSYNE_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | fastembed model |
| `MNEMOSYNE_EMBEDDING_DIM` | `384` | Embedding dimension |
| `MNEMOSYNE_EMBEDDING_API_URL` | `https://openrouter.ai/api/v1` | Cloud API endpoint |
| `MNEMOSYNE_NO_EMBEDDINGS` | `false` | Disable dense vector retrieval entirely |
| `MNEMOSYNE_EMBEDDINGS_VIA_API` | `false` | Force cloud API mode |

### LLM (Optional — for sleep consolidation)
| Variable | Default | Description |
|----------|---------|-------------|
| `MNEMOSYNE_LLM_ENABLED` | `true` | Enable LLM summarization during sleep |
| `MNEMOSYNE_LLM_BASE_URL` | — | OpenAI-compatible API base URL |
| `MNEMOSYNE_LLM_API_KEY` | — | API key for remote LLM |
| `MNEMOSYNE_LLM_MODEL` | — | Model identifier |
| `MNEMOSYNE_LLM_MAX_TOKENS` | `2048` | Max output tokens |
| `MNEMOSYNE_FORCE_LOCAL` | `false` | Skip remote LLM, use local GGUF model |
| `MNEMOSYNE_LLM_REPO` | `openbmb/MiniCPM5-1B-GGUF` | HuggingFace repo for GGUF |
| `MNEMOSYNE_LLM_FILE` | `MiniCPM5-1B-Q4_K_M.gguf` | GGUF filename |

### Scoring Weights (Hybrid Ranking)
| Variable | Default | Description |
|----------|---------|-------------|
| `MNEMOSYNE_VEC_WEIGHT` | `0.5` | Vector similarity weight |
| `MNEMOSYNE_FTS_WEIGHT` | `0.3` | Full-text search weight |
| `MNEMOSYNE_IMPORTANCE_WEIGHT` | `0.2` | Importance score weight |

### Entity Extraction
| Variable | Default | Description |
|----------|---------|-------------|
| `MNEMOSYNE_EXTRACTION_MODEL` | `google/gemini-2.5-flash` | Model for entity/fact extraction via OpenRouter |
| `MNEMOSYNE_EXTRACTION_PROMPT` | — | Custom extraction prompt |

## Tool Reference

Mnemosyne exposes 25 tools through the Hermes plugin. Key tools:

| Tool | Purpose |
|------|---------|
| `mnemosyne_remember` | Store memories with entity/fact extraction |
| `mnemosyne_recall` | Hybrid vector+FTS5 search with configurable weights |
| `mnemosyne_sleep` | Run consolidation — compress working memory into episodic (CLI: `hermes mnemosyne sleep`) |
| `mnemosyne_stats` | Memory system statistics (CLI: `hermes mnemosyne stats`) |
| `mnemosyne_forget` | Permanently delete a memory by ID |
| `mnemosyne_update` | Update content or importance of an existing memory |
| `mnemosyne_doctor` / `hermes mnemosyne doctor` | PII-safe diagnostics — NOT `mnemosyne_diagnose` |
| `mnemosyne_triple_add` / `mnemosyne_triple_query` | Knowledge graph operations |
| `mnemosyne_graph_link` / `mnemosyne_graph_query` | Semantic graph traversal |
| `mnemosyne_scratchpad_write` / `mnemosyne_scratchpad_read` / `mnemosyne_scratchpad_clear` | Temporary workspace |
| `mnemosyne_shared_remember` / `mnemosyne_shared_recall` / `mnemosyne_shared_forget` / `mnemosyne_shared_stats` | Cross-agent shared surface |
| `mnemosyne_remember_canonical` / `mnemosyne_recall_canonical` | Owner-scoped canonical facts |
| `mnemosyne_validate` / `mnemosyne_invalidate` | Memory attestation |
| `mnemosyne_export` / `mnemosyne_import` | Backup and migration |
| `mnemosyne_get` | Retrieve by ID |

## Population Guide — 3-Layer Pattern

When populating Mnemosyne with essential agent+user data for the first time, use this layered approach:

### Layer 1: Canonical (stable identity & preferences)

Use `mnemosyne_remember_canonical()` for single-source-of-truth facts that rarely change:
- `category="identity"` — name, language, email, location, role, phone
- `category="preference"` — reporting style, repo visibility, communication tone
- `category="project"` — current transition, work context, key paths

Canonical entries have `trust_tier: CANONICAL` and are returned as `fact_match: true` on recall. They survive sleep consolidation untouched.

### Layer 2: Triples (relational facts)

Use `mnemosyne_triple_add()` for structured subject-predicate-object facts:
- SSH hosts: `subject="ssh-host-{name}"`, `predicate="has_address"|"user"|"auth"`
- Provider/model mappings: `subject="migbert"`, `predicate="uses_provider"|"uses_model"`
- Capabilities: `subject="migbert"`, `predicate="speaks"` (one per language)
- Infrastructure: server configs, script locations, tool paths

Query with `mnemosyne_triple_query()` by subject, predicate, or object. Triples are organized as a knowledge graph — link subjects via `mnemosyne_graph_link()` for graph traversal.

### Layer 3: General memories (environment, conventions, history)

Use `mnemosyne_remember()` for free-text facts:
- Host/environment description (OS, kernel, desktop)
- Hermes configuration snapshot
- Desktop fonts, UI conventions
- Tool-specific commands and conventions
- Migration history and backup locations

Set `importance` (0.0-1.0) and `scope="global"` for cross-session availability.

### Verification

After populating, verify all three layers respond:
```bash
mnemosyne_recall(query="...")                # layer 3 + layer 1 (canonical shows as fact_match)
mnemosyne_recall_canonical(category)         # list all canonical in a category
mnemosyne_triple_query(subject|predicate)    # triples by relationship
```

### First-Run Behaviour

On first invocation of any Mnemosyne tool in a session, fastembed downloads the embedding model (BAAI/bge-small-en-v1.5, ~67 MB) from HuggingFace Hub. This produces progress bars:
```
Fetching 5 files: 100% ...
Download complete: 67.2M/67.2M
```
The model is cached at `~/.cache/huggingface/hub/` — subsequent sessions are instant.

### Consolidation

`hermes mnemosyne sleep` (or `mnemosyne_sleep` tool) consolidates working memories into episodic tier. Returns `"status": "no_op"` when working memory is fresh or empty — that's normal, not an error. Consolidation happens automatically on session end if configured.

## Pitfalls

### Dead plugin symlink after package removal
If `mnemosyne-hermes` was uninstalled from the venv (e.g. `pip uninstall`, venv rebuild) but the config still has `provider: mnemosyne` and the plugin symlink persists at `~/.hermes/plugins/mnemosyne`, `hermes tools list | grep mnemosyne_` shows 0 tools. The symlink points to an empty or non-existent site-packages directory.

**Fix:**
```bash
~/.hermes/hermes-agent/venv/bin/pip install mnemosyne-hermes
export HERMES_HOME=~/.hermes
~/.hermes/hermes-agent/venv/bin/mnemosyne-hermes install --force
hermes plugins enable mnemosyne
```

The data in `~/.hermes/mnemosyne/data/mnemosyne.db` survives — it's not tied to the Python package. Verify with `hermes mnemosyne stats`.

### Plugins not auto-enabled
After installing mnemosyne-hermes, the plugin shows as "not enabled" in `hermes plugins list`. Must manually run `hermes plugins enable mnemosyne`. The `install --force` script only creates the symlink in `~/.hermes/plugins/` — it does NOT activate the plugin.

### Python interpreter mismatch
Hermes uses a uv-managed Python (cpython-3.11 at `~/.local/share/uv/python/`). The venv symlink at `~/.hermes/hermes-agent/venv/bin/python` points there. Installing mnemosyne in any other Python won't make it importable by Hermes. Always install via `~/.hermes/hermes-agent/venv/bin/pip install mnemosyne-hermes`.

### `hermes tools disable memory` kills ALL memory tools
The `memory` toolset gates BOTH the built-in `memory` tool AND all provider tools. If Mnemosyne tools don't show up, check that you haven't run `hermes tools disable memory`. Re-enable with `hermes tools enable memory`.

### Config changes take effect on next session
`hermes config set` and `hermes plugins enable` both say "takes effect on next session". Start `/reset` or a new conversation to activate.

### `hermes memory status` is misleading
This command always prints "Built-in: always active" regardless of provider settings. It cannot tell you whether Mnemosyne is working. Use `hermes doctor | grep -i memory` or `hermes tools list | grep mnemosyne_` instead.
