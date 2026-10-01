# Wikimedia Commons Direct URL Extraction

## Problem

You have a Wikimedia Commons file page URL (like `https://commons.wikimedia.org/wiki/File:Some_ThinkPad.jpg`) and need the direct download URL to feed to `curl` or `wget`.

Wikimedia stores files at URLs like:
`https://upload.wikimedia.org/wikipedia/commons/{hash1}/{hash2}/{filename}`

Where `{hash1}/{hash2}/` is derived from the MD5 hash of the filename and **cannot be guessed**.

## Solution: Browser Console Method

### Step 1
Navigate to the Commons file page.

### Step 2
Open the browser console (F12 > Console tab).

### Step 3
Run the extraction command:

```js
Array.from(document.querySelectorAll('a[href*="upload.wikimedia.org/wikipedia/commons/"]'))
  .filter(a => !a.href.includes('thumb'))
  .slice(0,3)
  .map(a => a.href)
```

### Step 4
The result is an array of direct URLs. Pick the first one.

## Why This Works

- Every Commons file page has anchor tags pointing to the original file
- Thumbnail URLs contain `/thumb/` in the path -- we filter those out
- The remaining URLs are direct links to the full-resolution original

## Rate Limiting

If you get no results or all results are thumbnails, you may be rate-limited. Check by looking at the response headers for any downloaded file:

```bash
curl -sI "https://upload.wikimedia.org/wikipedia/commons/..." -H "User-Agent: Mozilla/5.0" | grep -i "HTTP/"

# HTTP/2 429 means rate-limited. Check retry-after:
curl -sI "..." -H "User-Agent: Mozilla/5.0" | grep -i "retry-after"
```

Wait the `retry-after` seconds before trying again.
