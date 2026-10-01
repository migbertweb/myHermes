# VibeVoice (fork comunitario) — detalle de sesión 2026-08-08

Repo: https://github.com/vibevoice-community/VibeVoice (MIT; backup del removido microsoft/VibeVoice)
Instalado en: `~/proyectos/IA-voces/vibevoice`, venv `.venv` (py3.11, torch 2.13.0+cpu, vibevoice 0.1.0 editable, transformers 4.51.3).

## Model Zoo (HuggingFace)
| Modelo | Contexto | Longitud | Speakers | Notas |
|---|---|---|---|---|
| VibeVoice-1.5B (`vibevoice/VibeVoice-1.5B`) | 64K | ~90 min | hasta 4 | voice cloning desde wav de referencia |
| VibeVoice-7B (`vibevoice/VibeVoice-7B`) | 32K | ~45 min | hasta 4 | más estable (BGM, canto, zh); requiere GPU |
| Realtime-0.5B (`microsoft/VibeVoice-Realtime-0.5B` — **muerto**, ver nota) | 8K | real-time | 1 | voice embeddings precomputados .pt; ideal CPU |

⚠️ **Gotcha clave**: `demo/inference_from_file.py` tiene `default="microsoft/VibeVoice-1.5b"` (modelo removido). Siempre pasar `--model_path vibevoice/VibeVoice-1.5B`. El Realtime-0.5B de Microsoft también fue removido — verificar backup comunitario antes de usarlo.

## Comandos
```bash
# CLI multi-speaker
.venv/bin/python demo/inference_from_file.py --model_path vibevoice/VibeVoice-1.5B --device cpu \
    --txt_path demo/text_examples/2p_music.txt --speaker_names "Alice Frank"

# Streaming 0.5B (voces: Carter Davis Emma Frank Grace Mike Samuel; .pt en demo/voices/streaming_model/)
.venv/bin/python demo/streaming_inference_from_file.py --model_path <realtime-model> \
    --speaker_name Emma --cfg_scale 1.5 --ddpm_steps 5

# UI Gradio
.venv/bin/python demo/gradio_demo.py --model_path vibevoice/VibeVoice-1.5B --device cpu  # → http://127.0.0.1:7860

# ASR (batch: archivos, directorio o dataset HF)
.venv/bin/python demo/vibevoice_asr_inference_from_file.py --model_path <asr-model> --audio_dir <dir>

# Finetune LoRA (experimental, single-speaker, requiere GPU bf16)
python -m vibevoice.finetune.train_vibevoice --model_name_or_path vibevoice/VibeVoice-1.5B ...
```

## Notas del Gradio demo
- El código tiene `server_port=args.port` **comentado** → el `--port` se ignora; Gradio usa 7860 por defecto.
- Carga 9 voces (demo/voices/) y 8 guiones de ejemplo; filtra scripts >15 min.
- Streaming mode ENABLED (escucha mientras genera); cola 1 request a la vez.

## Capacidades
- Conversaciones/podcasts largos multi-speaker (hasta 4 voces, 90 min)
- Voice cloning desde wav de referencia; `--disable_prefill` para voz genérica sin clonar
- Emergentes (no controlables): BGM/música espontánea (heredada si el prompt de voz tiene música), canto (7B mejor), cross-lingual EN↔ZH con acento (inestable, re-sampling)
- Control de emoción vía truco PsiPi (HF discussion #12 en microsoft/VibeVoice-1.5B)
- Sin normalización de texto; zh inestable → usar puntuación EN, variante 7B, dividir turnos largos

## Realidad en CPU (laptop sin GPU)
1.5B: RTF ~22x (63s audio ≈ 23 min generación), 321% CPU (~3.2 cores), ~11GB RAM. El streaming 0.5B es la opción usable en tiempo real. 7B inviable sin GPU.
