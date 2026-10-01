---
name: youtube-editor
description: Edita videos: cortes, transiciones, audio, timing, sincronización. Usa FFmpeg, imagen, image_generate. Worker M3 del equipo youtube_team.
platforms: [linux]
---

# YouTube Editor (M3 worker)

Esta skill la carga el **worker de video** del agente `youtube_team`.
El orquestador (deepseek-v4-flash-free) la activa cuando el usuario pide:
"edita el video", "corta esto", "sincroniza con audio", "ajusta el timing".

## Cuándo el orquestador debe activar esta skill

- **Edición de video real** (cortes, transiciones, concatenación)
- **Procesamiento de audio** (normalización, sincronización, música)
- **Conversión de formato** (mp4, webm, codecs)
- **Generación de clips** (para Shorts a partir de video largo)
- **Color correction** / grading básico
- **Composición multicapa** (picture-in-picture, lower-thirds, intro/outro)
- **Export final** con settings YouTube-optimized

## NO usar esta skill para

- Guión o copy (eso es `youtube-script` con deepseek)
- Generación de thumbnails (eso es `youtube-thumbnail` con M3 también, pero skill separada)
- SEO/metadata (eso es `youtube-script` con deepseek)
- Publishing (eso es `youtube-publisher` con gemma4)

## Stack de herramientas del worker M3

```python
# El worker M3 TIENE acceso directo a:
- terminal: para correr ffmpeg, ffprobe, sox, audacity-cli
- file: para leer assets, escribir intermediate files
- vision_analyze: para revisar frames específicos
- image_generate (FAL.ai FLUX 2 Klein): para generar B-roll/inserts
- youtube-content (skill): para obtener el video original si es URL
```

## FFmpeg — comandos base que el worker debe conocer

```bash
# Info del video
ffprobe -v error -show_format -show_streams input.mp4

# Cortar (lossless, stream copy)
ffmpeg -i input.mp4 -ss 00:01:30 -to 00:05:00 -c copy output.mp4

# Cortar + re-encode (cuando necesitas precisión de frame)
ffmpeg -i input.mp4 -ss 00:01:30 -to 00:05:00 -c:v libx264 -c:a aac output.mp4

# Normalizar audio
ffmpeg -i input.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v copy output.mp4

# Concatenar varios clips
echo "file 'clip1.mp4'
file 'clip2.mp4'
file 'clip3.mp4'" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

# Extraer frame para thumbnail o análisis
ffmpeg -ss 00:01:30 -i input.mp4 -frames:v 1 -q:v 2 frame.png

# Generar Short vertical 9:16 desde un clip 16:9
ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih" -c:a copy short.mp4

# Export YouTube-optimized (1080p, h264, AAC)
ffmpeg -i input.mp4 \
  -c:v libx264 -preset slow -crf 18 \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  -pix_fmt yuv420p \
  youtube_final.mp4
```

## Convenciones del worker M3

1. **NUNCA** destruir el original — siempre trabajar sobre copia con sufijo `_edit.mp4`
2. **SIEMPRE** verificar el resultado con `ffprobe` antes de reportar éxito
3. **SIEMPRE** incluir duración final, bitrate, resolución en el reporte al orquestador
4. **Logs** en `~/.hermes/skills/youtube-editor/editor.log`
5. **Intermediate files** en `/tmp/yt-edit-<timestamp>/` y limpiar al terminar

## Reporte al orquestador

```json
{
  "status": "ok | error | partial",
  "input": "/path/to/input.mp4",
  "output": "/path/to/output.mp4",
  "metadata": {
    "duration_s": 1234,
    "resolution": "1920x1080",
    "fps": 30,
    "video_bitrate": "8 Mbps",
    "audio_bitrate": "192 kbps",
    "size_mb": 234
  },
  "operations_applied": ["corte 0:30", "audio normalized", "intro agregada"],
  "warnings": [],
  "errors": []
}
```

## Cómo invocar al worker

```
delegate_task(
  goal="<tarea de edición específica>",
  context="<input path, output spec, duración objetivo>",
  role="leaf",
  toolsets=["terminal", "file", "vision"]
)
# NOTA: Este worker DEBE ser M3 (minimax-m3) — el orquestador lo especifica
# via agent_definition en youtube_team.yaml
```

## Pitfalls

- **No usar `-c copy` después de un corte si el corte no es keyframe-aligned** — se va a descuadrar
- **No aplicar `loudnorm` dos veces** — distorsiona
- **No subir videos >2GB al canal sin comprimir** — YouTube rechaza o tarda horas
- **No olvidar `-movflags +faststart`** — sin esto, YouTube no puede empezar a reproducir hasta descargar todo
- **Aspect ratio 9:16 para Shorts** — recortar desde el centro SIEMPRE mata el contenido, mejor reencuadrar inteligente con `cropdetect`
