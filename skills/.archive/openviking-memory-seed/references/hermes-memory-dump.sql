# Hermes Memory Store → OpenViking Seed Reference

Extracted from `~/.hermes/memory_store.db` (SQLite) on Jul 4, 2026.
27 facts total from table `facts`.

## Schema

```sql
CREATE TABLE facts (
    fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content         TEXT NOT NULL UNIQUE,
    category        TEXT DEFAULT 'general',
    tags            TEXT DEFAULT '',
    trust_score     REAL DEFAULT 0.5,
    retrieval_count INTEGER DEFAULT 0,
    helpful_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hrr_vector      BLOB            -- skip, Hermes internal
);
```

## Extraction Query

```bash
sqlite3 ~/.hermes/memory_store.db \
  "SELECT fact_id, content, category, tags, created_at FROM facts ORDER BY fact_id"
```

## Category Mapping

| Hermes `category` | OpenViking `category` | Notes |
|---|---|---|
| `user_pref` | `preference` | User profile, preferences, style |
| `general` | `entity` | Factual knowledge (devices, configs, projects) |
| `general` (workflow) | `pattern` | Procedures, protected configs |
| — | `event` | Historical occurrences (not used in this seed) |

## Deduplication Rules Applied

- **facts 4, 5, 6, 22** — all variations of user profile (full-stack dev). Kept #22 (most recent and complete). Dropped the rest.
- **facts 12, 13** — both about Hermes Desktop dashboard. Merged into one entry.
- **facts 25, 26** — both about environment/location. Kept #25 (more detailed).
- **fact 27** — about OpenViking config but STALE (said VLM was `qwen2.5-coder:0.5b` which was superseded by `guoxuter/ov_intent_analysis_sft:v1_q8`). Skipped; wrote fresh entry.
- **facts 2, 19** — both about SSH. Kept #19 (newer, with auth method detail). Dropped #2.

## Result

15 memories stored across 3 categories:
- 4 preferences (model, name, profile, repos)
- 10 entities (SSH, DeskMate, Tuya, Syncthing, agent-browser, youtube_team, dashboard, instances, OpenViking config, RRHH survey)
- 1 pattern (config.yaml protection)

## Resources Uploaded (same session)

Beyond memories, these files were uploaded as OpenViking resources via temp_upload + REST API:

| Resource | File | Root URI |
|---|---|---|
| Config | `~/.hermes/config.yaml` | `viking://resources/config` (3 extracted docs) |
| Cron | `~/.hermes/cron/jobs.json` | `viking://resources/jobs` (1 extracted doc) |
| YouTube Agent | `~/.hermes/agents/youtube_team.yaml` | `viking://resources/youtube_team` (2 extracted docs) |
| YouTube Agent desc | `~/.hermes/agents/youtube_team.md` | `viking://resources/youtube_team_1` |
| All skills (bulk) | TAR of 116 SKILL.md + support files | `viking://resources/hermes-skills-full.tar/` |

Key discovery: `viking_add_resource` times out on local files. Use the REST API directly:
1. `POST /api/v1/resources/temp_upload` (multipart form)
2. `POST /api/v1/resources` (JSON with temp_file_id + reason)

## Verification

After seeding, run:
```
viking_search(query="<relevant keyword>", mode="fast")
```

Expect results with `score > 0.5`. Resources appear with `type: "resource"`.

Check registered resources:
```bash
curl -s "http://localhost:1933/api/v1/fs/ls?uri=viking://resources"
```

If empty, wait for VLM async processing to finish or check `journalctl --user -u openviking.service` for timeout errors.

## What NOT to upload

- **secrets.yaml / .env** — API keys, tokens; don't mix secrets with KB
- **state.db** (25MB) — OpenViking already captures sessions via Hermes peer
- **Archived skills** (`.archive/`) — outdated, not maintained
- **Binary/cache files** (images, audio, node_modules, venvs, .git)

## ⚠️ User Identity Scope Issue (discovered in production)

`viking_remember()` stores memory files under `user/{account_user}/peers/hermes/memories/` (e.g. `user/migbert/peers/hermes/memories/`), but the OpenViking Studio web UI reads from `user/default/memories/`. These are SEPARATE filesystem namespaces.

**Filesystem layout:**
```
~/.openviking/data/viking/
├── migbert/
│   └── user/migbert/
│       └── peers/hermes/memories/   ← where viking_remember() writes
│             ├── entities/   (10 files)
│             ├── preferences/ (4 files)
│             ├── patterns/   (2 files)
│             └── events/     (empty)
├── default/
│   ├── resources/                   ← uploaded resources (config, cron, agents, skills tar)
│   └── user/default/
│       ├── memories/                ← web UI reads from here (initially empty)
│       ├── peers/
│       ├── sessions/
│       └── skills/
└── _system/
```

**Fix: copy files from `migbert` to `default` scope + restart:**
```bash
SRC="$HOME/.openviking/data/viking/migbert/user/migbert/peers/hermes/memories"
DST="$HOME/.openviking/data/viking/default/user/default/memories"
for d in entities preferences patterns events; do
  [ -d "$SRC/$d" ] && cp -r "$SRC/$d" "$DST/"
done
systemctl --user restart openviking.service
```

**Limitation:** The REST API's `POST /api/v1/content/write` cannot create new files under `user/default/memories/` (returns NOT_FOUND). Filesystem-level copy + service restart is the only reliable method discovered so far.

**Web UI verification:** `http://localhost:1933/studio/playground` → expand User > default > memories > {category} — individual `.md` files should appear as clickable tree entries.