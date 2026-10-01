---
name: video-editor-studio
description: "Master Skill para producción, edición y postproducción de video profesional multi-formato (16:9 YouTube y 9:16 Reels/Shorts/TikTok) con subtítulos trilingües (ES, PT, EN), Drift MCP, Remotion y generación de imágenes con Pollinations/Civitai."
version: 1.0.0
author: Antigravity + Migbert
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [video-editing, drift, remotion, reels, shorts, youtube, subtitles, pollinations, civitai, tts, multi-format]
---

# Video Editor Studio — Workflow Multi-Formato & Trilingüe

Workflow integral para edición de video creativo de alta retención en redes sociales (Reels, TikTok, Shorts) y YouTube Standard (16:9), con generación de imágenes IA, subtítulos trilingües (Español, Portugués e Inglés) y control mediante **Drift MCP** y **Remotion**.

---

## 1. Configuración de Formatos de Renderizado (Capa de Salida)

El proyecto o edición siempre debe exportar o contemplar dos relaciones de aspecto primarias según la plataforma destino:

| Formato | Resolución | FPS | Destino Principal | Regla de Encuadre Visual |
|---|---|---|---|---|
| **Vertical** | `1080x1920` (9:16) | 30 / 60 | Instagram Reels, TikTok, YouTube Shorts | Sujeto/acción centrado en el tercio medio. Zonas de seguridad para UI de red social (evitar bordes superior e inferior). |
| **Horizontal** | `1920x1080` (16:9) | 30 / 60 | YouTube Standard, Vimeo, Web / Portafolio | Composición panorámica con regla de tercios y espacio para gráficos laterales o B-Roll. |

---

## 2. Flujo de Subtítulos Trilingües (ES 🇪🇸 / PT 🇧🇷 / EN 🇬🇧)

Todo video debe contar con subtítulos sincronizados en los 3 idiomas principales:

### Paso A: Extracción y Transcripción Fuente
1. Extraer audio desde el video/edición base:
   ```bash
   ffmpeg -y -i "/path/to/input.mp4" -vn -c:a copy "/path/to/audio.m4a"
   ```
2. Transcribir el audio fuente mediante Groq Whisper (`whisper-large-v3-turbo`) con `response_format=verbose_json` o archivo `.srt`.

### Paso B: Traducción y Generación de `.srt` Trilingüe
Ejecutar el script auxiliar incluido en la skill para generar automáticamente los 3 archivos SRT:
```bash
python3 ~/.hermes/skills/media/video-editor-studio/scripts/translate_srt.py "/path/to/subtitles.srt" --source es --target es pt en
```
*Salidas generadas:*
- `subtitles.es.srt` (Español Latino)
- `subtitles.pt.srt` (Portugués PT-BR)
- `subtitles.en.srt` (Inglés Técnico)

### Paso C: Importación a Drift MCP
Importar la pista de subtítulos deseada al proyecto en Drift:
```json
{
  "name": "mcp__drift__apply",
  "arguments": {
    "ops": [
      { "tool": "import_subtitle_file", "args": { "path": "/path/to/subtitles.es.srt", "at": 0 } }
    ]
  }
}
```

---

## 3. Generación de Assets & B-Roll con IA

Cuando se requieran imágenes de apoyo, fondos o B-Roll estilizado, combinar los 3 generadores disponibles:

### A. Pollinations.ai (Rápido, Gratuito, Sin API Key)
Usar el script incluido en la skill para generar imágenes en formato 9:16 o 16:9:
```bash
# Para Reels / Shorts (9:16)
python3 ~/.hermes/skills/media/video-editor-studio/scripts/generate_pollinations_image.py \
  --prompt "futuristic cybernetic workstation, neon glowing cyan, dark background, 8k resolution" \
  --output "/path/to/assets/broll_01.png" --width 1080 --height 1920 --model flux

# Para YouTube Standard (16:9)
python3 ~/.hermes/skills/media/video-editor-studio/scripts/generate_pollinations_image.py \
  --prompt "developer typing on mechanical keyboard, cinematic warm lighting" \
  --output "/path/to/assets/broll_16_9.png" --width 1920 --height 1080 --model flux
```

### B. Civitai Orchestration MCP
Para generación con modelos específicos o LoRAs:
Usar `mcp__civitai_orchestration__generate_image` indicando modelo, prompt y dimensiones.

### C. Hermes `image_generate` Tool
Usar la herramienta nativa `image_generate(prompt=..., aspect_ratio='portrait'|'landscape')`.

---

## 4. Ensamblaje en Drift MCP & Verificación QA

1. **Inspección Inicial:**
   ```json
   { "name": "mcp__drift__inspect", "arguments": { "clips": true, "detail": true } }
   ```
2. **Importación y Posesionamiento de Media:**
   ```json
   {
     "name": "mcp__drift__apply",
     "arguments": {
       "ops": [
         { "tool": "import_media", "args": { "paths": ["/path/to/video.mp4", "/path/to/audio.mp3"] } },
         { "tool": "add_track", "args": { "type": "video" } },
         { "tool": "place_clip", "args": { "asset": "<videoAssetUUID>", "at": 0, "track": 0 } }
       ]
     }
   }
   ```
3. **Verificación QA Visual (Captura de Frame):**
   Antes de exportar el render final, capturar fotogramas en momentos clave para verificar encuadre y subtítulos:
   ```json
   { "name": "mcp__drift__capture", "arguments": { "timestamp": 2.5, "format": "png" } }
   ```

---

## 5. Integración con Remotion

Para gráficos en movimiento programáticos (Intro animada, lower thirds, barras de progreso o transiciones):
1. Usar el proyecto Remotion en `~/proyectos/reels-instagram` (o crear uno nuevo).
2. Renderizar componentes individuales como clips MP4 o ProRes alpha:
   ```bash
   npx remotion render src/index.ts MainComposition out/overlay.mp4 --width=1080 --height=1920
   ```
3. Importar el resultado a Drift MCP como capa superior de video.

---

## 6. Lista de Chequeo QA Pre-Render
- [ ] ¿El hook visual/auditivo ocurre en los primeros 3 segundos?
- [ ] ¿Están listos los renders para ambos formatos target (`1080x1920` 9:16 y `1920x1080` 16:9)?
- [ ] ¿Están generados los archivos de subtítulos en ES, PT-BR y EN?
- [ ] ¿El volumen de la música de fondo hace ducking adecuado bajo la voz?
- [ ] ¿Se capturó y verificó visualmente con `mcp__drift__capture`?
