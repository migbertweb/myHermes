---
name: youtube-shorts-publish
description: Automates publishing of YouTube Shorts (≤60s) and cross-platform repurposing (TikTok, Instagram Reels, Twitter)
platforms: [linux]
---

# YouTube Shorts Publisher

This skill handles the end-to-end automation of Shorts publishing, from formatting metadata to scheduling and cross-platform distribution.

## When to invoke

- Shorts upload (vertical ≤60s) → auto-format description, hashtags, timestamps
- Cross-platform repurpose → generate TikTok/Reels captions, Twitter threads
- Scheduling → smart time/day recommendations per platform
- Generate pinned comment for engagement
- Hashtag strategy → platform-specific whitelist

## Output schema (JSON) returned to orchestrator

```json
{
  "status": "ok|error",
  "shorts_published": true,
  "cross_platform": ["tiktok","instagram","twitter"],
  "scheduled_for": [{"platform":"tiktok","iso":"2026-07-02T19:30:00-03:00"}]
}
```

## Output per platform

### YouTube Shorts (≤60s)
```
Título: <hook ≤100 chars>
Descripción: 1-2 líneas + 3-5 hashtags
```

### TikTok (≤3min, ideal 15-30s)
```
Caption: <hook + 1 línea + 3-5 hashtags>
Texto en pantalla: ≤3 palabras
```

### Instagram Reel (≤90s)
```
Caption: 5-8 líneas story + 8-15 hashtags
Cover text: 2-3 palabras
```

### Twitter/X (≤280 chars)
```
Tweet: <hook + 1 línea>
Hilo (opcional): 1/ Hook 2/ Contexto 3/ CTA
```

## Smart scheduling
| Platform | Best time (UTC-3) | Best day |
|---|---|---|
| YouTube Shorts | 12:00-14:00 / 19:00-21:00 | Any day |
| TikTok | 19:00-22:00 | Tue, Thu, Fri |
| Instagram | 11:00-13:00 / 19:00-21:00 | Wed, Sun |
| Twitter | 08:00-10:00 / 18:00-20:00 | Tue, Wed |

**Rules**
- NEVER publish 03:00-05:00 (audience asleep)
- Shorts/TikTok: high cadence (3-5/week)
- Long videos: 1-2/week → Thu or Sun

## Auto-generated pinned comment
```markdown
📌 ¿Qué parte te quedaste atascado? Deja el timestamp y te ayudo.

⏱️ Timestamps clave:
- 0:00 — Hook
- 5:00 — Main topic
- 10:00 — CTA

🔗 Sources:
- Repo: <repo-url>
```

## How to invoke
```yaml
delegate_task(
  goal="\"publish youtube shorts\"",
  context="\"<final video path, title, description base, target platforms>\"",
  role="leaf",
  toolsets=["terminal","file"]
)
```

## Common pitfalls

- **>5 visible hashtags on YouTube** → backend tags absorb extras
- **Repeating hashtags across platforms** → dilutes community focus
- **Using vertical video as main post** → must be published as Short
- **Forgetting the "more" in description** → first lines decide click-through
- **Same caption on TikTok and Instagram** → adapt tone per platform