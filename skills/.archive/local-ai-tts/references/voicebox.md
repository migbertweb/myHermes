# Voicebox (jamiepine/voicebox) — verificación 2026-08-10

Repo: https://github.com/jamiepine/voicebox (MIT, Spacedrive Technology Inc). INSTALADO y VERIFICADO 2026-08-10 (v0.5.0) en `~/proyectos/ai-agents/voice`. Página oficial de instalación Linux: https://voicebox.sh/linux-install

## Qué es
Estudio de voz local-first (alternativa open-source a ElevenLabs + WisprFlow): app Tauri (Rust) + React + backend FastAPI Python. NO es un modelo único — orquesta 7 motores TTS. REST API + servidor MCP (`voicebox.speak`, `voicebox.transcribe`, `voicebox.list_captures`, `voicebox.list_profiles`). Whisper STT + dictado global (macOS principalmente), LLM local Qwen3 0.6-4B para personalidades, efectos pedalboard, editor multi-track, chunking hasta 50k chars.

## Motores TTS (negrita = relevante para CPU)
| Motor | Tamaño | Notas |
|---|---|---|
| **Kokoro** | **82M** | tiny, CPU rápida, 50 voces preset, 8 idiomas |
| **Chatterbox Turbo** | **350M** | rápido, tags paralingüísticos `[laugh]` `[sigh]` |
| Qwen3-TTS | 0.6B / 1.7B | clonación multi-idioma, instrucciones de delivery ("susurra") |
| LuxTTS | ~1GB VRAM | 48kHz, reclama 150x realtime en CPU (no verificado) |
| Chatterbox Multilingual | — | 23 idiomas (el más amplio) |
| TADA (HumeAI) | 1B / 3B | 700s+ audio coherente |
| Qwen CustomVoice | — | 9 voces preset, sin audio de referencia |

## Instalación Linux (sin binarios prebuilt — build source o Docker)
Prereqs Arch/CachyOS: git, rust, just, bun, deps Tauri (`webkit2gtk-4.1 libayatana-appindicator librsvg patchelf pkg-config`)
```bash
git clone https://github.com/jamiepine/voicebox.git && cd voicebox
just setup    # venv py3.11/3.12 + pip requirements + bun install
just dev      # app Tauri completa (compila Rust, primer build lento)
just dev-web  # backend + web UI en localhost:1420 — SIN build Rust, ideal para aprender
just dev-backend  # solo API
```
- API: `127.0.0.1:17493`, docs en `/docs`
- Modelos se autodescargan en primer uso (Whisper, Qwen3-TTS ~2-4GB)
- Docker: `docker compose up` (host 17600→17493, build CPU default, overlay ROCm existe)
- El justfile detecta GPU: NVIDIA→cu128, AMD kfd→rocm, ninguno→torch CPU. `chatterbox-tts` y `hume-tada` se instalan `--no-deps` deliberadamente (pins torch conflictivos) — no "arreglar".

## Estado del usuario (chequeado 2026-08-10)
✅ TODO presente: git, rustc/cargo 1.94, just, bun 1.3.14, node 26, python3.11.15 + 3.12.13 + 3.14.6, webkit2gtk-4.1, librsvg, pkg-config, libayatana-appindicator, patchelf, libsoup3. Disco ~31G libres. Ya NO hace falta instalar prereqs.

## Instalación verificada (2026-08-10)
- Clonar directo en carpeta vacía: `git clone https://github.com/jamiepine/voicebox.git .` (funciona).
- `just setup` tarda ~6+ min (torch CPU + requirements + Qwen3-TTS desde git + bun install ~815 paquetes) → background con notify_on_complete, no foreground.
- justfile resuelve `python3.12 || python3.13 || python3`: con python3.12 presente elige 3.12 y el setup pasa limpio — el pitfall del 3.14 solo ocurre en máquinas sin 3.12/3.13.
- Verificación sin Tauri: `backend/venv/bin/uvicorn backend.main:app --port 17493` → `curl -s 127.0.0.1:17493/health` → `{"status":"healthy",...,"backend_variant":"cpu"}` y `/docs` → 200 → kill.
- Log de arranque: "Voicebox v0.5.0 starting up"; DB en `data/voicebox.db`; modelo cache `~/.cache/huggingface/hub`; "MCP: mounted at /mcp" + StreamableHTTP session manager.
- `just dev` corre además `bun run setup:dev` (sidecar placeholder, receta `_ensure-sidecar`) antes de compilar Tauri — automático, no manual.
- UI web (`just dev-web`) en :1420; backend :17493; para probar rápido: dev-web (sin build Rust).
