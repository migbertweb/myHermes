---
name: youtube-publisher
description: Publica y formatea contenido para YouTube y plataformas derivadas (Shorts, Instagram, TikTok, Twitter). Worker gemma4:31b-cloud del equipo youtube_team.
platforms: [linux]
---

# YouTube Publisher (gemma4 worker)

Esta skill la carga el **worker de publishing** del agente `youtube_team`.
El orquestador (deepseek-v4-flash-free) la activa cuando el usuario pide:
"publica esto", "sube a Shorts", "adapta a TikTok", "formatea para Twitter", "agenda la salida".

## Cuándo el orquestador debe activar esta skill

- **Formateo final** de descripción larga para YouTube (markdown → bbcode/plain)
- **Adaptación cross-platform** (Shorts, TikTok, Reels, Twitter, LinkedIn)
- **Scheduling** (calcular fecha/hora óptima según audiencia)
- **Generación de pinned comment** con timestamps
- **Hashtag strategy** por plataforma
- **End screen / cards** suggestions
- **Community post** teaser

## NO usar esta skill para

- Guión (eso es `youtube-script`)
- Edición de video (eso es `youtube-editor`)
- Thumbnail (eso es `youtube-thumbnail`)

## Por qué gemma4 hace este trabajo

Gemma4:31b-cloud es **barato y rápido** en ollama-cloud. Las tareas de publishing son:
- Mecánicas y repetitivas (formatear texto)
- No requieren razonamiento profundo (gemma4 las clava)
- Alto volumen (un video genera 5-8 outputs derivados: Short, TikTok, Twitter thread, etc.)

Deepseek queda libre para lo que realmente necesita razonamiento (guión, SEO strategy).

## Output por plataforma

### YouTube (descripción completa)

```markdown
## Descripción del video en 1-2 líneas (aparece arriba del "más")

<gancho emocional o promesa concreta>

## Timestamps (capítulos)

0:00 — Hook
1:30 — Sección 1: <título>
5:00 — Sección 2: <título>
...

## Links

- 🌐 Web/Blog: <url>
- 🐦 Twitter: <url>
- 💬 Discord: <url>
- ☕ Apóyame: <url ko-fi o similar>

## Sobre el canal

<bio de 2-3 líneas>

## Tags (YouTube backend, max 500 chars)

linux, devops, dokploy, hetzner, postgresql, self-hosted, <5-10 tags relevantes>

## Hashtags (visibles, max 3-5)

#Linux #DevOps #SelfHosted
```

### YouTube Shorts (≤60s)

```
Título: <hook agresivo, max 100 chars>
Descripción: 1-2 líneas + 3-5 hashtags
```

### TikTok (≤3min, ideal 15-30s)

```
Caption: <hook + 1 línea + 3-5 hashtags>
Texto en pantalla: <3-5 palabras máximo>
```

### Instagram Reel (≤90s)

```
Caption: 5-8 líneas con storytelling + 8-15 hashtags
Cover text: 2-3 palabras
```

### Twitter / X (video nativo o link)

```
Tweet principal: <hook + 1 línea>
Hilo (opcional, si el tema lo amerita):
1/ Hook
2/ Contexto
3/ Punto clave 1
4/ Punto clave 2
5/ CTA con link al video
```

### LinkedIn (dev/tech audience)

```
<post profesional, 3-5 párrafos, sin hashtag spam (max 3)>
```

## Scheduling inteligente

El worker consulta la audiencia del canal y recomienda:

| Plataforma | Mejor hora (UTC-3, Brasil) | Mejor día |
|---|---|---|
| YouTube largo | 18:00-20:00 | Jueves, Domingo |
| YouTube Shorts | 12:00-14:00 o 19:00-21:00 | Cualquier día |
| TikTok | 19:00-22:00 | Martes, Jueves, Viernes |
| Instagram | 11:00-13:00 o 19:00-21:00 | Miércoles, Domingo |
| Twitter | 08:00-10:00 o 18:00-20:00 | Martes, Miércoles |
| LinkedIn | 07:00-09:00 o 17:00-18:00 | Martes, Miércoles, Jueves |

**Reglas:**
- NUNCA publicar a las 3-5 AM (audiencia dormida)
- NUNCA programar para viernes tarde si el tema es técnico (la gente sale)
- Shorts y TikTok: alta cadencia (3-5/semana) → spreadear entre días
- Videos largos: 1-2/semana → Jueves (pre-weekend) o Domingo (planning semanal)

## Pinned comment automático

```markdown
📌 ¿En qué parte te quedaste atascado? Comenta el timestamp y te ayudo.

⏱️ Timestamps clave:
- 0:00 — Lo que NO funciona con Waybar
- 2:30 — La solución con Quickshell
- 8:00 — Mi configuración final

🔗 Links útiles:
- Repo: <url>
- Docs: <url>
```

## Reporte al orquestador

```json
{
  "status": "ok | error",
  "platforms_published": ["youtube", "tiktok", "twitter"],
  "scheduled_for": [
    {"platform": "youtube", "iso": "2026-07-03T20:00:00-03:00"},
    {"platform": "tiktok", "iso": "2026-07-02T19:30:00-03:00"}
  ],
  "assets_generated": {
    "youtube_description": "...",
    "shorts_caption": "...",
    "tiktok_caption": "...",
    "twitter_thread": ["...", "..."],
    "pinned_comment": "..."
  },
  "warnings": []
}
```

## Cómo invocar al worker

```
delegate_task(
  goal="<tarea de publishing>",
  context="<video final, título, descripción base, plataformas target>",
  role="leaf",
  toolsets=["terminal", "file"]
)
# Este worker DEBE ser gemma4:31b-cloud — el orquestador lo especifica en el agent
```

## Pitfalls

- **No usar más de 5 hashtags visibles en YouTube** — los demás van en backend tags
- **No repetir hashtags entre plataformas** — cada red tiene su propia cultura
- **No publicar Shorts como video principal** — suben como Short, formato vertical, <60s
- **No olvidar el "más" en descripción de YouTube** — los primeros 2-3 renglones (antes del "show more") son los que决定 si la gente ve el video
- **No usar la misma caption en TikTok e Instagram** — TikTok más crudo, Instagram más curado
