---
name: youtube-script
description: Genera guiones, escaletas, hooks, SEO y metadata para videos de YouTube. Usado por el worker deepseek del equipo youtube_team.
platforms: [linux]
---

# YouTube Script & SEO (deepseek worker)

Esta skill la carga el **worker de scripting/SEO** del agente `youtube_team`.
El orquestador (deepseek-v4-flash-free) la activa cuando el usuario pide:
"hazme un guión", "escribe la escaleta", "dame títulos SEO", "metadata para YouTube".

## Cuándo el orquestador debe activar esta skill

- Pedidos de **guión completo** o **escaleta** para un video
- Pedidos de **hook** (primeros 5-15 segundos)
- Pedidos de **títulos alternativos** y **descripción SEO**
- Pedidos de **tags**, **hashtags**, **pinned comment**
- Pedidos de **storyboard** visual (qué mostrar en cada sección)
- Pedidos de **CTA** (calls to action)
- Pedidos de **timeline con secciones** a partir de una transcripción
- Análisis de **keywords** o ángulos

## También activar cuando (video local)

- El usuario comparte un **archivo de video local** (`.mp4`, `.mkv`) y pide procesarlo para YouTube
- El usuario pide **transcripción** de un video en disco
- El usuario tiene una transcripción cruda de ASR y pide **corregir errores** + generar metadata

## NO usar esta skill para

- Edición de video real (eso es `youtube-editor` con M3)
- Generación de thumbnails (eso es `youtube-thumbnail` con M3)
- Publishing/scheduling (eso es `youtube-publisher` con gemma4)

## Workflow: video local → YouTube metadata

Cuando el usuario da un archivo de video local, el worker ejecuta este pipeline:

1. **Extraer audio** con ffmpeg (mono 16kHz WAV):
   ```bash
   ffmpeg -y -i "<video.mp4>" -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/audio.wav
   ```
2. **Transcribir** con faster-whisper (modelo `small` para CPU, `tiny` si es urgente):
   ```python
   from faster_whisper import WhisperModel
   model = WhisperModel("small", device="cpu", compute_type="int8")
   segments, info = model.transcribe("/tmp/audio.wav", language="es")
   ```
   - Guardar con timestamps: `[inicio -> fin] texto`
   - Verificar que `language` sea español; sino, retranscribir sin `language`.

3. **Corregir errores de ASR** — Whisper en español malinterpreta términos técnicos recurrentemente. Consultar `references/asr-correction-patterns.md` para el mapeo de correcciones comunes.

4. **Generar metadata** a partir de la transcripción corregida:
   - Descripción SEO
   - Timeline con secciones
   - Tags / hashtags
   - Títulos sugeridos

## Herramientas requeridas

```bash
# Verificar disponibles:
which ffmpeg ffprobe
pip list 2>/dev/null | grep -i faster-whisper
```

Si falta faster-whisper:
```bash
pip install faster-whisper
```

## Formato de salida

El worker SIEMPRE devuelve al orquestador un bloque JSON estructurado más markdown legible:

```json
{
  "tipo": "guion | escaleta | hook | seo | storyboard | cta",
  "video_id": "<número o slug>",
  "titulo_sugerido": ["opción 1", "opción 2", "opción 3"],
  "descripcion_seo": "...",
  "tags": ["...", "..."],
  "hashtags": ["#...", "#..."],
  "duracion_estimada_min": 15,
  "hook_15s": "...",
  "escaleta": [
    {"timestamp": "0:00-1:30", "seccion": "Intro", "contenido": "...", "b_roll": "..."}
  ]
}
```

## Estilo de escritura

- **Idioma:** Español latino neutro (venezolano-suave, brasilero cuando aplique)
- **Tono:** cercano, técnico pero accesible, sin academicismos
- **Voz del creador:** entusiasta de Linux, DevOps, tech libre. Nada de "estimados suscriptores" ñoño.
- **Hook obligatorio:** los primeros 5 segundos tienen que tener una pregunta, dato shocking, o demo visual impactante
- **Estructura del guión:**
  1. Hook (0:00-0:15)
  2. Setup / promesa (0:15-1:30)
  3. Desarrollo por bloques numerados
  4. Demo en vivo
  5. Problemas comunes / troubleshooting
  6. CTA + despedida

## Contexto del canal

Canal: **Migbert on Linux** (`@migbertonlinux`)
Tagline: *"La tecnología libre no es para temer, sino para crecer"*
Tags base: `linux`, `programacion`, `tecnologia`, `venezuela`, `thinkpad`, `archlinux`
Audiencia: developers hispanohablantes, DevOps junior-mid, entusiastas Linux

## Patrones que funcionan (data del canal)

- **Series largas** retienen mejor que videos sueltos (Dokploy 5-partes fue su mejor racha)
- **Quickshell/QML/Hyprland**几乎没有 competencia en español → prioridad alta
- **Comparativas** generan CTR (Brave vs Vivaldi, Copilot vs Gemini)
- **DevOps práctico** > tutoriales genéricos
- **Personalización daily-driver** engancha (mostrar tu setup real, no slides)

## Cómo invocar al worker

Desde el orquestador deepseek-v4-flash-free:

```
delegate_task(
  goal="<pedido específico>",
  context="<resumen del video, ángulo, duración>",
  role="leaf",
  toolsets=["web", "terminal", "file"]
)
# Este worker hereda el modelo del agente (deepseek)
```

## Pitfalls

- **No inventar métricas** ("10x más rápido" sin fuente) — el worker debe pedir medición o usar "potencialmente"
- **No usar jerga anglo innecesaria** (excepto términos técnicos ya establecidos: Wayland, kernel, deploy)
- **No repetir el hook** en el cuerpo — quemarlo en 15s y avanzar
- **No escribir escaletas sin timestamps** — el editor (M3) los necesita para cortar
- **ASR: siempre corregir términos técnicos** — Whisper en español confunde nombres propios (CachyOS, Hyprland, DeepSeek, ThinkPad, Syncthing, Fastfetch, DankMatterShell). Consultar `references/asr-correction-patterns.md` antes de entregar transcripción al usuario.
- **ASR: detectar dobles palabras** — Whisper en español suele duplicar artículos ("una una", "de los de los"). Revisar y colapsar.
- **No adivinar el idioma** — siempre verificar `info.language` del resultado de faster-whisper. Si no es español, retranscribir forzando `language="es"`.
