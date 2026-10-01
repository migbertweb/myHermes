---
name: groq-stt-transcripcion
description: "Transcribe audio with Groq Whisper STT; fix tech terms."
version: 1.0.0
author: Migbert + Hermes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [stt, whisper, groq, transcription, postprocess, audio]
---

# Groq STT + Postprocesado de Transcripciones

Transcribir audio local con Groq Whisper (free tier, GPU server-side, ~0.5s por clip corto) y postprocesar SIEMPRE los errores típicos: nombres propios y acrónimos técnicos que Whisper transcribe por fonética.

## When to Use

- Notas de voz, audios de vídeos YouTube, grabaciones → texto.
- Cualquier transcripción donde el hablante use términos técnicos/nombres propios.

## Flujo

1. **Verificar el audio**: `ffprobe -v quiet -show_entries format=duration,size -of default=noprint_wrappers=1 "<archivo>"`. Límite Groq: ~25 MB / 4 horas.
2. **Transcribir** (foreground si el audio es corto; `background=true, notify_on_complete=true` si >10 min o el timeout de 600s no alcanza):

```bash
set -a; source ~/.hermes/.env 2>/dev/null; set +a
curl -s -X POST https://api.groq.com/openai/v1/audio/transcriptions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -F "file=@<ruta con comillas>" \
  -F "model=whisper-large-v3-turbo" \
  -F "language=es" \
  --max-time 900 -o /tmp/stt_real.json -w "HTTP %{http_code} | %{size_download} bytes | %{time_total}s\n"
```

3. **Extraer y guardar** el texto del JSON (`data['text']`) en un `.txt` con el mismo nombre y directorio del audio.
4. **Leer el texto completo** (imprimir en chunks de ~600 chars si es una línea gigante) y cazar TODOS los términos mal transcritos, no solo los obvios.
5. **Postprocesar con python** (lista de tuplas regex→reemplazo, `re.subn`, contar cada uno). Backup del original a `/tmp/` antes.
6. **Verificar**: contar ocurrencias de cada término corregido en el resultado + mostrar fragmentos clave.

## Pitfalls

- **Case-sensitivity**: `re.subn` sin flags no matchea "V4 flash" si buscas "v4 flash". Usar `re.IGNORECASE` o variantes explícitas.
- **Órden de reemplazos**: específicos primero ("Dixieck" antes que "dixie", "fin to fin o end to end" antes de "end to end").
- **Dobles dichos**: "Dixieck Dixieck V4 flash" → queda "DeepSeek DeepSeek V4 Flash" (refleja lo hablado, es correcto).
- **No inventar**: si una frase no se puede resolver con certeza, dejarla intacta y listarla como duda para el usuario. Whisper genera ruido al leer texto de terminal ("info.bqm", "un linea tal tal") — se deja.
- **Comandos leídos en voz alta** se rompen feo: "ubicó main app reloj error" → `uvicorn main:app --reload`; "empy en Start" → `npm start`; "main pronto" → `main.py`.
- El gateway bloquea `hermes gateway restart` desde dentro (SIGTERM propaga) — pedir al usuario que lo corra en terminal aparte.

## Lista de términos del entorno de Migbert (confirmados 2026-08-16)

| Mal transcrito (fonético) | Correcto |
|---|---|
| kchos | CachyOS |
| hyperland | Hyprland |
| mvp paper | mpvpaper |
| dance/dan material linux, DanMaterialLinux | Dank Material Linux / DankMaterialLinux |
| MS Shell | DMS Material Shell |
| ovni row, unirro, un emotrón | OmniRoute |
| Oyama Cloud | Ollama Cloud |
| faz/fas/fac api | FastAPI |
| open codec, OpenCodec | OpenCode |
| dixie, Dixieck | DeepSeek (V4 Flash) |
| camba, Canva | Kanban |
| reactme, react-me | README |
| PROM, promos | prompt, prompts |
| Mistur/Mystery of Agents, el mes | MoA (Mixture of Agents) |
| config.yames | config.yaml |
| msp (herramientas) | MCP |
| beck interactivo | PetDex interactivo |
| a su cuna (mascota) | Sukuna |
| futbol (skill) | DogFood |
| robinson cruzó | Robinson Crusoe |
| Ironman | Iron Man |
| requerimiento punto txt, requeriment | requirements.txt |
| main pronto | main.py |
| ubicó main app reloj error | uvicorn main:app --reload |
| empy en Start / RunDeck | npm start / npm run dev |
| en tu end, fin to fin | end to end |
| ya en red | Reddit |
| framework de JSON | framework de Python |
| no module nombrado fastapi | No module named fastapi |

## Verificación del STT de Hermes

- Config: `~/.hermes/config.yaml` → `stt.provider: groq`, `stt.groq.model: whisper-large-v3-turbo`, `stt.groq.language: es` (hermes config set).
- Key: `GROQ_API_KEY` en `~/.hermes/.env` (free tier).
- Tras cambiar config: `hermes gateway restart` desde terminal externa (no desde el chat).
- El STT no loguea al arranque — se inicializa bajo demanda al llegar el primer audio.
