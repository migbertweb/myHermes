---
name: voz-output-friendly
description: "Output para TTS. Sin barras, extensiones, rutas ni tablas."
version: 1.0.0
---

# Output friendly para voz (TTS)

Aplicar SIEMPRE que la respuesta vaya a ser leída en voz alta (Telegram con TTS activo, voice-to-voice). El TTS lee literal: barras, puntos de extensión, guiones bajos.

## Reglas absolutas

### 1. Cero barras
Nunca escribir `/`. El TTS dice "barra diagonal".
- ❌ `config/tools` → ✅ "la carpeta config, dentro tools"
- ❌ `~/.hermes/profiles/` → ✅ "la carpeta profiles dentro de hermes en tu home"
- ❌ `clave/valor` → ✅ "clave y valor" o "clave, valor"

### 2. Cero extensiones de archivo
Nunca escribir `.md`, `.yaml`, `.db`, `.json`, etc. El TTS hace pausa en el punto y deletrea la extensión.
- ❌ `soul.md` → ✅ "Soul"
- ❌ `config.yaml` → ✅ "config" o "el archivo de configuración"
- ❌ `state.db` → ✅ "la base de datos" o "state"
- Si necesito aclarar el formato, va en frase aparte: "es un archivo yaml" o "en formato markdown"

### 3. Cero guiones bajos ni snake_case
- ❌ `api_key` → ✅ "api key" o "la clave de la API"
- ❌ `max_turns` → ✅ "max turns" o "el límite de turnos"

### 4. Nada de rutas técnicas
- ❌ `~/.hermes/hermes-agent/hermes_cli/profiles.py` → ✅ "el módulo de perfiles en el código fuente de Hermes"

### 5. Nada de tablas
Las tablas son ilegibles en voz. Describir en frases, viñetas, o estructura hablada.
- ✅ "Tienes tres archivos: el de configuración, el de secretos, y el de personalidad"
- ❌ tabla con columnas archivo | función

### 6. Puntos y enumeraciones
Cuidado con números seguidos de punto — el TTS puede interpretarlos mal.
- ❌ "1. primero 2. segundo" → ✅ "primero, ... segundo, ..." o usar guiones

## Checklist pre-respuesta
Antes de soltar cualquier respuesta por voz, repasar:
- ¿Hay alguna barra? → reescribir
- ¿Hay alguna extensión de archivo? → quitar
- ¿Hay guiones bajos? → separar
- ¿Hay una ruta técnica? → describir en palabras
- ¿Hay tabla? → convertir a frases
