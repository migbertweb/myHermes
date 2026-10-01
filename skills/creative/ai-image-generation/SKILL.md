---
name: ai-image-generation
description: Generate images via free and paid backends.
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [image-generation, pollinations, civitai, fal, flux, mcp]
    related_skills: [remotion-video-production, banner-design, comfyui]
---

# AI Image Generation — backends comparados

Guía de backends para generar imágenes (fondos de reels, banners, thumbnails, avatares, material de consulta) con sus costos, límites de resolución y trampas reales. Elegir backend según saldo disponible y resolución requerida.

## Decisión rápida (tabla)

| Backend | Costo | Key | Resolución máx | Velocidad | Cuándo usarlo |
|---|---|---|---|---|---|
| Pollinations.ai | **$0** | ninguna | **576×1024** (lado largo clampado a 1024) | ~5s | Sin saldo en nada más; fondos con overlay (nunca foco visual) |
| Civitai Orchestration MCP | Buzz (saldo cuenta) | CIVITAI_API_KEY | según engine (sdcpp → 1024×1024 siempre) | ~10s | Cuando hay Buzz; calidad buena |
| `image_generate` nativo (FAL FLUX 2 Klein 9B) | **Pago por imagen** (FAL) | configurada en Hermes | nativa (portrait/landscape/square real) | ~10-30s | Cuando hay créditos FAL; mejor calidad + 9:16 nativo |
| AI Horde (Stable Horde) | $0 (kudos por registro) | key gratuita | mayor (SDXL nativo) | minutos (cola de workers) | Gratis + mayor resolución, aceptando espera |

## Pollinations.ai (gratis, sin registro)

Endpoint directo por HTTP, sin auth:
```
https://image.pollinations.ai/prompt/<prompt url-encoded>?width=W&height=H&model=flux&nologo=true
```
- `model=flux` (default recomendado); `turbo` también funciona; `seedream` → 500 error (solo enterprise/enter.pollinations.ai).
- **Límite de resolución (verificado 2026-08):** el modelo flux clampa el lado largo a 1024 → para 9:16 lo máximo es **576×1024**, sin importar width/height pedidos. `enhance=true` NO sube la resolución.
- **Fix para fondos de video:** upscale con ffmpeg antes de usar:
  `ffmpeg -y -i in.jpg -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.4:5:5:0.0" -q:v 4 out.jpg`
  Adecuado como backdrop con overlay oscuro + texto encima; no como imagen protagonista.
- **Prompt base para fondos tech** (consistencia entre imágenes): "3D tech illustration, dark navy background with cyan and purple neon glow, clean minimal composition, lots of negative space in the upper third for text overlay, high quality render, no text in image".
- Script listo: `scripts/fetch_pollinations.py` — dict nombre→prompt, descarga a un directorio, reporta bytes.

## Civitai Orchestration MCP

Tool: `mcp__civitai_orchestration__generate_image`. Parámetros clave: `prompt` (obligatorio), `engine` (sdcpp default | seedream | flux1-kontext | openai | gemini | google/nano-banana | grok | qwen | wan), `model`, `aspectRatio`/`width`/`height`, `negativePrompt`, `seed`, `quantity` (1-12), `outputFormat`.

- **PITFALL principal:** el engine `sdcpp`/`flux2klein` devuelve **1024×1024 SIEMPRE**, ignora `aspectRatio`/`width`/`height`. Para vertical real hay que pedir otro engine o usar la imagen con `objectFit: cover`.
- **`InsufficientBuzz` en el error = saldo agotado** (no es bug del MCP ni del código). No reintentar en bucle; buscar otro backend o recargar Buzz.
- **Descarga del blob:** la respuesta trae URL firmada; usar `curl -L` con headers `Authorization: Bearer $CIVITAI_API_KEY` y `User-Agent` (la URL redirige a `/content/`; sin `-L` da 0 bytes).
- Key en `~/.hermes/.env` como `CIVITAI_API_KEY`; config en config.yaml con `Bearer ${CIVITAI_API_KEY}`.
- Buzz gratis diario: la web de Civitai regala Buzz con check-in diario/votos (sin pagar) — opción para acumular.

## `image_generate` nativo (Hermes → FAL)

Herramienta nativa (no skill ni MCP): `image_generate(prompt, aspect_ratio, image_url?, reference_image_urls?)`.
- Backend/modelo activo se ve en el system prompt (ej. "Active backend: FAL.ai · model: FLUX 2 Klein 9B").
- **Soporta 9:16 real** (`aspect_ratio: "portrait"`), edición (`image_url`) y hasta 9 `reference_image_urls` para consistencia de estilo (pasar una imagen existente como referencia de look/paleta).
- Pago por imagen en FAL — verificar saldo antes de prometer un lote (falla tipo "no credits").

## Verificación antes de comprometer un lote

1. Probar con **una generación pequeña de validación** (ej. 540×960) antes de generar N imágenes — confirma saldo/resolución del backend sin gastar de más.
2. `file <img>` para confirmar dimensiones reales (los backends free suelen no respetar lo pedido).
3. Mostrar rutas al usuario para validación visual antes de renderizar (el visor de visión puede estar caído; no bloquearse en él).
