---
name: web-extraction
category: web
description: Use when extracting content from web links or web service APIs.
---

## Procedure

### Method 1: Web Page Extraction (HTML/Markdown)
1. Use the `web_extract` tool to extract content from a given URL.
2. If the URL points to a file, download it using `terminal` with `wget` or `curl`.
3. If the content is not available or the tool fails, try an alternative approach.

### Method 2: REST API Extraction (JSON/Data)
1. Identify if the target service has a documented REST API (check `/api`, `/swagger`, `/docs`, or docs site).
2. Use `httpx`/`requests` in Python to call API endpoints directly — more reliable than scraping.
3. Handle authentication: API keys, Bearer tokens, Basic Auth, or session cookies.
4. Implement pagination, rate limiting, and retry logic for production use.
5. Validate responses with Pydantic models for type safety.

## Pitfalls
- **Large Files**: Some URLs may point to large files that exceed size limits. Download manually or stream.
- **Tool Limitations**: Web extraction tools may have unsupported file types or size restrictions.
- **API Changes**: REST APIs can change; version your client and monitor for breaking changes.
- **Authentication**: Never hardcode credentials. Use environment variables or secret managers.
- **Rate Limits**: Respect `Retry-After` headers; implement exponential backoff.
- **SSL Verification**: Disable only for dev (`verify_ssl=False`); production must verify.

## Tools
- `web_extract`: Extracts content from web pages and supported file types.
- `terminal`: Downloads files using `wget` or `curl`.
- `httpx` / `requests`: For REST API calls in Python scripts.
- `browser_exec`: For JavaScript-heavy sites requiring browser automation.

## Common Patterns

### Filebrowser API Example
```python
import httpx

async def get_videos(base_url, user, passwd, folder="/"):
    async with httpx.AsyncClient() as client:
        # Auth
        resp = await client.post(f"{base_url}/api/auth/login",
            json={"username": user, "password": passwd})
        token = resp.json()["token"]
        client.headers["X-Auth"] = token
        
        # List resources
        resp = await client.get(f"{base_url}/api/resources", params={"path": folder})
        items = resp.json()["data"]
        
        videos = [i for i in items if not i["isDir"] and 
            Path(i["name"]).suffix.lower() in {'.mp4','.mov','.mkv','.webm'}]
        
        return [{
            "title": Path(v["name"]).stem,
            "direct_url": f"{base_url}/api/raw{v["path"]}",
            "size_mb": round(v["size"]/1024/1024, 2)
        } for v in videos]
```

### Generic Pagination Pattern
```python
async def fetch_all(client, url, params):
    results = []
    while url:
        resp = await client.get(url, params=params)
        data = resp.json()
        results.extend(data["items"])
        url = data.get("next_page")  # or Link header
        params = None  # next_page URL already has params
    return results
```