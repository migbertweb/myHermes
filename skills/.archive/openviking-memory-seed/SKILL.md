---
name: openviking-memory-seed
description: >-
  Seed OpenViking with the agent's injected context (MEMORY + USER PROFILE),
  Hermes' internal memory store (SQLite), full config/cron/agents/skills as resources,
  or populate the agent's own identity/soul files. Four approaches: context-based
  (fastest, no SQLite), DB extraction (fuller facts), resource upload (durable docs),
  or direct identity/soul seed.trigger:
trigger: user asks to populate, seed, train, or bootstrap OpenViking with existing memories, data, config, or skills; or after setting up a fresh OpenViking instance.
---

# OpenViking Memory Seed

Seed OpenViking with the agent's existing data so vector search immediately returns useful results instead of starting empty.

Four complementary approaches:
  - **Agent Context (Method A)** — seed from the injected MEMORY + USER PROFILE sections. Fastest, no SQLite needed. Best for first-time seed.
  - **DB Memories (Method B)** — individual facts extracted from Hermes `memory_store.db` via `viking_remember()`. Best for fuller historical data.
  - **Resources (Method C)** — full files via `temp_upload + /api/v1/resources`. Best for config, cron, agents, and skills.

All are indexed semantically by OpenViking's VLM and searchable via `viking_search()`.

---

## Method A: Seed from Agent Context (MEMORY + USER PROFILE)

Simplest approach — no SQLite queries needed. The agent's injected MEMORY and USER PROFILE sections
already contain curated, deduplicated facts about the user. Read them from the current context and
store directly.

**Best for:** first-time seed, when memory_store.db is empty or newly configured.

1. **Read the agent's injected context**
   - The MEMORY section (`~1,941 chars`) contains environment facts, tool quirks, tool locations,
     SSH/Syncthing/Tuya details, server config, Hermes Desktop patch notes.
   - The USER PROFILE section (`~1,238 chars`) contains user identity, language, role/title, stack,
     architecture details, preferences, provider config.
   - Both are visible at the top of every conversation in the system prompt.

2. **Audit what's already in OpenViking**
   ```
   viking_search(query="<test keyword>", mode="fast")
   viking_browse(path="viking://user/migbert/memories/preferences", action="list")
   ```
   Check for existing content in preferences/, entities/, events/ directories. Don't re-seed
   data already present.

3. **Categorize facts from context**
   | Source | Category | Example |
   |--------|----------|---------|
   | Language, tone, agent-name, style preferences | `preference` | "El agente se llama Viernes, no Hermes Agent" |
   | User identity, machines, tools, providers | `entity` | "Laptop CachyOS: hostname cachy, IP 192.168.1.17" |
   | Historical milestones, ongoing projects | `event` | "Julio 2026: aplicando a Krona via Senior HCM" |
   | Recurring procedures, known workarounds | `pattern` | skip — these belong in skills, not memory |

4. **Store in batches via viking_remember**
   ```
   viking_remember(category="preference|entity|event", content="<self-contained fact>")
   ```
   - One call per fact. Each fact should be self-contained (readable without context).
   - Batch by category: send all preferences first, then entities, then events.
   - Keep each fact under ~250 chars for concise vector embeddings.

5. **Verify via semantic search**
   ```
   viking_search(query="<keyword from seeded data>", mode="fast")
   ```
   Confirm results appear with `score > 0.3`. If score is too low, the VLM may still be
   processing — wait 10-30s and retry.

6. **(Optional) Copy memories to web UI scope**
   If the user also wants memories visible in the OpenViking Studio web UI, see
   "Web UI visibility" under Post-Seed Steps below.

### Pitfalls (Method A)
- **Don't seed OpenViking config details** — model names, ports, and provider strings
  about OpenViking itself will be stale next week and pollute search results.
- **Don't seed secrets** — API keys, tokens, credentials never belong in OpenViking.
- **Beware of stale environment facts** — verify facts like IPs, hostnames, and tool
  paths against the actual filesystem before storing.
- **Session-specific knowledge** (e.g. "fixed bug X", "submitted PR Y") goes in session
  history, not OpenViking memories. Only durable facts belong here.
- **Viking_remember stores under user/{account_user} scope**, not user/default.
  See "Web UI visibility" below if the user wants memories in the web playground.

---

## Method B: Seed Memories (from memory_store.db)

Use when the agent context is incomplete and the SQLite memory_store.db has
accumulated facts from prior sessions.

1. **Extract facts from Hermes memory store**
   ```bash
   sqlite3 ~/.hermes/memory_store.db \
     "SELECT fact_id, content, category, tags, created_at FROM facts ORDER BY fact_id"
   ```

2. **Analyze and deduplicate**
   - Group facts by topic. Multiple entries for the same user preference (e.g. profile, skills) — keep only the most recent/complete one.
   - Flag facts that are stale (e.g. old VLM model name, old environment info) — skip them or update before storing.
   - Typical categories in Hermes `facts`: `user_pref` (personal preferences), `general` (factual knowledge).

3. **Map to OpenViking categories**
   - `user_pref` → `preference`
   - `general` with factual knowledge → `entity`
   - Workflows/procedures → `pattern`
   - Historical occurrences → `event`

4. **Store each memory**
   ```
   viking_remember(category="preference|entity|pattern|event", content="...")
   ```
   Use one `viking_remember` call per fact. Keep content concise but self-contained.

5. **Verify indexing completed**
   ```
   viking_search(query="<relevant keyword>", mode="fast")
   ```
   Confirm results appear with `score > 0.5` before declaring success.

### Pitfalls (Method B)
- Same as Method A pitfalls above.
- **Dedup is critical**: memory_store.db may have multiple versions of the same
  fact. Keep only the most recent/complete version.
- **Skip stale data**: old model names, old tool paths, old config values that
  have been updated in config.yaml or the filesystem.

---

## Reducing Local Resource Usage (avoid Ollama RAM/CPU tax)

OpenViking with Ollama embedding + VLM consumes significant local RAM/CPU (Ollama keeps models loaded). Replace them with free cloud APIs:

### OpenRouter (with credits or free models)

**embedding**: `provider: "openai"` pointing to OpenRouter's API. `extra_headers` required by OpenRouter for analytics/ranking. **`encoding_format: "float"` is REQUIRED** — the OpenAI Python SDK defaults to `encoding_format=base64`, and OpenRouter returns empty `data: []` when it receives that parameter, causing `Embedding failed: No embedding data received` at startup.

**VLM**: Same `provider: "openai"` — any chat or vision model from OpenRouter. `extra_headers` is NOT supported in the VLM section (only embedding).

```json
{
  "embedding": {
    "dense": {
      "provider": "openai",
      "api_base": "https://openrouter.ai/api/v1",
      "api_key": "<openrouter-api-key>",
      "model": "nvidia/llama-nemotron-embed-vl-1b-v2:free",
      "dimension": 2048,
      "encoding_format": "float",
      "extra_headers": {
        "HTTP-Referer": "https://your-app-name.com",
        "X-Title": "Your App Name"
      }
    }
  },
  "vlm": {
    "provider": "openai",
    "api_base": "https://openrouter.ai/api/v1",
    "api_key": "<openrouter-api-key>",
    "model": "meta-llama/llama-4-scout:free",
    "timeout": 30,
    "max_retries": 2
  }
}
```

Free embedding model: `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048d, $0/M tokens).
Free VLM options: `meta-llama/llama-4-scout:free`, `deepseek/deepseek-chat-v3.1:free`.

**When changing dimension** (e.g. 768→2048): wipe vector DB before restart — `rm -rf ~/.openviking/data/viking/*/vectordb/` or just `~/.openviking/data/vectordb/`.

### Gemini (free tier, user already has API key for Hindsight)

**embedding**: `provider: "gemini"` — model `gemini-embedding-exp-03-07` (768d, same dimension as nomic-embed-text, so existing vectors remain compatible).

**VLM**: `provider: "openai"` pointing to Gemini's OpenAI-compatible endpoint — model `gemini-2.0-flash`.

```json
{
  "embedding": {
    "dense": {
      "provider": "gemini",
      "api_key": "<gemini-api-key>",
      "model": "gemini-embedding-exp-03-07",
      "dimension": 768
    }
  },
  "vlm": {
    "provider": "openai",
    "api_base": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "api_key": "<gemini-api-key>",
    "model": "gemini-2.0-flash",
    "timeout": 30,
    "max_retries": 2
  }
}
```

Gemini free tier: 60 RPM, generous daily limits. No credit card needed for free tier, just a Google account.

### Jina AI embedding + Gemini VLM

```json
{
  "embedding": {
    "dense": {
      "provider": "jina",
      "api_key": "<jina-api-key>",
      "model": "jina-embeddings-v3",
      "dimension": 1024
    }
  },
  "vlm": {
    "provider": "openai",
    "api_base": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "api_key": "<gemini-api-key>",
    "model": "gemini-2.0-flash",
    "timeout": 30,
    "max_retries": 2
  }
}
```

Jina free tier: 1M tokens/month, no credit card needed. Uses 1024d — vectors will be incompatible with existing 768d vectors (requires vector DB wipe).

### Migration steps

```bash
systemctl --user stop openviking.service
# If changing dimension (768→1024): wipe existing vector DB
rm -rf ~/.openviking/data/viking/*/vectordb/
# Edit ov.conf with new provider config
# Validate before starting
openviking-server doctor
systemctl --user start openviking.service
# Wait for re-indexing (VLM processes asynchronously)
```

### Supported embedding providers

From OpenViking docs: `openai`, `azure`, `volcengine`, `vikingdb`, `jina`, `ollama`, `gemini`, `voyage`, `dashscope`, `minimax`, `cohere`, `litellm`, `local`.

### Supported VLM providers

`openai`, `azure`, `volcengine`, `openai-codex`, `kimi`, `glm`.

---

## Session auto-capture verification

Hermes sessions are automatically saved to OpenViking when `memory.provider: openviking` is active in config.yaml. Sessions appear under `user/{account_user}/sessions/` (e.g. `viking://user/migbert/sessions/`).

To verify sessions are being captured:

```
viking_browse(path="viking://user/migbert/sessions", action="list")
```

Each session directory contains:
- `messages.jsonl` — raw conversation
- `history/` — compressed/turn history
- `tool-results/` — tool call outputs

Sessions are stored under the same account user as memories (`migbert`, not `default`). To make them visible in the web UI (which reads `user/default/`), copy session directories:

```bash
cp -r "$HOME/.openviking/data/viking/migbert/user/migbert/sessions" \
      "$HOME/.openviking/data/viking/default/user/default/"
```

---

## Method C: Upload Resources (config, cron, agents, skills)

OpenViking can ingest entire files via its REST API and auto-extract/searchable content from them.

**Do NOT use `viking_add_resource` for local files** — it times out (the tool tries to upload via temp_upload internally but the VLM processing blocks). Use the raw API directly:

### Step-by-step

1. **Upload the file to temp storage**
   ```bash
   UPLOAD=$(curl -s -X POST http://localhost:1933/api/v1/resources/temp_upload \
     -F 'file=@/path/to/file.yaml' \
     | python3 -c "import json,sys; print(json.load(sys.stdin)['result']['temp_file_id'])")
   ```

2. **Register as a resource**
   ```bash
   curl -s -X POST http://localhost:1933/api/v1/resources \
     -H "Content-Type: application/json" \
     -d "{\"temp_file_id\": \"$UPLOAD\", \"reason\": \"Description of what this is\"}"
   ```

3. **The VLM processes it asynchronously** — files are extracted into markdown chunks under `viking://resources/<name>/`.

### What to upload as resources

| Source | File | Reason string |
|---|---|---|
| Config | `~/.hermes/config.yaml` | "Hermes Agent full configuration - providers, toolsets, agent settings, personalities" |
| Cron | `~/.hermes/cron/jobs.json` | "Scheduled cron jobs - system update check, status scripts" |
| Agents | `~/.hermes/agents/<name>.yaml` | "Multi-agent orchestration definition - orchestrator and worker roles" |
| Skills (bulk) | TAR of all `SKILL.md` files | "All active Hermes Agent skills with SKILL.md, DESCRIPTION.md, templates, and scripts" |

### Bulk-uploading skills (the efficient way)

116+ active skills exist. Uploading them individually is impractical. Instead:

```bash
cd ~/.hermes/skills
tar czf /tmp/hermes-skills.tar.gz \
  $(find . -path "./.archive" -prune -o \( -name "SKILL.md" -o -name "DESCRIPTION.md" -o -name "*.yaml" -o -name "*.sh" -o -name "*.py" -o -name "*.tpl" \) -print)
# Then upload the tar via temp_upload + resources (steps 1-2 above)
```

**Note**: TAR resources are registered as directory-like URIs (`viking://resources/hermes-skills-full.tar/`). The VLM extracts and indexes the inner files over time. They become searchable once processing completes.

## Method D: Populate identity.md & soul.md (the agent's own identity)

Beyond seeding user memories, OpenViking stores the agent's **own identity** in two special files
that the Hermes peer reads as its self-concept. The user may expect these to be populated.

**Files** (under the Hermes peer's workspace):
- `<workspace>/viking/{account_user}/user/{account_user}/memories/identity.md`
- `<workspace>/viking/{account_user}/user/{account_user}/memories/soul.md`

The workspace root is defined by `storage.workspace` in `~/.openviking/ov.conf`
(typically `/home/<user>/.openviking/data/`).

**Format**: These files use `<!-- MEMORY_FIELDS -->` JSON blocks that OpenViking parses
for structured metadata. Write both the human-readable markdown AND the metadata block.

```markdown
# identity.md - Quién Soy

- **Nombre:** Viernes
- **Naturaleza:** Agente AI (Hermes Agent - Nous Research)
- **Modelo:** DeepSeek V4 Flash via OpenRouter
- **Idioma:** Español latino neutro

<!-- MEMORY_FIELDS
{
  "creature": "AI agent (Hermes Agent)",
  "name": "Viernes",
  "introduction": "Short description of who the agent is.",
  "memory_type": "identity"
}
-->
```

```markdown
# soul.md - Mi Ser

## Principios
- **Honestidad ante todo.** No invento datos.

## Cómo Trabajo
- Código funcional, optimizado, comentarios mínimos.

<!-- MEMORY_FIELDS
{
  "core_truths": "Honestidad, directo al grano, reporto hechos no aspiraciones.",
  "boundaries": "No invento datos, no accedo sin permiso, no politizo lo técnico.",
  "vibe": "Técnico, preciso, honesto, sin cortesías vacías.",
  "continuity": "My identity lives in this file.",
  "memory_type": "soul"
}
-->
```

**Steps:**
1. Locate the workspace root in `ov.conf` → `storage.workspace`
2. Construct the path: `<workspace>/viking/{account_user}/user/{account_user}/memories/`
3. `write_file` the content preserving the `<!-- MEMORY_FIELDS -->` block
4. Verify with `viking_read(uri="viking://user/{account_user}/memories/identity.md")`

### Pitfalls (Method D)

- **Don't write to `~/.hermes/openviking/`** — that's not OpenViking's storage location.
  Always read `ov.conf` → `storage.workspace` to find the real path.
- **The MEMORY_FIELDS block is mandatory** — without it, OpenViking ignores the file
  for structured querying (though it still indexes it for vector search).
- **identity.md/soul.md live directly under `memories/`** (not `memories/preferences/`
  or `peers/hermes/memories/`). They are at the `user/{user}/memories/` level.
- **Do NOT use `viking_remember` for these** — identity/soul are single files, not
  multiple entries. Write them as files on the filesystem.

---

## Post-Seed: Web UI visibility

If the user wants memories visible in the OpenViking Studio web UI (which reads `user/default/memories/` instead of `user/{account_user}/`):

1. **Copy memory files** from the `migbert` user scope to the `default` user scope:
   ```bash
   SRC="$HOME/.openviking/data/viking/migbert/user/migbert/peers/hermes/memories"
   DST="$HOME/.openviking/data/viking/default/user/default/memories"
   cp -r "$SRC/entities" "$DST/" 2>/dev/null
   cp -r "$SRC/preferences" "$DST/" 2>/dev/null
   cp -r "$SRC/patterns" "$DST/" 2>/dev/null
   cp -r "$SRC/events" "$DST/" 2>/dev/null
   ```

2. **Restart the service** to trigger re-indexing:
   ```bash
   systemctl --user restart openviking.service
   ```

3. **Wait for VLM processing** — newly copied files need to be indexed by the VLM before they appear in search results.

4. **Verify in the web UI** — open `http://localhost:1933/studio/playground`, expand `User > default > memories > entities/preferences/patterns` — individual `.md` files should now be visible.

### Filesystem structure reference

```\n~/.openviking/data/viking/\n├── {account}/\n│   ├── resources/          ← Visible in web UI (config, cron, agents, skills tar)\n│   ├── user/\n│   │   └── default/        ← Web UI scope\n│   │       ├── memories/   ← Copied memories + auto-generated overviews\n│   │       ├── peers/      ← Peer identities\n│   │       ├── sessions/   ← Auto-captured sessions\n│   │       └── skills/     ← Auto-detected skills\n│   └── temp/\n└── {other_account}/\n    └── user/\n        └── {account_user}/\n            ├── memories/\n            │   ├── identity.md         ← Agent's self-identity (MEMORY_FIELDS format)\n            │   ├── soul.md             ← Agent's principles/work-style (MEMORY_FIELDS format)\n            │   ├── preferences/        ← viking_remember(category=\"preference\")\n            │   ├── entities/           ← viking_remember(category=\"entity\")\n            │   ├── events/             ← viking_remember(category=\"event\")\n            │   ├── skills/             ← viking_remember(category=\"skill\"?)\n            │   ├── tools/              ← tool-usage patterns\n            │   └── trajectories/       ← session trajectories\n            └── peers/\n                └── hermes/\n                    └── memories/       ← Where viking_remember() actually stores\n```

## Verification

After uploading, check resources are registered:
```bash
curl -s "http://localhost:1933/api/v1/fs/ls?uri=viking://resources"
```

Then search for content:
```
viking_search(query="something from the resources", mode="fast")
```

Expect results with `type: "resource"` and `score > 0.5`.

---

## Pitfalls

- **`viking_add_resource` times out on local files** — always use the direct temp_upload → resources API instead.
- **Resources API only accepts files from the temp upload directory** — you can't POST a raw path; must upload first, then reference the temp_file_id.
- **Don't store stale config info** about OpenViking itself (model names, ports) — it will be outdated next week and pollutes search results.
- **`encoding_format: "float"` is REQUIRED with OpenRouter**: the OpenAI SDK sends `encoding_format=base64` by default. OpenRouter returns empty `data: []` for base64 requests. Without this field, OpenViking fails with `Embedding failed: No embedding data received` and the circuit breaker opens.
- **`extra_headers` only in embedding section** (OpenViking v0.4.7): the VLM section does NOT accept `extra_headers`. Embedding section does (via `EmbeddingModelConfig`/`OpenAIDenseEmbedder`).
- **Changing embedding dimension requires vector DB wipe**: if new model has a different dimension (e.g. 768→2048), old vectors in `~/.openviking/data/vectordb/` are incompatible. Delete that dir and let OpenViking rebuild from scratch on restart.
- **Model name change breaks startup**: OpenViking checks `collection_meta.json` metadata. Changing the embedding model string (e.g. `nomic-embed-text` → `nomic-embed-text:latest`) triggers `EmbeddingRebuildRequiredError`. Either revert to the original name, or if metadata is already corrupted, delete `~/.openviking/data/vectordb/context/` and let it rebuild.
- **`embedding.dense.allow_metadata_override` is NOT a valid config field** in OpenViking v0.4.7 — don't add it. It causes startup failure with `Unknown config field`.
- **Run `openviking-server doctor`** after any config change to validate before restarting.
- **Facts table columns**: `fact_id | content | category | tags | trust_score | retrieval_count | helpful_count | created_at | updated_at | hrr_vector` (binary embedding, skip it).
- **Secrets (secrets.yaml, .env) should NEVER go into OpenViking** — the knowledge base is not a secrets store.
- **State.db (25MB) should NOT be uploaded** — OpenViking already captures sessions automatically via its Hermes peer integration.
- **Memory entry for OpenViking itself gets stale fast** — after seeding, update your memory entry about OpenViking to remove stale model/port info.
- **Find workspace path in `ov.conf`, not by guessing**: `storage.workspace` in `~/.openviking/ov.conf` is the authoritative path. Don't assume `~/.hermes/openviking/` — that path doesn't exist.

## Related files

- `references/hermes-memory-dump.sql` — Full extraction query, schema, category mapping table, and dedup rules from the initial seed run.