---
name: local-ai-tts
description: "Local AI TTS: install/run engines (VibeVoice, Voicebox)."
---

# Local AI TTS (instalar y usar)

## Trigger
- Usuario pide instalar/usar un repo local de TTS o generación de voz (VibeVoice, Voicebox, Kokoro, Piper, Chatterbox, TADA...)
- Usuario pregunta "qué puedo hacer con X modelo de voz" — leer references + repo antes de responder
- Comparar motores TTS para hardware sin GPU

## Contexto de máquina (laptop CachyOS)
- SIN GPU NVIDIA/AMD → torch CPU; el build CUDA por defecto desperdicia ~3GB
- Python del sistema 3.14.6 demasiado nuevo para deps ML pinneadas (transformers 4.51.3, numba/llvmlite, datasets)
- `python3.11.15` en `~/.local/bin/python3.11` — la opción segura para venvs ML
- `uv 0.11.17` disponible (venv + pip rápido)
- ~20GB libres en /home — ojo con disco; stack ML + modelos = 8-12GB+
- Área de proyectos: `~/proyectos/IA-voces/`

## Patrón de instalación estándar (repo ML en CPU)
1. Diagnosticar primero: `nvidia-smi -L`, versiones de python disponibles, disco
2. venv con python3.11: `uv venv .venv --python 3.11`
3. Instalar torch CPU PRIMERO para que pip no baje CUDA: `uv pip install --python .venv torch --index-url https://download.pytorch.org/whl/cpu`
4. Luego `uv pip install --python .venv -e .` (o `-r requirements.txt`)
5. Verificar: `.venv/bin/python -c "import <pkg>, torch, transformers; ..."` imprimiendo versiones
6. El python del sistema es PEP 668 → siempre venv, nunca pip global

## Preferencia del usuario: instalaciones manuales (aprender haciendo)
Cuando diga "dame los pasos, lo hago yo" / "quiero hacerlo a mano para aprender":
- NO ejecutar la instalación. Verificar todo primero, luego entregar pasos exactos.
- Verificar el repo REAL, no pasos genéricos: shallow clone a /tmp, leer justfile/CONTRIBUTING/requirements.txt/pyproject.toml
- Chequear qué YA tiene el usuario (`command -v` de cada prerequisito) y dar solo lo que falta, marcado ✅/❌
- Explicar qué hace cada comando de setup (para que aprenda)
- Ofrecer caminos alternativos (p.ej. `just dev-web` vs `just dev` cuando el build Rust es pesado)

## Pitfalls
- Python 3.14 del sistema → deps ML pinneadas fallan. Elegir siempre 3.11/3.12.
- torch por defecto en Linux = build CUDA. Sin GPU, instalar índice CPU primero.
- Repos HF muertos aguas arriba: `microsoft/VibeVoice-*` fueron removidos; existen forks comunitarios (vibevoice/VibeVoice-1.5B). Leer README "Updates"/notas del fork antes de confiar en model IDs documentados.
- El ruido de shell (errores gitstatus/zsh) al lanzar scripts parece fallo — revisar exit code y salida real del proceso.
- Watch-pattern "error" en procesos background puede matchear ruido de init de zsh, no errores reales — poll antes de reaccionar.
- Demos Gradio: el modelo carga una vez al lanzar; generación en CPU es lenta (RTF ~22x para 1.5B) — fijar expectativas, sugerir engines ligeros.

## Engines cubiertos
- `references/vibevoice.md` — VibeVoice fork comunitario (1.5B/7B/0.5B): multi-speaker largo, streaming realtime, voice cloning, ASR, LoRA finetune
- `references/voicebox.md` — Voicebox (jamiepine): 7 motores TTS incl. ligeros (Kokoro 82M, Chatterbox Turbo 350M, LuxTTS), REST API + MCP, Linux = build source o Docker
