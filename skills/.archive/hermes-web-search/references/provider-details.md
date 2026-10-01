# Provider-specific setup details

Gathered from Hermes Agent docs at hermes-agent.nousresearch.com/docs.

## Firecrawl

- **Env vars:** `FIRECRAWL_API_KEY` (required for cloud), `FIRECRAWL_API_URL` (optional, self-hosted)
- **Capabilities:** Search, Extract, Crawl
- **Free tier:** 500 credits/month
- **Key source:** https://firecrawl.dev
- **Self-hosted:** Set `FIRECRAWL_API_URL=http://localhost:3002`. When set, API key is optional (auth can be disabled server-side via `USE_DB_AUTHENTICATION=false`).
- **Auto-detection:** Yes — highest priority when `FIRECRAWL_API_KEY` or `FIRECRAWL_API_URL` is set.
- **Notes:** Default backend. Best all-around choice for most users.

## Tavily

- **Env var:** `TAVILY_API_KEY`
- **Capabilities:** Search, Extract
- **Free tier:** 1,000 searches/month
- **Key source:** https://app.tavily.com
- **Auto-detection:** Yes — third priority (after Firecrawl, Parallel).
- **Notes:** AI-optimised search. Good alternative to Firecrawl.

## Brave Search (free tier)

- **Env var:** `BRAVE_SEARCH_API_KEY`
- **Capabilities:** Search only. Does NOT support Extract.
- **Free tier:** 2,000 queries/month
- **Key source:** https://api.search.brave.com
- **Auto-detection:** No — not in the auto-detection chain.
- **Notes:** Search-only. Must pair with Firecrawl/Tavily/Exa for `web_extract`.

## DDGS (DuckDuckGo)

- **Env var:** None (no API key needed)
- **Capabilities:** Search only. Does NOT support Extract.
- **Free tier:** Unlimited
- **Key source:** N/A
- **Auto-detection:** No — must set explicitly.
- **Notes:** Uses the `ddgs` Python package (v9.x, by deedy5) under the hood. Auto-installed on first use if missing (`pip install ddgs`). Import: `from ddgs import DDGS`. Completely free and unlimited, but fewer features than Firecrawl/Tavily.

## SearXNG

- **Env var:** `SEARXNG_URL`
- **Capabilities:** Search only. Does NOT support Extract.
- **Free tier:** Free (requires self-hosting or a public instance)
- **Auto-detection:** Yes — fifth priority (after Exa).
- **Notes:** Privacy-respecting metasearch engine. Needs JSON format enabled in settings.yml (`formats: [html, json]`). See docs for Docker setup.

### Self-hosting with Docker (recommended)
```yaml
# docker-compose.yml
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8888:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8888/
    restart: unless-stopped
```

After starting, enable JSON API:
```
docker cp searxng:/etc/searxng/settings.yml ./searxng/settings.yml
```
Edit to add `formats: [html, json]` under `search:`, then restart.

### Public instances
Listed at https://searx.space — filter by instances with JSON format enabled.

## Exa

- **Env var:** `EXA_API_KEY`
- **Capabilities:** Search, Extract
- **Free tier:** 1,000 searches/month
- **Key source:** https://exa.ai
- **Auto-detection:** Yes — fourth priority (after Tavily).
- **Notes:** Neural/semantic search. Good for research and conceptually related content.

## Parallel

- **Env var:** `PARALLEL_API_KEY`
- **Capabilities:** Search, Extract
- **Free tier:** Paid only
- **Key source:** https://parallel.ai
- **Auto-detection:** Yes — second priority (after Firecrawl).
- **Notes:** AI-native search with deep research capabilities.

## xAI (Grok)

- **Env var:** `XAI_API_KEY` or OAuth via `hermes auth login xai-oauth`
- **Capabilities:** Search only. Does NOT support Extract.
- **Free tier:** Paid (SuperGrok or per-token)
- **Auto-detection:** No — must be set explicitly via `web.backend: "xai"`. Having `XAI_API_KEY` set does NOT auto-route web through xAI.
- **Notes:** LLM-generated results, not index-backed. Titles, descriptions, and URL choice are model output.

### Additional config options
```yaml
web:
  backend: "xai"
  xai:
    model: grok-build-0.1        # reasoning model for web_search
    allowed_domains:             # max 5, mutex with excluded_domains
      - arxiv.org
    excluded_domains:            # max 5
      - example-spam.com
    timeout: 90
```

## Per-capability split config (the "fallback" workaround)

Since Hermes has no native web search backend fallback chain, use this pattern to combine a free/search-only provider with a paid/extract provider:

```yaml
web:
  search_backend: "ddgs"        # free search
  extract_backend: "firecrawl"  # paid extract
```

Priority order:
1. `web.search_backend` / `web.extract_backend` (explicit)
2. `web.backend` (shared fallback)
3. Auto-detect from env vars

## Auxiliary web_extract model

The `web_extract` tool runs long page content through an auxiliary LLM for summarization. By default (`auxiliary.web_extract.provider: "auto"`), it uses your main chat model. To save costs on expensive reasoning models:

```yaml
auxiliary:
  web_extract:
    provider: openrouter
    model: google/gemini-3-flash-preview
    timeout: 360
```

Size thresholds for summarization:
| Page size         | Behavior                                                    |
|-------------------|-------------------------------------------------------------|
| < 5,000 chars     | Returned as-is                                              |
| 5k – 500k chars   | Single-pass summary via aux model (~5k chars output)        |
| 500k – 2M chars   | Chunked: 100k-char chunks in parallel, then synthesis       |
| > 2M chars        | Refused with hint to use a more focused URL                 |
