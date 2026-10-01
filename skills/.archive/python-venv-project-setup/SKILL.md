---
name: python-venv-project-setup
description: Use when installing a Python/ML git project into a venv.
---

# Python/ML Project Venv Setup

Instalar proyectos Python o ML/AI clonados de GitHub en un venv aislado, sin romper el sistema y sin descargar binarios inútiles.

## Trigger
- "clona X e instálalo" / "setup de Y" / "install this repo" para cualquier proyecto Python con pyproject.toml o requirements.txt
- Instalación de modelos ML (TTS, LLM, difusión) que dependen de torch/transformers

## Workflow

1. **Clonar**: `git clone <url> .` dentro del directorio destino (verificar que esté vacío antes).
2. **Leer pyproject.toml + README primero**: pinneos de versión y sección Installation mandan. El README del repo suele indicar el comando exacto (`uv pip install -e .`, `pip install -r requirements.txt`, etc.).
3. **Verificar compatibilidad del intérprete ANTES de crear el venv**:
   - Python del sistema suele ser 3.13/3.14 (CachyOS/Arch), pero deps pinneadas tipo `transformers==4.51.3`, `datasets==3.5.0`, `numba>=0.57`+`llvmlite` NO soportan 3.14.
   - Buscar alternativas: `which python3.13 python3.12 python3.11 python3.10` (suelen vivir en `~/.local/bin` vía uv/ASDF). Si no hay, `uv python install 3.11` lo descarga.
4. **Chequear GPU**: `nvidia-smi -L`. Sin GPU NVIDIA → instalar **torch CPU primero**, antes del install editable, para no arrastrar ~3GB de binarios CUDA:
   ```bash
   uv venv .venv --python 3.11
   uv pip install --python .venv torch --index-url https://download.pytorch.org/whl/cpu
   ```
5. **Instalar el proyecto**: `uv pip install --python .venv -e .` — en background con `notify_on_complete=true` si baja muchas deps (gradio, librosa, etc.).
6. **Verificar**: `.venv/bin/python -c "import <pkg>, torch; print(torch.__version__)"` y confirmar versiones de las deps pinneadas clave.

## Pitfalls

- **PEP 668**: pip del sistema en Arch/CachyOS está bloqueado (externally-managed-environment). Siempre venv o uv, nunca `pip install` global.
- **torch por defecto de PyPI baja CUDA** aunque no haya GPU — siempre `--index-url https://download.pytorch.org/whl/cpu` cuando `nvidia-smi -L` no reporte nada.
- **Repos eliminados de Microsoft/grandes empresas**: verificar si existe fork comunitario y backup de pesos en HuggingFace. Los defaults de los scripts de inferencia pueden apuntar a repos HF muertos (404) — el backup suele vivir en otra org (`vibevoice/VibeVoice-1.5B` vs `microsoft/VibeVoice-1.5b`).
- **Ruido de shell de uv/zsh** (gitstatus, "can't change option: monitor") en el output de install es inofensivo — mirar el exit_code y las líneas `+ paquete==version`.
- Modelos grandes en CPU: inferencia lenta; si el proyecto ofrece variante streaming/pequeña (0.5B vs 7B), es la opción usable sin GPU.

## References
- `references/vibevoice.md` — detalles específicos de VibeVoice (fork, model zoo, comandos de inferencia, estado de la instalación local).
