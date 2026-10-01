---
name: civitai-orchestration
description: Generate images/video/music via Civitai Orchestration MCP.
---

# Civitai Orchestration MCP

Uso de los 19 tools del MCP `civitai-orchestration` (configurado en Hermes laptop): generate_image / generate_video / generate_music, upscale, TTS, caption, enhance_prompt, find_models, submit_workflow. Es el generador de imágenes para fondos/escenas de videos (reels Remotion, HyperFrames) y assets.

## Config (ya hecha en la laptop)
- URL: `https://orchestration.civitai.com/mcp`, transporte streamable-http
- Key: `CIVITAI_API_KEY` en `~/.hermes/.env` (config.yaml usa `Bearer ${CIVITAI_API_KEY}`)
- Invocar: `tool_search("civitai generate image")` → `tool_describe` → `tool_call`

## Flujo: imágenes para un proyecto de video
1. `tool_call generate_image`: prompt detallado (estilo + paleta + "negative space upper third for text" + "no text in image"), `engine`, `model`, `outputFormat: "jpeg"`, `seed` fijo por imagen (reproducibilidad).
2. La respuesta trae un blob URL firmado (`orchestration-new.civitai.com/v2/consumer/blobs/<id>.jpg?sig=...&exp=...`).
3. Descargar SIEMPRE con `-L` + Authorization + User-Agent (el blob redirige HTTP 301 a `/content/`; sin `-L` da 0 bytes):
   ```bash
   curl -sL -o public/img/foo.jpg -H "Authorization: Bearer $CIVITAI_API_KEY" -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64)" "<blob-url>"
   ```
4. Mapear nombres de asset ANTES de escribir código (`reel1-hook.jpg → escena Hook`) para que el swap posterior sea directo.

## Pitfalls (encontrados en producción 2026-08-25)
- **El engine sdcpp/flux2klein devuelve 1024×1024 aunque pidas `aspectRatio: "9:16"` o width/height** — ignora el aspect ratio. Para verticales: usar la imagen con `objectFit: cover` + overlay oscuro en Remotion (recorta sin deformar).
- **Buzz es una cuota consumible**: `"error": "Failed to initialize workflow: InsufficientBuzz"` = saldo agotado A MEDIO LOTE (los primeros N funcionan, el resto falla). Estrategia: generar en tandas y verificar cada una; diseñar el video con backdrops fallback (gradientes animados) para las imágenes que falten, y hacer swap de archivos después — cero re-trabajo de código si los nombres ya están mapeados.
- El blob URL tiene `exp=` — descargar inmediatamente tras generarlo.
- Varias llamadas en paralelo pueden disparar rate-limit del servidor MCP ("MCP server unreachable, auto-retry in ~59s") — no reintentar en bucle; esperar o cambiar de tarea.

## Engines y modelos (schema del tool)
| engine | modelos |
|---|---|
| sdcpp (default, rápido) | flux2klein (default), qwen, zimage-turbo, zimage-base |
| flux1-kontext | pro / max / dev |
| openai | gpt-image-2 / gpt-image-1.5 / gpt-image-1 |
| gemini | 2.5-flash |
| google | nano-banana-2 / nano-banana-2-lite / imagen4 / nano-banana-pro |
| seedream | v4.5 / v5.0-lite / v5.0-pro |
| grok | v2.0 (default) / v1.0 |
| qwen | createImage: 3.0-pro / 2.0-pro / 2.0 (default) / max / plus; editImage: 3.0-pro / 2.0-pro / 2.0 / edit-max / edit-plus (default) / edit |
| wan | (video) |

- `operation`: createImage (default) / editImage (con `images[]` + opcional `maskImage`) / createVariant
- Otros params: `negativePrompt`, `guidanceScale`, `steps`, `seed`, `quantity` (1-12), `outputFormat` (jpeg/png/webp)

## Otros tools útiles
- `generate_video`: video desde texto/imagen (engines wan, etc.)
- `generate_music`: ACE Step 1.5, letras estructuradas con `[Verse]`/`[Chorus]`; devuelve MP3 o WebM con cover
- `upscale_image`, `caption_media` (describir media antes de procesar), `enhance_prompt`, `transcribe_audio`, `text_to_speech`, `chat_completion` (LLM vía OpenRouter)

## Relacionado
- `remotion-video-production` (fondos generados → composiciones Remotion)
- `procedural-audio-synthesis` (BGM fallback sin consumir buzz)
