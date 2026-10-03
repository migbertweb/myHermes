---
name: composio-instagram-publish
description: Publicar Reels Instagram Composio.
version: 1.0.0
author: Migbert
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [devops, instagram, composio]
    related_skills: [validate-hermes-skill, inteligente-hashtags]
---

# Publicar Reels en Instagram con Composio

Workflow para el canal **@migbertonlinux** (IG Business/Creator). Probado en laptop CachyOS;
el server (serverhogar) necesita video_url público o staging en sandbox remoto.

## Conexión (ya configurada)
- CLI: `~/.local/bin/composio` (workspace `migbertyanez_workspace`, cuenta `instagram_predry-unsort` alias `MigbertOnLinux`).
- MCP nativo Hermes: server `composio` en `~/.hermes/config.yaml` → `url: https://connect.composio.dev/mcp` + `x-consumer-api-key` desde `COMPOSIO_API_KEY`.
- Verificación: `hermes mcp test composio` → tools incluyen `INSTAGRAM_POST_IG_USER_MEDIA`, `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`, `INSTAGRAM_GET_IG_MEDIA`, etc.

## Requisito previo: control de qué está publicado y qué falta + URLs válidas para Meta

El microservicio **video_link_extractor** (`/home/piro/proyectos/video_link_extractor/`) lista los videos locales del server. **El CLI con username/password genera tokens de sesión TRUNCADOS** (Meta devuelve 401/ERROR). 

### Fix crítico: usar FILEBROWSER_TOKEN (API token) directamente
```bash
# En .env: FILEBROWSER_TOKEN=eyJhbG... (token completo, 303 chars, 3 partes JWT)
# El CLI debe usar este token, NO username/password
```

### 0. Listar videos locales (genera `videos.json` con JWTs completos)
```bash
cd /home/piro/proyectos/video_link_extractor
source venv/bin/activate  # si no existe, crear venv
python cli.py -o videos.json  # solo si videos.json no existe
```
- El CLI usa `FILEBROWSER_TOKEN` del `.env` → `direct_url` con JWT completo válido
- `stream_url`: **NO** usar con Composio/Meta → responde 520 con user-agent facebookexternalhit, causando container ERROR.
- `direct_url` de `/api/resources/download`: usar **SIEMPRE**. Responde 200 con `Content-Type: video/mp4` para cualquier user-agent. Soporta Range implícito.

> El CLI funciona standalone (no requiere el server FastAPI corriendo).

### 0b. Comparar con Instagram (genera `instagram_comparison.json`)
Obtén los Reels de tu cuenta con Composio (tool `INSTAGRAM_GET_IG_USER_MEDIA` o similar) y compara sus captions/títulos con los títulos de `videos.json`. El script de comparación crea `instagram_comparison.json` con:
- `published`: videos locales que ya tienen su Reel en IG (con `match_score`).
- `missing`: títulos de videos locales **sin** publicar (fuente del `direct_url` para el paso 1).
- `other_instagram_reels`: captions de Reels que no coinciden con ningún video local.

```bash
python compare.py videos.json --ig-file ig_reels.json -o instagram_comparison.json
```

## Flujo completo (CLI + comparación + inteligente-hashtags)

### 0. Listar videos y generar hashtags
```bash
cd /home/piro/proyectos/video_link_extractor && python cli.py -o videos.json
# Buscar el video deseado en instagram_comparison.json (sección missing) y copiar su direct_url y title
```

### 0.5 Generar hashtags inteligentes (nuevo)
Usar el skill `inteligente-hashtags` con el título del video:
```bash
# Entrada: título del video (ej. "Adiós_Makefiles__Por_Qué_Necesitas_Just")
# Salida: hashtags técnicos + tags base del canal @migbertonlinux
# Backend: Ollama gemma3:1b (local) o gemma4:31b-cloud (premium)
```

**Script de integración (`scripts/generate_hashtags.py`):**
```python
#!/usr/bin/env python3
"""
Genera hashtags inteligentes para Instagram Reels usando Ollama.
Integración directa con el skill inteligente-hashtags.
"""
import json
import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"  # local, rápido
# MODEL = "gemma4:31b-cloud"  # premium, mejor semántico

# Tags base del canal @migbertonlinux
BASE_TAGS = ["#Linux", "#ArchLinux", "#DevOps", "#Terminal", "#OpenSource", "#CachyOS", "#Hyprland"]

def generate_hashtags(title: str, max_tags: int = 5) -> list:
    """Genera hashtags semánticos desde un título usando Ollama."""
    prompt = f"Extract {max_tags} technical keywords from this title for Instagram hashtags. Output ONLY the words, comma-separated, no other text:\n\n{title}"
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=15)
        resp.raise_for_status()
        keywords = resp.json().get("response", "").strip()
        # Parse comma-separated keywords
        tags = [f"#{k.strip().capitalize()}" for k in keywords.split(",") if k.strip()]
        return tags[:max_tags]
    except Exception as e:
        print(f"Error Ollama: {e}, usando fallback regex...", file=sys.stderr)
        return fallback_hashtags(title, max_tags)

def fallback_hashtags(title: str, max_tags: int) -> list:
    """Fallback regex estricto: solo sustantivos técnicos."""
    import re
    stop_words = {'el','la','un','una','y','en','de','por','para','con','los','las','su','mi','tu','nuestro'}
    clean = re.sub(r'[_\-]+', ' ', title.lower())
    words = [w for w in clean.split() if w not in stop_words and len(w) >= 3]
    tech_whitelist = {'linux','docker','kubernetes','rust','go','python','nvim','vscode','git','terraform','ansible','prometheus','grafana','kafka','redis','postgres','mysql','mongodb','nginx','traefik','cachyos','hyprland','wayland','sway','i3','qtile','awesome','xmonad','kde','gnome','xfce','arch','debian','ubuntu','fedora','opensuse','nixos','gentoo','alpine','void','artix','manjaro','endeavour','garuda','nobara','bazzite','bluefin','aurora','ublue','silverblue','kinoite','sericea','onyx','makefiles','buildsystems','automation','valgrind','debugging','memory','lazygit','git','history','fzf','menus','interactive','terminal','replaces','programming','dokploy','coolify','produccion','triage','server','downtime'}
    tags = [f"#{w.capitalize()}" for w in words if w in tech_whitelist]
    return tags[:max_tags]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_hashtags.py \"Título del video\"")
        sys.exit(1)
    
    title = sys.argv[1]
    semantic_tags = generate_hashtags(title)
    all_tags = semantic_tags + BASE_TAGS
    print(json.dumps({"title": title, "hashtags": all_tags}, ensure_ascii=False))
```

### 1. Crear container
```bash
composio execute INSTAGRAM_POST_IG_USER_MEDIA -d '{
  "ig_user_id": "28194571276874046",
  "media_type": "REELS",
  "video_url": "https://file.migbertweb.xyz/api/resources/download?file=/sync/Shorts/Tu_Video.mp4&source=Shared&auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "caption": "Tu caption con #hashtags_generados",
  "share_to_feed": true
}'
```
Respuesta: `data.id` → **creation_id** (guardar).

### 1.5. Esperar a FINISHED antes de publicar
Meta necesita tiempo para procesar. Poll obligatorio:
```bash
composio execute INSTAGRAM_GET_POST_STATUS -d '{"creation_id":"<creation_id>"}'
```
Repetir hasta que `status_code` sea `FINISHED`. Si queda en `ERROR`, crear un container NUEVO con `direct_url`.

### 2. Publicar
```bash
composio execute INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH -d '{
  "ig_user_id": "28194571276874046",
  "creation_id": "<creation_id>",
  "max_wait_seconds": 120
}'
```
- `max_wait_seconds`: 120 para Reels (procesamiento 30-120s). 0 solo si ya verificado FINISHED.
- Respuesta: `data.id` → **ig_media_id** (publicado).

### 3. Verificar (opcional)
```bash
composio execute INSTAGRAM_GET_IG_MEDIA -d '{"ig_media_id": "<ig_media_id>"}'
```

## Parámetros clave
| Campo | Valor | Nota |
|---|---|---|
| `ig_user_id` | `28194571276874046` (o `"me"`) | IG Business Account ID |
| `media_type` | `REELS` | obligatorio para video corto |
| `video_url` | `https://...` | MP4 directo, sin auth |
| `caption` | string | hashtags como `%23tag` o texto plano |
| `share_to_feed` | `true` | aparece en Feed y pestaña Reels |
| `thumb_offset` | ms | frame del thumbnail (default 0) |
| `cover_url` | `https://...` | portada custom opcional |

## Validación del video (antes de subir)
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name -show_entries format=duration /ruta/video.mp4
```
- Shorts/Reels: 1080x1920 (9:16), h264, AAC, ≤ 90 s (ideal 15-60 s).

## Metadata estilo Migbert (probado)
- **Caption:** hook en español + emojis + CTA pregunta + 8-12 hashtags (`#Ghostty #Terminal #Linux #ArchLinux #Hyprland #DevOps #Productividad #Dotfiles`).
- **Audio:** `audio_name` opcional (default "Original Audio").
- **Portada:** `cover_url` si quieres thumbnail custom.

## Pitfalls
- **Usar `FILEBROWSER_TOKEN` (API token) del `.env`, NO username/password** — el token de sesión que genera username/password es truncado por Filebrowser Quantum y Meta devuelve 401/ERROR. El CLI ya usa el API token si está configurado.
- **`creation_id` ≠ `ig_media_id`** — el primero es el container, el segundo el media publicado.
- **Reintentar publish del mismo `creation_id` → HTTP 409**. Si el container termina en `ERROR`, crear uno NUEVO con `direct_url` fresco.
- **Solo Business/Creator accounts** — Personal falla 400/403 (code 100, subcode 33).
- **Cuota diaria** — consultar `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT` antes de bursts.
- **`max_wait_seconds: 0` saltea polling** → falla 9007 si el container aún procesa (común en video).
- **El JWT en query param expira** — generar la URL justo antes de publicar (el CLI con API token renueva el token cada ejecución).

## Flujo MCP (remote workbench) — para server sin URL pública
```python
# 1. Subir video al sandbox Composio (requiere archivo en sandbox)
#    -> upload_local_file('/path/en/sandbox/video.mp4') -> s3key
# 2. Crear container con video_file
res = run_composio_tool('INSTAGRAM_POST_IG_USER_MEDIA', {
    'ig_user_id': 'me',
    'media_type': 'REELS',
    'video_file': {'name': 'video.mp4', 'mimetype': 'video/mp4', 's3key': '<s3key>'},
    'caption': '...',
    'share_to_feed': True
})
creation_id = res['data']['id']
# 3. Publicar
pub = run_composio_tool('INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH', {
    'ig_user_id': 'me',
    'creation_id': creation_id,
    'max_wait_seconds': 120
})
ig_media_id = pub['data']['id']
```

## Checklist final
- [ ] Container creado (`creation_id` guardado)
- [ ] Publicado sin error (`ig_media_id` guardado)
- [ ] `INSTAGRAM_GET_IG_MEDIA` devuelve `permalink` y `media_product_type: REELS`
- [ ] URL final: `https://www.instagram.com/reel/<shortcode>/` (shortcode no es el ID numérico)
