# VibeVoice — instalación y uso (fork comunitario)

Repo: https://github.com/vibevoice-community/VibeVoice — fork de preservación tras la remoción del repo oficial de Microsoft (2025-09). TTS conversacional AR + difusión, hasta 4 speakers, audio largo (hasta 90 min con 1.5B).

Instalado en: `/home/migbert/proyectos/IA-voces/vibevoice` (`.venv` Python 3.11.15, torch 2.13.0+cpu, transformers 4.51.3 pin del proyecto).

## Modelos HF — ids vivos vs muertos

| Modelo | Id HF | Uso |
|---|---|---|
| 1.5B | `vibevoice/VibeVoice-1.5B` ✅ vivo | largo, multi-speaker, 64K ctx |
| 7B (Large) | `vibevoice/VibeVoice-7B` | más estable, 32K ctx |
| Streaming/Realtime 0.5B | `VibeVoice-Realtime-0.5B` | real-time 1 speaker, voice embeddings .pt, MEJOR opción CPU |

⚠️ Los ids `microsoft/VibeVoice-*` del repo original están MUERTOS (Microsoft removió repo y modelos). Los scripts traen defaults al id muerto o a path local inexistente:
- `demo/inference_from_file.py`: default `microsoft/VibeVoice-1.5b` → pasar `--model_path vibevoice/VibeVoice-1.5B`
- `demo/gradio_demo.py`: default `/tmp/vibevoice-model` (path local) → pasar el id de HF igual que en CLI

## Comandos validados

Instalación (desde el root del repo):
```bash
uv venv .venv --python 3.11
uv pip install --python .venv torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv -e .
```

Inferencia CLI:
```bash
.venv/bin/python demo/inference_from_file.py --model_path vibevoice/VibeVoice-1.5B --device cpu
# → escribe ./outputs/<input>_generated.wav
```

UI Gradio:
```bash
.venv/bin/python demo/gradio_demo.py --model_path vibevoice/VibeVoice-1.5B --device cpu
# → http://127.0.0.1:7860 · 9 voces de demo/voices/ · 8 ejemplos · streaming ENABLED · cola 1 request
```

## Datos de rendimiento (CPU, laptop CachyOS, 23GB RAM)

- 1.5B en CPU: RTF ~22x → 63s de audio = ~23 min de generación (1404s, 478 tokens, prefill 319). RAM ~47% (~11GB), CPU ~3.2 cores.
- `demo/gradio_demo.py` tiene `server_port=args.port` COMENTADO → el flag `--port` no hace efecto, Gradio usa 7860.
- La demo Gradio skipea ejemplos >15 min de audio.
- El progress de generación no es lineal: el head de difusión va al final y es lo más pesado; `outputs/` se escribe al terminar (no incremental).
- Formato de guion: `[Speaker] texto` por turno; voces mapeadas a los wav en `demo/voices/`.
- Para uso real en CPU: VibeVoice-Streaming-0.5B (embeddings .pt precomputados, baja latencia) — hay voice cloning no oficial de la comunidad (`mohammed-bahumaish/vibevoice-realtime-0.5b-with-encoder`).
- Fine-tuning soportado (ver FINETUNING.md del repo, LoRA).
