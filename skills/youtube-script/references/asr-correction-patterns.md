# ASR Correction Patterns — Whisper (Spanish, Tech Content)

Whisper (`faster-whisper` model `small`) comete errores sistemáticos al transcribir
contenido técnico en español. Este archivo documenta los patrones observados para
que el corrector los aplique automáticamente.

## Marcas / Nombres propios

| Whisper (erróneo) | Corrección | Contexto |
|---|---|---|
| `tímpacta`, `timapac` | **ThinkPad** | Laptop Lenovo |
| `CacheOS` | **CachyOS** | Distro Linux basada en Arch |
| `Iperlap`, `Hiperland` | **Hyprland** | Compositor Wayland |
| `DanLinux`, `dan linus`, `Dank matter` | **DankMatterShell** | Shell/panel QML para Hyprland |
| `Dixie` | **DeepSeek** | Proveedor de modelos LLM |
| `Cintin`, `Sintin` | **Syncthing** | Herramienta de sincronización P2P |
| `fafesh`, `fafetch` | **Fastfetch** | Herramienta info sistema (neofetch) |
| `lino`, `Linu` | **Linux** | Sistema operativo |
| `Handy` | **Handy** | (correcto — app de transcripción) |
| `Cachy` | **CachyOS** | Forma corta de la distro |
| `Open Router` | **OpenRouter** | Agregador de modelos LLM |

## Términos técnicos / jerga

| Whisper (erróneo) | Corrección | Contexto |
|---|---|---|
| `setú` | **setup** | Configuración / equipo |
| `SP32`, `S P 32` | **ESP32** | Microcontrolador |
| `plasquillas`, `plaquitas` | **plaquitas** | (ya correcto) |
| `pantalleta` | **pantallita** | Pantalla pequeña (diminutivo) |
| `multi-hugging` | **multi-agent** | Arquitectura de múltiples agentes AI |
| `al acto`, `alato` | **al laptop** | Al computador portátil |
| `platita` | **la placa** | La placa (ESP32), o **laptop** según contexto |
| `la obra` | **la hora** | Contexto: clima, hora |
| `por clic` | **por CLI** | Interfaz de línea de comandos |
| `Hygiene`, `Herman` | **Agent** | Hermes Agent (nunca "Hygiene") |
| `el doc` | **el dock** | Panel dock de DankMatterShell |

## Patrones de ASR recurrentes

1. **Duplicación de palabras**: Whisper duplica artículos y preposiciones
   - "una una" → "una"
   - "de los de los" → "de los"
   - "con el con el" → "con el"

2. **Marcas extranjeras castellanizadas**: Whisper aplica fonética española a
   marcas en inglés, perdiendo la grafía original. Siempre verificar nombres
   propios contra la lista arriba.

3. **Palabras compuestas separadas**: "multihugging" como separado, "setú" como
   una palabra. Revisar términos compuestos.

4. **Acentos perdidos / mal puestos**:
   - "regalo" (presente) → "regaló" (pretérito) cuando es 3a persona singular
   - Examinar verbos en tiempo pasado que el ASR deja sin acento.

5. **Artículo erróneo**: "el" por "al" y viceversa, común en habla rápida.

## Workflow de corrección

1. Pasar transcripción contra la tabla de marcas/propietarios primero
2. Colapsar duplicaciones de palabras
3. Revisar verbos en pasado (acentos)
4. Leer la transcripción completa una vez para detectar términos que no
   encajan en el contexto técnico del video
5. Si hay duda sobre un término, dejarlo con nota `[?]` y preguntar al usuario

## Nota

Este archivo se nutre de cada sesión de transcripción. Cuando encuentres un
nuevo patrón de error, agrégalo aquí.
