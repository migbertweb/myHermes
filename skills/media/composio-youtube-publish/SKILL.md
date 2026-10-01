---
name: youtube-publish
description: Publicar Shorts YouTube (Composio + API propia).
version: 1.1.0
author: Migbert
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [devops, youtube, composio, shorts, google-api]
    related_skills: [validate-hermes-skill, inteligente-hashtags]
---

# Publicar Shorts/Videos en YouTube

Dos métodos disponibles:

## Método A: API propia con google-api-python-client (RECOMENDADO)
**Cuota propia** (10,000 units/día ≈ 6-7 Shorts/día), sin depender de Composio.

### Credenciales OAuth (desde `~/.hermes/config.yaml` → `youtube-mcp`):
```yaml
youtube-mcp:
  args:
    - YOUTUBE_CLIENT_ID=245033979911-0qekgmiq2i6lh8lmlqqa0fhst92vr9qn.apps.googleusercontent.com
    - YOUTUBE_CLIENT_SECRET=<COMPLETAR>
    - YOUTUBE_REFRESH_TOKEN=<COMPLETAR>
```

### Script: `/home/migbert/publish_youtube_own_api.py`
```bash
cd /home/migbert && python3 publish_youtube_own_api.py
```

**Ventajas:**
- ✅ Cuota propia (no compartida con otros usuarios Composio)
- ✅ Multipart upload nativo + verificación `fileDetails/processingDetails/status`
- ✅ Control total: reintentos, logging, metadata compleja
- ✅ Integración directa en Python (import googleapiclient)
- ✅ Añadir a playlist tras subida (`playlistItems().insert()`)

---

## Método B: Composio (MULTIPART_UPLOAD_VIDEO)
**Cuota compartida** (project_number:1068312718386) — propensa a 429 quota exceeded.

### ⚠️ REGLA CRÍTICA: nunca usar YOUTUBE_UPLOAD_VIDEO
**`YOUTUBE_UPLOAD_VIDEO` (resumable) está ROTO en Composio**: crea resource pero NO transfiere bytes → YouTube lo borra en ~45-90s.

**Siempre usar `YOUTUBE_MULTIPART_UPLOAD_VIDEO`** — probado: bytes llegan completos.

### Flujo CLI (server):
```bash
cd /dir/videos && composio execute YOUTUBE_MULTIPART_UPLOAD_VIDEO --file "Video.mp4" -d '{
  "title": "Título #Shorts", "description": "Hook + CTA + #tags",
  "tags": ["Tag1", "Shorts"], "categoryId": "28", "privacyStatus": "public"
}'
```
Verificar tras 60s:
```bash
composio execute YOUTUBE_GET_VIDEO_DETAILS_BATCH -d '{"id":["<videoId>"],"parts":["fileDetails","processingDetails","status"]}'
```
OK: `fileDetails.fileSize > 0` y `processingStatus: "succeeded"`.

---

## Identidad del canal (referencia)
- Canal: `Migbert on Linux` — handle `@migbertonlinux`
- Channel ID: `UCgpvOaIj-UTmRS4wC9YpwPA`
- Uploads playlist: `UUgpvOaIj-UTmRS4wC9YpwPA`
- Category ID: `28` (Ciencia y Tecnología)

## Convenio de metadata (estilo Migbert)
- **Título:** frase gancho en español + emoji + ` #Shorts` (≤100 chars)
- **Descripción:** 1-2 líneas + CTA con pregunta + 8-12 hashtags
- **Tags:** 8-11 keywords mixta ES/EN (`Shorts`, `Tecnología`, `devops`)
- Librería de Shorts: `~/sync/Shorts/`
