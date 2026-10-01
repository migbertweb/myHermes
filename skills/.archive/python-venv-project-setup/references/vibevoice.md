# VibeVoice — notas de instalación e inferencia

TTS conversacional de Microsoft (AR + difusión, tokenizers continuos a 7.5 Hz, hasta 90 min de audio, 4 speakers).

## Estado del repo (importante)
- Microsoft **eliminó** el repo y los modelos originales (sept 2025). El código vive en el fork comunitario `vibevoice-community/VibeVoice`.
- Pesos respaldados en HuggingFace org `vibevoice/`.
- ⚠️ El default de `demo/inference_from_file.py` es `microsoft/VibeVoice-1.5b` — está muerto (404). Usar `vibevoice/VibeVoice-1.5B`.
- Comunidad: Discord https://discord.gg/ZDEYTTRxWG

## Model Zoo

| Modelo | Contexto | Generación | Speakers | Nota |
|---|---|---|---|---|
| VibeVoice-Streaming-0.5B | 8K | tiempo real | 1 | Voice embeddings precomputados (.pt); mejor opción sin GPU |
| VibeVoice-1.5B | 64K | ~90 min | hasta 4 | Default razonable |
| VibeVoice-Large (7B) | 32K | ~45 min | hasta 4 | Más estable, más lento en CPU |

Voice cloning no oficial del streaming: `mohammed-bahumaish/vibevoice-realtime-0.5b-with-encoder`.

## Instalación local (hecha 2026-08-08)

Ruta: `/home/migbert/proyectos/IA-voces/vibevoice`, venv `.venv` (Python 3.11.15, torch 2.13.0+cpu, transformers 4.51.3).

```bash
uv venv .venv --python 3.11
uv pip install --python .venv torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv -e .
```

Pyproject pinnea `transformers==4.51.3`, `datasets==3.5.0`, `gradio==5.50.0` — incompatibles con Python 3.14 del sistema.

## Inferencia

```bash
source .venv/bin/activate
python demo/inference_from_file.py --model_path vibevoice/VibeVoice-1.5B --device cpu
```

- Primer run descarga ~3GB de pesos (HF).
- Voces preset en `demo/voices/*.wav`; `demo/inference_from_file.py` mapea nombres de speaker → wav (VoiceMapper).
- Textos de ejemplo en `demo/text_examples/` (ej. `1p_abs.txt`).
- Flags útiles: `--model_path`, `--input_file`, `--speaker`, `--output_dir`, `--device`, `--temperature` (default 1.3).
- Demo interactiva: `python demo/gradio_demo.py`. Streaming: `demo/streaming_inference_from_file.py`.

## Fine-tuning

- `FINETUNING.md` en raíz. Soporta LoRA para nueva voz/idioma.
- `vibevoice/scripts/merge_vibevoice_models.py` fusiona base + LoRA.
- Convertidor de checkpoints nnScaler → transformers en `vibevoice/scripts/`.

## Tips del README

- Chino inestable → usar puntuación inglesa (solo comas/puntos), preferir modelo Large.
- Voz muy rápida → trocear texto en múltiples turns con el mismo speaker label.
- Control de emoción: ver discussion #12 en HF (PsiPi).
