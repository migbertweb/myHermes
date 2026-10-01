# TPB API (apibay.org) Reference

The Pirate Bay has a lightweight JSON API at `apibay.org` that returns
torrent search results without any anti-bot protection. Useful when the
user's preferred torrent site is blocked by CAPTCHA/Proof-of-Work.

## Endpoint: Search

```
GET https://apibay.org/q.php?q=<query>&cat=<category>
```

### Parameters

| Param | Description |
|-------|-------------|
| `q`   | URL-encoded search terms |
| `cat` | Optional category filter (e.g. `201` = movies, `205` = music, `208` = TV shows) |

### Response (JSON array)

Each item has these fields:

```json
{
  "id": "12345",
  "name": "Movie.Name.2023.1080p.WEBRip.x265",
  "info_hash": "FE4CD297ECE7ECDEECA59462ACD825327215D2B5",
  "leechers": "4",
  "seeders": "12",
  "num_files": "1",
  "size": "1073741824",
  "username": "uploader_name",
  "added": "1700000000",
  "status": "vip",
  "category": "201",
  "imdb": "tt1234567"
}
```

### Key fields

| Field | Notes |
|-------|-------|
| `info_hash` | The BTIH hash. Build a magnet: `magnet:?xt=urn:btih:{info_hash}&dn={name}` |
| `size` | In bytes. Divide by 1073741824 for GB. |
| `seeders` / `leechers` | May be empty strings for entries with no activity. **Always check these before picking a torrent.** ⚠️ The field is `seeders` (not `seeds`) — a common mistake when writing Python parsers. |
| `name` | The display name, but may have special chars. URL-encode for the magnet `&dn=` param. |

### Common category IDs

| Category | ID |
|----------|----|
| Movies | 201 |
| Movies (HD) | 207 |
| TV Shows | 208 |
| TV Shows (HD) | 208 |
| Music | 101 |
| Applications | 301 |
| Games | 401 |

## Example queries

```bash
# Search for The Equalizer in 1080p
curl -sL "https://apibay.org/q.php?q=The+Equalizer+2014+1080p"

# Search with quality/size preference
curl -sL "https://apibay.org/q.php?q=equalizer+x265+1080p"

# Search for a specific movie + lightweight version
curl -sL "https://apibay.org/q.php?q=equalizer+2014+BRRip+HEVC"

# Search category-scoped (movies)
curl -sL "https://apibay.org/q.php?q=The+Equalizer&cat=201"
```

## Limitations

- No pagination — returns top ~30 results max
- Seed/leecher counts may be slightly stale (cached)
- `info_hash` field uses uppercase hex — the magnet link is case-insensitive
- The API does not return trackers; you can use a standard set like:
  `&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.opentrackr.org:1337`

## Search patterns for lightweight streaming torrents

When the user wants lightweight versions (< 2 GB per movie) for streaming:

1. **First try x265/HEVC:** `query=equalizer+1080p+x265` or `query=equalizer+1080p+hevc`
2. **Fallback to BRRip/WEBRip x265:** `query=equalizer+1080p+brrip+x265` or `query=equalizer+webrip+x265`
3. **Fallback to YTS (x264, but well-seeded):** `query=equalizer+YTS` or `query=equalizer+1080p+YTS`
   - YTS releases are optimized x264 at 1080p, 1.2-2 GB, with 50-150+ seeders
   - Great for streaming even though it's x264 — good quality/size trade-off
4. **If 1080p has no seeders, try 720p HEVC:** `query=equalizer+720p+hevc`

## Seed/leecher prioritization

When choosing between options, sort by this priority:
1. Versions with **both seeders and leechers visible** in the API response
2. Versions with **high seeders** (>20) even if 0 leechers — usually still downloadable
3. Versions with **any leechers** (>0) — someone managed to connect at least
4. Avoid versions where both `seeders` and `leechers` are empty strings

When adding magnets from the API, Transmission automatically uses the DHT
and PEX to find peers even without explicit tracker URLs, so the basic
magnet link format is sufficient.

## Alternative endpoints

- `https://apibay.org/t.php?id=<torrent_id>` — Get details for a specific torrent
- `https://apibay.org/precompiled/data_top100_<cat>.json` — Top 100 for a category
