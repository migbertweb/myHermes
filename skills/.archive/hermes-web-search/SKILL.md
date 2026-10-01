---
name: hermes-web-search
description: "Configure web search and extract backends in Hermes Agent — Firecrawl, Tavily, Brave, DDGS, SearXNG, Exa, and others."
triggers:
  - "configurar web search"
  - "firecrawl setup"
  - "tavily api key"
  - "brave search hermes"
  - "web backend fallback"
  - "search_backend extract_backend"
  - "hermes web tools"
---

# Hermes Web Search & Extract Configuration

Hermes Agent has two model-callable web tools: `web_search` (search the web) and `web_extract` (fetch/extract URL content). Both are configured through a single backend selection, configurable per-capability.

## Supported Backends

| Provider       | Env Var                | Search | Extract | Free tier           |
|----------------|------------------------|--------|---------|---------------------|
| Firecrawl      | `FIRECRAWL_API_KEY`    | ✔      | ✔       | 500 credits/mo      |
| Tavily         | `TAVILY_API_KEY`       | ✔      | ✔       | 1,000 searches/mo   |
| Brave          | `BRAVE_SEARCH_API_KEY` | ✔      | —       | 2,000 queries/mo    |
| DDGS (DDG)     | (no key)               | ✔      | —       | Free                |
| SearXNG        | `SEARXNG_URL`          | ✔      | —       | Free (self-hosted)  |
| Exa            | `EXA_API_KEY`          | ✔      | ✔       | 1,000 searches/mo   |
| Parallel       | `PARALLEL_API_KEY`     | ✔      | ✔       | Paid                |
| xAI (Grok)     | `XAI_API_KEY`          | ✔      | —       | Paid                |

**Note:** Brave, DDGS, SearXNG, and xAI are **search-only** — pair them with Firecrawl/Tavily/Exa for `web_extract`.

## Configuration

### Environment variables (in `~/.hermes/.env`)

```env
FIRECRAWL_API_KEY=fc-xxx          # firecrawl.dev
TAVILY_API_KEY=tvly-xxx           # app.tavily.com
BRAVE_SEARCH_API_KEY=xxx          # api.search.brave.com
SEARXNG_URL=http://localhost:8888 # self-hosted SearXNG
EXA_API_KEY=xxx                   # exa.ai
PARALLEL_API_KEY=xxx              # parallel.ai
XAI_API_KEY=xxx                   # xAI (Grok)
```

### `config.yaml` keys

```yaml
web:
  backend: "firecrawl"            # single backend for both search & extract
  search_backend: "brave-free"    # overrides backend for web_search only
  extract_backend: "firecrawl"    # overrides backend for web_extract only
```

Valid values: `firecrawl`, `tavily`, `brave-free`, `ddgs`, `searxng`, `exa`, `parallel`, `xai`

### Auto-detection (when both `backend` and `*_backend` are empty)

Hermes picks the first available backend from env vars, in this order:
`FIRECRAWL_API_KEY` → `PARALLEL_API_KEY` → `TAVILY_API_KEY` → `EXA_API_KEY` → `SEARXNG_URL`

`xai` is **not** in auto-detection — must be set explicitly via `web.backend: "xai"`.

## The "fallback" caveat

**There is no native web search backend fallback chain in Hermes.** Unlike LLM providers (which have `fallback_providers`), the web backend is a single choice. If your primary backend exhausts credits, the tool fails — there's no automatic failover.

**Practical workaround: per-capability split.** Set different providers for search vs extract. This doesn't provide true fallback but lets you e.g. use a free/search-only provider for searches and a paid full-featured one for extraction:

```yaml
web:
  search_backend: "ddgs"        # free, unlimited, no key needed
  extract_backend: "firecrawl"  # Firecrawl only when you need page content
```

Or:
```yaml
web:
  search_backend: "brave-free"  # 2,000 free queries/mo
  extract_backend: "firecrawl"
```

## Firecrawl specifics

- Get key at https://firecrawl.dev
- Self-hosted: set `FIRECRAWL_API_URL=http://localhost:3002` (key becomes optional)
- 500 credits/month free
- Supports search, extract, and crawl

## Tavily specifics

- Get key at https://app.tavily.com
- 1,000 searches/month free
- AI-optimised search + extract

## Brave specifics

- Get key at https://api.search.brave.com
- 2,000 queries/month free
- Search only — needs separate extract provider

## DDGS (DuckDuckGo) specifics

- **No API key needed** — completely free
- Uses the `ddgs` Python package (auto-installed on first use)
- Search only

## Applying config changes

Use `hermes config set` for individual keys instead of editing config.yaml directly:

```bash
hermes config set web.search_backend ddgs
hermes config set web.extract_backend firecrawl
```

Nested keys work with dot notation: `hermes config set web.backend tavily`.

## Verification

```bash
# Check detected backend
hermes setup | grep "Web Search"

# Firecrawl test
source ~/.hermes/.env
curl -s -X POST https://api.firecrawl.dev/v1/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -d '{"query":"test","limit":1}' | python3 -m json.tool

# DDGS test (no API key needed)
python3 -c "
from ddgs import DDGS
with DDGS() as ddgs:
    for r in ddgs.text('test', max_results=2):
        print(f\"{r['title']}: {r['href']}\")
"
```

## Troubleshooting pitfalls

- `web_extract` returns "search-only backend" → your search_backend provider can't extract. Set `web.extract_backend` to Firecrawl/Tavily/Exa.
- Firecrawl 500 credits exhaust fast on heavy usage → consider adding a second key, switching to Tavily, or self-hosting Firecrawl.
- SearXNG returns 403 → JSON format disabled in settings.yml. Add `formats: [html, json]` to `search:` section.
