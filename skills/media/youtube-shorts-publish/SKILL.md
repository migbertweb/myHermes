---
name: youtube-shorts-publish
description: Publicar YouTube Shorts con google-api-python-client OAuth.
version: 1.0.0
author: Migbert
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [devops, youtube, shorts, google-api, oauth]
    related_skills: [inteligente-hashtags, validate-hermes-skill]
---

## When to Use
- Publicar YouTube Shorts con cuota propia (10k units/día) sin depender de Composio.
- Cuando Composio devuelve 429 quota exceeded (cuota compartida agotada).
- Cuando se necesita control total: multipart upload, verificación automática, playlist, reintentos.
- Cuando las credenciales OAuth (client_id, client_secret, refresh_token) están en **variables de entorno** (`os.getenv`), NO en `~/.hermes/config.yaml`. El `youtube-mcp` en config.yaml es para el MCP server, independiente del script de publicación.

# Publicar YouTube Shorts con API propia (google-api-python-client)

**Cuota propia** (10,000 units/día ≈ 6-7 Shorts/día). No depende de Composio ni de cuotas compartidas.

## Credenciales OAuth
El script `publish_youtube_own_api.py` lee de **variables de entorno**, NO de `config.yaml`:
- `YOUTUBE_CREDENTIALS_FILE` → ruta al `client_secret*.json` descargado de Google Cloud Console. **Default seguro:** `/home/migbert/.hermes/auth/client_secret_channel2.json` (no dejarlo en `~/` raíz).
- `YOUTUBE_REFRESH_TOKEN2` → token del canal activo (el script lo prefiere con fallback: `os.getenv("YOUTUBE_REFRESH_TOKEN2") or os.getenv("YOUTUBE_REFRESH_TOKEN")`)
- `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` → se extraen del JSON, no de env (salvo override)

El `youtube-mcp` en `~/.hermes/config.yaml` es independiente: sirve al MCP server, no al script de publicación. No lo confundas.

Construir `google.oauth2.credentials.Credentials` con:
```python
creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    token_uri="https://oauth2.googleapis.com/token"
)
```

## Script de referencia
`/home/migbert/publish_youtube_own_api.py` — flujo completo:
1. Escanea `/home/migbert/sync/Shorts/` (ordena alfabéticamente, toma primeros N)
2. Genera título gancho + `#Shorts` desde mapeo de keywords
3. Extrae hashtags técnicos con Ollama `gemma3:1b` local (+ fallback regex)
4. Sube con `MediaFileUpload(resumable=True, chunksize=5MB)`
5. Verifica a los 60s: `videos().list(part=fileDetails,processingDetails,status)`
6. OK si `int(fileSize) > 0` y `processingStatus == "succeeded"`

## Pitfalls
- **Venv corrupto**: paquetes `google-api-python-client`, `httplib2`, `uritemplate`, `google-auth-httplib2` pueden quedar con solo archivos `.sync-conflict`. Fix: `pip3 install --ignore-installed <paquete>==<version>` para cada uno.
- **Origen de credenciales**: el skill dice `config.yaml` → `youtube-mcp.args`, pero el script lee `os.getenv(...)`. Si sigues el skill al pie de la letra no encontrarás la variable. Lee el script primero.
- **Múltiples canales**: cada canal requiere su propio `refresh_token` + `client_secret.json`. Para distinguirlos, usa un sufijo en la variable de entorno (ej. `YOUTUBE_REFRESH_TOKEN2`) y haz que el script la prefiera con fallback: `REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN2") or os.getenv("YOUTUBE_REFRESH_TOKEN")`. Si solo actualizas la variable sin el sufijo y el script no lo tiene en cuenta, subes al canal viejo sin error.
- **`mine=True` solo en `channels()`**: `videos().list(part=..., mine=True)` lanza `TypeError: unexpected keyword argument 'mine'`. Para verificar a qué canal pertenece un token antes de subir, usa `service.channels().list(part='id,snippet', mine=True)`.
- **Verificación pre-subida**: antes de subir, confirma el canal con `channels().list(mine=True)` y compara `id`/`snippet.title`. Un token válido no significa el canal correcto: un `refresh_token` viejo puede fallar con `unauthorized_client` si no coincide con el `client_secret` que se le pasa.
- **fileSize viene como string** de la API YouTube → castear a `int` antes de comparar: `int(file_details.get("fileSize", 0))`.
- **Verificación obligatoria a 60s**: YouTube necesita procesar el video; consultar antes da `processingStatus: "processing"` y `fileSize: null`.
- **Hashtags sucios de Ollama**: `get_hashtags()` usaba la respuesta de Ollama ciegamente → salía `#Makefiles #Makefiles #Why #Need #Why` (duplicados y fuera del set técnico). Ahora la salida de Ollama se filtra por la whitelist técnica (`tech = {...}`) y se deduplica con la lista extraída del título. Si Ollama devolviera fuera del set, se ignora y se usa solo el fallback regex.
- **Credenciales en config.yaml**: leer `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` de `youtube-mcp.args` en `~/.hermes/config.yaml`.
- **Playlist opcional**: usar `playlistItems().insert()` tras subida exitosa si se define `PLAYLIST_ID`.

## Metadata estilo Migbert
- **Título**: frase gancho en español + emoji + ` #Shorts` (≤100 chars)
- **Descripción**: 1-2 líneas + CTA con pregunta + 8-12 hashtags
- **Tags**: 8-11 keywords mixta ES/EN (`Shorts`, `Tecnología`, `devops`)
- Librería de Shorts: `~/sync/Shorts/` (detecta videos nuevos automáticamente)

## Comando rápido
```bash
cd /home/migbert && python3 publish_youtube_own_api.py
```

## Diferencia vs Método Composio
| Aspecto | API propia | Composio MULTIPART |
|---|---|---|
| Cuota | Propia (10k units/día) | Compartida (project 1068312718386, 966/día) |
| Confiabilidad | Alta (bajo control total) | Media (cuota agotada frecuente) |
| Verificación | Nativa en script | Requiere llamada separada GET_VIDEO_DETAILS_BATCH |
| Venv | Requiere google-api-python-client funcional | Solo CLI composio |

**Regla**: preferir API propia salvo que credenciales OAuth no estén disponibles.
