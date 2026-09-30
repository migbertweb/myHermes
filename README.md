# myHermes

Configuración personal de **Hermes Agent** — dotfiles, skills, perfiles y automatizaciones para DevOps, MLOps y producción de contenido tech.

## Stack

- **SO:** CachyOS (Arch) | Hyprland | DMS (DankMaterialShell)
- **Runtime:** Hermes Agent | Plugin Mnemosyne | Obsidian Second Brain
- **Editor:** Neovim / VS Code
- **Media:** FFmpeg, yt-dlp, HyperFrames, Remotion
- **Infra:** Docker, Dokploy, Kubernetes, CI/CD
- **IA Local:** llama.cpp, Ollama, modelos GGUF

## Estructura

```
├── config.yaml              # Config principal (proveedores, MCP, agentes)
├── SOUL.md                  # Instrucciones del agente (Viernes)
├── .gitignore               # Ignora runtime, caches, DBs, secretos
├── .env                     # Variables de entorno (NO committear)
├── profiles/                # Perfiles de agente (coder-back, coder-front, devops-chief, qualifier)
├── skills/                  # 130+ skills (DevOps, ML, UI, Video, Research, etc.)
├── cron/                    # Jobs programados + outputs
├── mnemosyne/               # Memoria persistente (config + datos)
├── scripts/                 # Utilidades CLI
├── agenda/                  # Sistema de tareas/notificaciones
├── kanban/                  # Tablero de tareas (SQLite)
└── plugins/                 # mnemosyne, mnemosyne-dashboard, ponytail, superpowers
```

## Perfiles activos

| Perfil | Uso |
|--------|-----|
| `coder-back` | Backend, APIs, DB, infra |
| `coder-front` | Frontend, React, UI, accesibilidad |
| `devops-chief` | CI/CD, Kubernetes, Docker, monitoring |
| `qualifier` | Code review, security, quality gates |

## Secrets

Todas las credenciales viven en `.env` (gitignored) y se referencian en `config.yaml` como `${VAR_NAME}`. Ejemplos:

```bash
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...
YOUTUBE_ACCESS_TOKEN=...
```

## Uso rápido

```bash
# Clonar
git clone git@github.com:migbertweb/myHermes.git ~/.hermes

# Instalar Hermes (ver docs oficiales)
# Luego copiar .env.example → .env y rellenar secrets

# Iniciar gateway
hermes gateway start

# Lanzar agente
hermes
```

## Skills destacadas

- `devops/docker-management` — contenedores, imágenes, volúmenes
- `devops/hermes-*` — gestión de Hermes (config, MCP, perfiles, skills)
- `mlops/llama-cpp` — inferencia local GGUF
- `media/video-editor-studio` — pipeline FFmpeg/Whisper
- `creative/hyperframes` — video generativo 9:16
- `software-development/github` — PRs, issues, reviews via gh CLI

## Licencia

Uso personal. Skills bajo sus respectivas licencias (MIT/Apache-2.0 mayormente).