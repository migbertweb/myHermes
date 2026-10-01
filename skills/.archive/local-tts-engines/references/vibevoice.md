# VibeVoice — model zoo, usage, CPU notes

Repo: github.com/vibevoice-community/VibeVoice (community fork; Microsoft removed original repo + models 2025-09). MIT. Fork adds unofficial finetuning. Original: microsoft/VibeVoice (paper arxiv 2508.19205).

## Model zoo

| Model | Context | Gen length | Speakers | HF id |
|---|---|---|---|---|
| Streaming-0.5B | 8K | real-time, ~10 min audio | 1 | microsoft/VibeVoice-Realtime-0.5B |
| 1.5B | 64K | ~90 min | up to 4 | vibevoice/VibeVoice-1.5B |
| Large (7B) | 32K | ~45 min | up to 4 | vibevoice/VibeVoice-7B |

## Streaming-0.5B language facts (HF model card, verified 2026-08)

- Official: English only (trained on EN data only). "Other languages may produce unpredictable results."
- 9 EXPERIMENTAL languages provided for exploration: German, French, Italian, Japanese, Korean, Dutch, Polish, Portuguese, Spanish. Untested, unstable.
- Single speaker. ~300ms first-audio latency. Voice presets are precomputed .pt embeddings: Carter, Davis, Emma, Frank, Grace, Mike (EN); Samuel (Indian EN). NO voice cloning.
- Warning "Some weights not initialized from checkpoint" on load is EXPECTED (voice-cloning removed).

## 1.5B/7B capabilities

- Multi-speaker podcasts: up to 4 distinct speakers, turn-taking, 90 min in one pass.
- Voice cloning from reference wav (demo/voices/*.wav presets); `--disable_prefill` skips speaker conditioning.
- Emergent behaviors (not controllable): spontaneous BGM/music (voice prompt with BGM tends to inherit it; 7B more stable), singing (off-key, emergent — no music in training data), cross-lingual EN↔ZH with accent retention (unstable, resample), Chinese ok with English punctuation + 7B.
- Emotion control via PsiPi trick (HF discussion #12 on microsoft/VibeVoice-1.5B).
- ASR model included: demo/vibevoice_asr_inference_from_file.py (batch, dirs, or HF datasets like LibriSpeech) + vibevoice_asr_gradio_demo.py.

## CPU reality (no GPU, measured 2026-08)

- 1.5B: RTF ≈ 22x → 63s audio took 1405s (~23 min). Prefill 319 + 478 gen tokens. fp32 ~11GB RAM.
- Gradio demo: `python demo/gradio_demo.py --model_path vibevoice/VibeVoice-1.5B --device cpu` → :7860, 9 voices from demo/voices/, 8 example scripts loaded (45/100-min ones skipped), streaming enabled, concurrency 1.
- CLI: `python demo/inference_from_file.py --model_path vibevoice/VibeVoice-1.5B --txt_path demo/text_examples/1p_abs.txt --speaker_names Andrew --device cpu` → outputs/1p_abs_generated.wav.
- Streaming CLI: `python demo/streaming_inference_from_file.py --model_path microsoft/VibeVoice-Realtime-0.5B --txt_path demo/text_examples/1p_vibevoice.txt --speaker_name Emma --cfg_scale 1.5 --ddpm_steps 5` (lower steps = faster).
- NOTE: script defaults point to `microsoft/...` which was REMOVED — check community mirrors before running.

## Finetune (experimental, GPU required)

- `python -m vibevoice.finetune.train_vibevoice` — LoRA, single-speaker only. Dataset text format `Speaker 1: text`. bf16. Community tip: single-voice training → `voice_prompt_drop_rate 1.0` (kills cloning support, more natural).
- Merge: vibevoice/scripts/merge_vibevoice_models.py --base_model_path model --checkpoint_path output/lora --output_path merged.
