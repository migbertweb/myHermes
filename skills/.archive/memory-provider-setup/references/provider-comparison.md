# Memory Provider Comparison — Resource & Capability Guide

Real-world resource estimates for Hermes Agent memory providers on a typical
home server (tested on 3.3GB RAM / 4-core / 187GB disk — results may scale).

## At a Glance

| Provider | RAM (idle) | RAM (peak) | Disk | Dependencies | Reasoning | LLM Key Needed? |
|----------|-----------|------------|------|-------------|-----------|-----------------|
| **Built-in** | 0 MB | 0 MB | ~1 MB | None | ❌ No | No |
| **Holographic** | ~20 MB | ~50 MB | ~10 MB | None (SQLite) | Partial¹ | No |
| **Hindsight** (cloud) | ~5 MB | ~20 MB | 0 | API key only | ✅ Sí² | No (use cloud) |
| **Hindsight** (local_embedded) | ~150 MB | ~400 MB | ~6 GB | hindsight-all (emb. PG + LLM key + torch + CUDA ~2.5GB download) | ✅ Sí² | Yes (for local LLM) |
| **Hindsight** (local_external) | ~5 MB | ~20 MB | 0 | hindsight-client + existing server | ✅ Sí² | Optional |
| **Mem0** | ~5 MB | ~20 MB | 0 | API key only | ✅ Sí³ | No (use cloud) |
| **Honcho** | ~900 MB | ~1.8 GB | ~2 GB | Docker: PG+Redis+worker | ✅ Completo⁴ | Yes (for reasoning) |
| **OpenViking** | ~250 MB | ~430 MB | ~95 MB + 1.6 GB venv | pip + systemd service **(56+ deps)** | ✅ Sí | Optional |
| **RetainDB** | ~5 MB | ~15 MB | 0 | API key only | ❌ No | No (use cloud) |
| **ByteRover** | ~5 MB | ~15 MB | ~50 MB | npm CLI + cloud sync | ❌ No | No |
| **Supermemory** | ~5 MB | ~15 MB | 0 | API key only | ❌ No | No |

¹ **Holographic:** `probe` (entity recall), `reason` (AND queries), `contradict`
(detection of conflicting facts). No async LLM background worker — all
reasoning is pre-computed or algebraic, not generative.

² **Hindsight:** full pipeline — `retain` (store + extract entities/knowledge graph),
`recall` (multi-strategy retrieval), `reflect` (cross-memory LLM synthesis).
Closest to Honcho's Deriver for one-off queries. cloud mode uses Hindsight's
own LLM backend (no extra key). local_embedded mode requires your own LLM API key.

³ **Mem0 conclude:** explicit fact extraction via LLM on session end.

⁴ **Honcho:** Deriver (async conclusion extraction), Dialectic (chat endpoint
with injected context), Dreamer (nightly consolidation). Full pipeline.

## Token Saving Mechanisms

| Provider | How It Saves Tokens | Cost per Turn |
|----------|---------------------|---------------|
| **Built-in** | Fixed ~800+500 chars injected; agent chooses what to store | 0 (already in prompt) |
| **Compression** (any) | Auto-compresses context at 50% threshold → 20% target ratio | 1 LLM call per compression |
| **Holographic** | Injects only relevant facts via `fact_store search` | Configurable |
| **Hindsight** | Injects auto-recalled memories + session summaries | Low–mid (local LLM) |
| **Mem0** | Injects semantic search results + auto-extracted facts | API call per turn |
| **Honcho** | Multi-layer: session summary + representation + peer card + dialectic | Configurable cadence (1–5 turns) |

> **Key insight:** Hermes's built-in `compression` feature (threshold: 0.5,
> target_ratio: 0.2) works independently of any memory provider. Even with
> no external provider, compression already saves ~50% of context tokens
> automatically. Memory providers add *targeted* injection — you get relevant
> facts without re-inserting the whole history.

## OpenViking — RAM Breakdown (Measured: v0.4.7, cloud embeddings, ~15 memories)

Even with cloud embeddings (OpenRouter/Gemini — zero local model), the
openviking-server process consumes ~306 MB RSS / ~433 MB cgroup. The RAM
comes from the server process itself, not from any local model:

| Component | RAM | Notes |
|-----------|-----|-------|
| **Tree-sitter parsers** (10 langs) | ~80–150 MB | Python, JS, TS, Rust, Go, Java, C++, C#, PHP, Lua — all loaded at startup, **no config to disable them** |
| **numpy** | ~30–40 MB | Required dependency |
| **LevelDB cache** (vectordb) | ~50–80 MB | Block cache + bloom filters. On-disk: 53 MB (.ldb files) |
| **File parsers** | ~30–50 MB | pdfminer, pdfplumber, openpyxl, python-pptx, python-docx, ebooklib, xlrd — imported even if unused |
| **Uvicorn + FastAPI + httpx** | ~25–30 MB | HTTP framework + async networking |
| **OpenTelemetry SDK** | ~10–20 MB | Tracing exporters |
| **AGFS filesystem tree** | ~15–25 MB | In-memory metadata for viking:// hierarchy |
| **APScheduler + Jinja2 + others** | ~15–20 MB | Background scheduler, template engine, etc. |
| **Python 3.11 runtime** | ~15–20 MB | Base overhead |
| **Total** | **~270–435 MB** | Depends on measurement (RSS vs cgroup) |

**Key takeaway:** The server has **56+ pip dependencies**. Switching to cloud
embeddings saves zero server RAM — the model is remote but the process still
carries the full dependency chain. There is no `--minimal` flag, no config
option to exclude tree-sitter grammars or file parsers. If ~300 MB is too
much, migrate to **Holographic** (no daemon, ~0 MB idle).

**Vectordb detail:** Uses LevelDB (not FAISS). Files are `.ldb` format in
`{workspace}/vectordb/context/store/`. ~53 MB on disk for ~15 memories with
2048d vectors.

## Decision Tree for Constrained Hardware (< 4 GB RAM)

```
¿Necesitas razonamiento deductivo (conclusiones automáticas)?
├── No → ¿Quieres búsqueda semántica entre sesiones?
│        ├── Sí  → Holographic (SQLite local, 20-50 MB)
│        └── No  → Built-in (0 MB extra, ya activo)
└── Sí  → ¿Puedes pagar API cloud?
         ├── Sí  → Mem0 (gratis/freemium, 5-20 MB RAM) o Hindsight cloud (5-20 MB)
         └── No  → Hindsight local_embedded (150-400 MB + ~2.5GB download / ~6GB installed)
                   o Holographic (parcial, sin LLM)
```

## Honcho: The Real Resource Picture

Honcho is the most capable provider but also the heaviest. On a 3.3GB RAM
server with 4 cores:

| Component | RAM | Notes |
|-----------|-----|-------|
| PostgreSQL 15 + pgvector | ~300-500 MB | Grows with data |
| Redis 8.2 | ~50-100 MB | Cache + queue |
| Honcho API (FastAPI) | ~200-400 MB | Per process |
| Deriver worker | ~200-400 MB | Background reasoning |
| Docker build (uv sync) | ~800 MB – 1.8 GB | Peak during `uv sync` (build succeeds but very slow on <4 GB) |
| **Total steady state** | **~900 MB – 1.4 GB** | PG + Redis + API + Deriver |
| **Total with build** | **~1.5 – 1.8 GB** | Build takes ~2–3 hours on 3.3 GB RAM but **does** complete |

**Build issues on low-RAM machines:**
- `docker compose build` runs `uv sync` which compiles native Python deps
- BuildKit executor + uv + Rust compiler (for some deps) can push past 2GB
- The `python:3.13-slim-bookworm` base image is ~120MB compressed
- **Actual experience on 3.3 GB RAM / 4 cores:** the build DOES complete
  (exit 0) after ~2–3 hours. It does NOT OOM, but it is extremely slow.
  BuildKit caches aggressively, so subsequent builds are faster.
- Produces ~1.73 GB images each for api and deriver services

**Honcho build workaround for low-RAM:**

On 3.3 GB RAM the build already completes without extra swap — it's just slow
(~2–3 hours). To speed it up, add swap before building:

```bash
# Increase swap to 4GB+ first (optional — speeds up the build)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Then build with limited parallelism
DOCKER_BUILDKIT=1 docker compose build --parallel 1
```

**Expected output:** images of ~1.73 GB per service (api + deriver).
**Decision criterion:** if your server has < 4 GB total RAM and runs other
services (Hermes, Syncthing, databases), the steady-state ~1 GB Honcho
consumption may leave too little headroom. Consider Holographic (~20–50 MB)
or Hindsight cloud (~5–20 MB) instead.

**If abandoning Honcho, full cleanup:**
```bash
cd ~/honcho
docker compose down -v
docker images | grep honcho
docker volume ls --filter name=honcho
docker network ls --filter name=honcho
docker builder prune --all --force
rm -rf ~/honcho
```

## Hindsight local_embedded — Resource Detail

The local_embedded mode bundles an embedded PostgreSQL daemon within the
Hermes process. Unlike Honcho's full PG+Redis+worker stack, hindsight-embed
uses a lightweight embedded PG that shares the process lifecycle:

| Aspect | Detail |
|--------|--------|
| Install size | ~3GB download, ~6GB installed (hindsight-all pulls torch 507MB, nvidia-cublas 403MB, nvidia-cudnn 349MB, nvidia-cusolver 191MB, nvidia-cusparse 139MB, nvidia-nvjitlink 38MB, nvidia-cufft 204MB, triton 192MB — plus numpy, scipy, transformers, onnxruntime, sentencepiece, pg0-embedded, litellm — 231 packages total) |
| RAM idle | ~150 MB |
| RAM peak (during reflect) | ~400 MB |
| Disk (data) | ~100-200 MB, grows with knowledge graph |
| Dependencies | `uv pip install hindsight-all` |
| LLM support | openai, anthropic, **gemini**, groq, openrouter, minimax, ollama, lmstudio, openai_compatible |
| Daemon lifecycle | Starts with Hermes, shuts down after 300s idle (configurable) |
| Tools | hindsight_retain, hindsight_recall, hindsight_reflect |

## Holographic — Real-world Detail

Uses SQLite + FTS5 + Jaccard + optional HRR vectors:

| Aspect | Detail |
|--------|--------|
| Database | SQLite single file |
| Search | FTS5 full-text search + Jaccard token overlap rerank |
| Vectors | HRR (Holographic Reduced Representations) — requires numpy (~16MB install) |
| Without numpy | Graceful fallback: FTS5 + Jaccard only (keyword, no semantic similarity) |
| Trust scoring | Default 0.5; helpful +0.05, unhelpful -0.10; filtered at min_trust (0.3) |
| Entity resolution | Extracts capitalized names, quoted terms, "aka" → entities + fact_entities tables |
| Tools | `fact_store` (9 actions: add/search/probe/related/reason/contradict/update/remove/list) + `fact_feedback` (helpful/unhelpful) |
| Auto-extract | Optional at session end via `auto_extract: true` |
| RAM (idle) | ~20 MB |
| RAM (peak) | ~50 MB |
| Setup | `hermes memory setup` or manual config.yaml + plugins.hermes-memory-store |

numpy is NOT auto-installed by the setup wizard. Install manually for HRR:
```bash
uv pip install --python /path/to/hermes/venv/bin/python numpy
```

Without numpy all actions still work — just without semantic HRR similarity. FTS5 + Jaccard + trust weighting produce good keyword results.

### When to pick Holographic over Hindsight local_embedded

- RAM constrained (< 100 MB available for memory provider)
- Disk constrained (< 1 GB free)
- Don't want embedded PG daemon lifecycle to manage
- Keyword/FTS5 search is sufficient (no need for knowledge graph)
- Want zero-weight setup: no downloads beyond plugin code

## Decision Guidance

### When to use Built-in only
- You just need Hermes to remember facts you explicitly tell it
- No need for semantic search or cross-session recall
- Memory fits in ~2,200 chars for facts + ~1,375 for profile

### When to use Holographic
- You want semantic search without running any server
- Local-only data (no cloud dependency)
- Your server has < 4 GB RAM
- You want `reason` (AND queries) and `contradict` (conflict detection)

### When to use Hindsight (cloud)
- You want knowledge graph + entity relationships without managing infra
- < 20 MB RAM budget
- No LLM key needed (Hindsight handles LLM server-side)
- Cloud data storage is acceptable

### When to use Hindsight (local_embedded)
- You want knowledge graph + entity relationships locally
- You have an LLM API key (Gemini, OpenAI, Anthropic, etc.)
- Medium resource budget acceptable (~150-400 MB RAM)
- You want full control over data

### When to use Mem0 (cloud)
- You want auto-extraction without managing infra
- < 50 MB RAM is your max budget for the provider
- Cloud data storage is acceptable
- You have/like freemium pricing

### When to use Honcho
- You need the full Deriver → Dialectic → Dreamer pipeline
- Multi-agent with peer-based user modeling
- You have ≥ 4 GB RAM dedicated to it
- You have LLM API keys for reasoning (separate from Hermes's keys)
