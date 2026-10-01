---
name: local-ml-repo-setup
description: Use when installing/running a Python ML repo in a venv.
---

# Local ML repo setup (venv + CPU)

Instalar y correr repos de ML/IA clonados de GitHub (TTS, difusión, modelos HF) en las máquinas del usuario (laptop CachyOS, server). Patrón validado con VibeVoice (ver `references/vibevoice.md`).

## Workflow

1. **Recon del repo**: leer `pyproject.toml` (deps y pins) y la sección Installation del README ANTES de crear el venv.
2. **Compatibilidad de Python**: si las deps están pinneadas a versiones viejas (`transformers==4.5x`, `datasets==3.5.x`, `numba`/`llvmlite`) NO usan el Python del sistema si es 3.13+. En CachyOS el sistema trae 3.14 y esas deps no compilan/instalan ahí. Usar Python viejo gestionado por uv:
   ```bash
   uv venv .venv --python 3.11   # 3.11 ya está en ~/.local/bin/python3.11 (uv-managed)
   ```
3. **Sin NVIDIA GPU → torch CPU primero**: `nvidia-smi` falla en ambas máquinas del usuario. Instalar torch CPU con su índice ANTES que el proyecto, para que uv/pip no baje el build CUDA (~3GB de desperdicio):
   ```bash
   uv pip install --python .venv torch --index-url https://download.pytorch.org/whl/cpu
   uv pip install --python .venv -e .
   ```
   El orden importa: si instalas el proyecto primero, resuelve torch CUDA por defecto.
4. **Verificar import**: `.venv/bin/python -c "import <pkg>, torch, transformers; print(torch.__version__, transformers.__version__)"`.
5. **Chequear que los modelos HF existan**: repos upstream de Microsoft/AI labs se remueven (VibeVoice fue borrado 2025-09). Leer el Model Zoo del README y usar el id del espejo comunitario; los defaults de los scripts suelen apuntar al id muerto. Pasar el id vivo explícitamente en `--model_path`.
6. **Primera inferencia**: correr el script demo en background, avisar al usuario que en CPU los tiempos son largos (ver pitfall RTF).
7. **UI Gradio**: lanzar en background; el signal de readiness es `Running on local URL: http://127.0.0.1:PORT`.

## Pitfalls

- **Python 3.14 + numba/llvmlite/transformers viejo = incompatible, no pelear** — usar 3.11/3.12 vía uv.
- **El progress de generación no es lineal** — el head de difusión va al final y es lo más pesado; outputs/ se escribe al terminar, no incremental. No confundir "50%" con "mitad del tiempo".
- **El flag `--port` de scripts Gradio puede estar ignorado** si el código tiene `server_port=args.port` comentado (pasa en VibeVoice) — Gradio cae a 7860.
- **Watch patterns en background**: al lanzar procesos desde la shell zsh del usuario, el ruido de arranque (gitstatus "failed to initialize", "error") genera falsos positivos con watch_patterns=['error']. Usar el pattern de readiness real ("Running on local URL") y no alarmarse por el ruido.
- **Inferencia CPU**: RTF típico ~20x (1 min de audio ≈ 20+ min de cómputo). Para uso real en CPU, preferir el modelo streaming/chico del repo (VibeVoice-Realtime-0.5B en vez del 1.5B).
- RAM: un 1.5B en fp32 cabe en 23GB, usar ~11GB; CPU ~3 cores.

## References
- `references/vibevoice.md` — VibeVoice: ids de modelos vivos/muertos, comandos validados, timings CPU, quirks de la demo Gradio.
