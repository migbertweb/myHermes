# Voicebox (jamiepine/voicebox) — voice studio details

Local-first ElevenLabs + WisprFlow alternative. Tauri (Rust) + FastAPI (Python) + React. MIT, Spacedrive Technology Inc. NOT a model: orchestrates 7 TTS engines + Whisper STT + local Qwen3 LLM. site voicebox.sh, API on :17493, MCP at /mcp.

## 7 TTS engines

| Engine | Languages | Strengths |
|---|---|---|
| Qwen3-TTS (0.6B/1.7B) | 10 | quality multilingual cloning, delivery instructions ("speak slowly", "whisper") |
| Qwen CustomVoice | 10 | 9 preset voices, NL delivery control, no ref audio needed |
| LuxTTS | English | ~1GB VRAM, 48kHz output, claims 150x realtime on CPU (unverified) |
| Chatterbox Multilingual | 23 | broadest coverage: ar, da, fi, el, he, hi, ms, no, pl, sw, sv, tr, ... |
| Chatterbox Turbo | English | 350M fast; ONLY engine that interprets paralinguistic tags `[laugh]` `[sigh]` `[gasp]` etc. Others read them literally |
| TADA (1B/3B) | 10 | HumeAI speech-LM, 700s+ coherent audio |
| Kokoro | 8-9 | 50 preset voices, 82M tiny, fast CPU. 0.9.4 ALIASES: en-us, en-gb, es, fr-fr, hi, it, pt-br, ja, zh |

## Install (Linux — no prebuilt binaries)

```bash
sudo pacman -S libayatana-appindicator patchelf just   # Tauri deps + task runner
curl -fsSL https://bun.sh/install | bash               # project uses Bun, NOT Node
git clone https://github.com/jamiepine/voicebox.git && cd voicebox
just setup      # backend/venv + pip deps + bun install
just dev-web    # backend :17493 + Vite web :1420 (no Rust build — fastest)
# just dev (Tauri desktop) | just dev-backend (API only) | just build (production)
```

Verified env (CachyOS 2026-08): git, Rust 1.94, webkit2gtk-4.1, librsvg, pkg-config already present; needed libayatana-appindicator, patchelf, just, bun.

## Pitfalls

1. **Python resolution** (hit 2026-08): justfile picks `python3.12 || python3.13 || python3`. Box with only 3.14/3.11 → picks 3.14 → `kokoro>=0.9.4` fails (Requires-Python >=3.10,<3.13). Fix: `sudo pacman -S python312; rm -rf backend/venv; just setup`, OR pre-create `backend/venv` with `python3.11 -m venv backend/venv` (justfile respects existing venv).
2. `chatterbox-tts` and `hume-tada` installed `--no-deps` INTENTIONALLY (pin torch==2.6 / torch<2.8 incompatible with project torch) — do not "fix".
3. No NVIDIA/AMD detected → plain CPU torch (no CUDA/ROCm index). Expected.
4. First generate downloads models from HF to ~/.cache/huggingface (full set ~7.8GB): Kokoro-82M, Qwen3-TTS 0.6B/1.7B, chatterbox, LuxTTS, whisper, Qwen2.5-1.5B (local LLM).
5. `--port` arg in gradio-style scripts may be ignored if server_port commented out — check code.

## Runtime verification

```bash
curl http://127.0.0.1:17493/health
# {"status":"healthy","model_loaded":true,"model_size":"0.6B","gpu_available":false,"backend_variant":"cpu",...}
curl http://127.0.0.1:17493/profiles   # voice profiles (cloned presets)
curl http://127.0.0.1:17493/docs       # Swagger: /generate /speak /transcribe /profiles
```

- DB: data/voicebox.db (profiles, generations). Data dir: data/.
- Example profile seen: name `voz-personal`, language `es`, voice_type `cloned`, default_engine `qwen`, 1 sample.
- MCP tools: voicebox.speak, voicebox.transcribe, voicebox.list_captures, voicebox.list_profiles. REST + stdio shim.
- Features: auto-chunking + crossfade (up to 50k chars), post-effects (pedalboard), Stories multi-track editor, voice personalities (local Qwen3 LLM rewrite), global dictation hotkey (macOS-first).

## CPU engine pick (no GPU)

- Default: Kokoro (instant) — preset voices only.
- Spanish + cloning: Qwen3-TTS 0.6B (best CPU balance). 1.7B slow on CPU.
- EN + emotion tags: Chatterbox Turbo.
- Avoid on CPU: TADA 3B, Chatterbox Multilingual heavy loads, Qwen3-TTS 1.7B.
- Spanish in Kokoro 0.9.4: lang code `es` EXISTS in ALIASES, but the es_* voicepack must actually be downloaded — if UI shows no es voice, pack missing.
