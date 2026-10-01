---
name: local-tts-engines
description: "Install/compare local TTS engines: VibeVoice, Voicebox."
---

# Local TTS Engines (VibeVoice, Voicebox, ...)

Deploying and choosing local text-to-speech model stacks on Migbert's hardware. Context: CachyOS laptop, NO NVIDIA GPU → CPU-only inference, 23GB RAM. User needs SPANISH support; English-only engines are a dead end for him.

## Engine selection (CPU-only laptop)

| Engine | Size | Languages | CPU speed | Use for |
|---|---|---|---|---|
| Kokoro | 82M | 9 (en-us, en-gb, es, fr-fr, hi, it, pt-br, ja, zh) | instant | fastest preset TTS, no cloning |
| Chatterbox Turbo | 350M | English ONLY | fast | EN + paralinguistic tags `[laugh]` `[sigh]` — no es |
| Chatterbox Multilingual | — | 23 langs (incl. es) | medium | max language coverage (no tags) |
| Qwen3-TTS 0.6B | 0.6B | 10 | acceptable | best CPU balance: Spanish + cloning + delivery instructions |
| LuxTTS | ~1GB VRAM | English | 150x realtime CPU (claimed, unverified) | 48kHz quality |
| VibeVoice-1.5B | 1.5B | en/zh + emergent | RTF ~22x (slow) | long multi-speaker podcasts, up to 4 voices |
| VibeVoice-Streaming-0.5B | 0.5B | English official + 9 experimental (incl. es) | ~300ms latency | real-time streaming, single speaker |

Golden rule: verify language support in the INSTALLED package (pip show / grep lang ALIASES), never trust README claims alone. Verified Kokoro 0.9.4 pipeline.py ALIASES: `en-us, en-gb, es, fr-fr, hi, it, pt-br, ja, zh`. Chatterbox Turbo is EN-only BY DESIGN (its multilingual sibling covers 23 langs but loses paralinguistic tags).

## VibeVoice (vibevoice-community fork of Microsoft's removed repo)

- Pinned deps (transformers==4.51.3, datasets==3.5.0, numba/llvmlite) DON'T work on Python 3.14 → venv with 3.11/3.12.
- Install: `uv venv .venv --python 3.11 && uv pip install --python .venv torch --index-url https://download.pytorch.org/whl/cpu && uv pip install --python .venv -e .` — CPU index first avoids ~3GB of useless CUDA wheels.
- Script default model IDs point to removed `microsoft/...` repos → use community org `vibevoice/VibeVoice-1.5B`.
- CPU reality: 1.5B RTF ≈ 22x (63s audio ≈ 23 min compute). Gradio UI: `python demo/gradio_demo.py --model_path vibevoice/VibeVoice-1.5B --device cpu` (:7860).
- Full model zoo, streaming facts, finetune, ASR: references/vibevoice.md

## Voicebox (jamiepine/voicebox — local-first voice studio)

- NOT a model: Tauri app + FastAPI backend orchestrating 7 TTS engines + Whisper STT + local Qwen3 LLM. MIT, Spacedrive Technology Inc.
- Linux: NO prebuilt binaries → build from source. `sudo pacman -S libayatana-appindicator patchelf just` + Bun (`curl -fsSL https://bun.sh/install | bash`). Project uses Bun, NOT Node.
- `just setup` → `just dev-web` (backend :17493 + web :1420) | `just dev` (Tauri desktop) | `just dev-backend` (API only).
- PITFALL (hit in 2026-08): justfile resolves python as `python3.12 || python3.13 || python3`. On a box with only 3.14/3.11 it picks 3.14 and `kokoro>=0.9.4` fails (Requires-Python >=3.10,<3.13). Fix: `sudo pacman -S python312; rm -rf backend/venv; just setup` OR pre-create `backend/venv` with python3.11 (justfile respects an existing venv).
- chatterbox-tts and hume-tada are installed `--no-deps` INTENTIONALLY (they pin torch to incompatible versions) — do not "fix".
- Health: `curl http://127.0.0.1:17493/health` → model_loaded, model_size, backend_variant. API docs :17493/docs. MCP at /mcp. Models auto-download on first use to ~/.cache/huggingface (~7.8GB for the full set).
- Engine table, pitfalls, runtime details: references/voicebox.md

## Workflow notes (user preferences)

- User runs installs MANUALLY to learn → give exact commands + the WHY (what each step does), don't execute everything for him. Diagnose the environment first (python versions, GPU, disk) before recommending a path.
- On this laptop, always install torch via `--index-url https://download.pytorch.org/whl/cpu` (no GPU).
- Compare against what VibeVoice does well that Voicebox doesn't: long multi-speaker conversation in one pass (up to 90 min, 4 voices). Voicebox's strength: speed, cloning, MCP/API integration, 23 languages.
