# Holographic Memory — Internals Reference

Plugin location: `plugins/memory/holographic/` in the Hermes repo.

## Database Schema

Single SQLite file (default: `$HERMES_HOME/memory_store.db`).

```sql
facts (
    fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content         TEXT NOT NULL UNIQUE,
    category        TEXT DEFAULT 'general',   -- user_pref, project, tool, general
    tags            TEXT DEFAULT '',
    trust_score     REAL DEFAULT 0.5,
    retrieval_count INTEGER DEFAULT 0,
    helpful_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    hrr_vector      BLOB                     -- phase vector (binary)
);

entities (
    entity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    entity_type TEXT DEFAULT 'unknown',
    aliases     TEXT DEFAULT ''
);

fact_entities (
    fact_id   INTEGER REFERENCES facts,
    entity_id INTEGER REFERENCES entities,
    PRIMARY KEY (fact_id, entity_id)
);

-- FTS5 virtual table for full-text search (auto-synced via triggers)
facts_fts USING fts5(content, tags, content=facts, content_rowid=fact_id);
```

## Trust Scoring Math

- Start: `trust_score = 0.5`
- `fact_feedback helpful` → `+0.05`
- `fact_feedback unhelpful` → `-0.10`
- Clamped to `[0.0, 1.0]`
- Filtered from results when `trust_score < min_trust` (default: 0.3)
- Final search score: `relevance * trust_score`

## Retrieval Pipeline

1. **FTS5 candidates** — SQLite full-text search, gets `limit * 3` candidates
2. **Jaccard rerank** — token overlap between query and fact content/tags
3. **HRR similarity** (if numpy available) — cosine similarity of phase vectors
4. **Trust weighting** — `final_score = (fts * 0.4 + jaccard * 0.3 + hrr * 0.3) * trust_score`
5. **Temporal decay** (optional) — `decay = 0.5^(age_days / half_life)`

## HRR Vectors (Holographic Reduced Representations)

Active only when numpy is installed in the Hermes venv. Without numpy, weights
auto-redistribute: FTS5=0.6, Jaccard=0.4, HRR=0.0.

- **Dimension:** 1024 (configurable via `hrr_dim`)
- **Encoding:** Deterministic SHA-256 → phase angles in [0, 2π)
- **Operations:** bind (circular convolution), unbind (circular correlation),
  bundle (circular mean), similarity (cosine)
- **Cross-platform:** Hash-based, so same text → same vector across machines

## Tool Reference

### `fact_store`

| Action | Params | Description |
|--------|--------|-------------|
| `add` | content, [category, tags, entity] | Store a fact with optional entity association |
| `search` | query, [category, min_trust, limit] | Keyword FTS5 search with trust rerank |
| `probe` | entity | All facts linked to a named entity |
| `related` | entity | Entities adjacent to a given entity |
| `reason` | entities[] | Facts connected to ALL specified entities (AND) |
| `contradict` | [min_trust] | Facts making conflicting claims about same entity |
| `update` | fact_id, [content, category, tags, trust_delta] | Modify a fact |
| `remove` | fact_id | Delete a fact |
| `list` | [category, min_trust, limit] | Browse facts |

### `fact_feedback`

| Action | Params | Description |
|--------|--------|-------------|
| `helpful` | fact_id | +0.05 trust, increments helpful_count |
| `unhelpful` | fact_id | -0.10 trust |

## Entity Extraction

Automatic on `fact_store add` — extracts from:
- Capitalized multi-word phrases (`John Smith`)
- Quoted strings (`"project alpha"`)
- "AKA" patterns (`X also known as Y`)
- Stored in `entities` + `fact_entities` join table

## Config Reference

```yaml
plugins:
  hermes-memory-store:
    db_path: ~/.hermes/memory_store.db    # SQLite file path
    auto_extract: false                   # Extract facts on session end
    default_trust: 0.5                    # Trust for new facts
    min_trust_threshold: 0.3             # Filter below this
    temporal_decay_half_life: 0          # Days (0 = disabled)
    hrr_dim: 1024                         # HRR vector dimensions
    hrr_weight: 0.3                       # HRR similarity weight
```

Resources: ~20 MB RAM idle, ~50 MB peak, ~10 MB disk per 1000 facts.
No servers, no Docker, no API keys.
