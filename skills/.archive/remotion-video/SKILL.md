---
name: remotion-video
description: Use when creating React-based videos with Remotion (bun).
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [video, remotion, react, render, creative]
    related_skills: [general-video, hyperframes, manim-video]
---

# Remotion Video

Remotion = videos programáticos con React (HTML/CSS/JS + React → MP4). Alternativa/complemento a HyperFrames cuando el proyecto pide React, composiciones con estado o el Studio interactivo. Remotion 4.x es gratis para equipos ≤3.

## When to use
- Crear un video/animación programática en React (no HTML/CSS puro como HyperFrames).
- Trabajar en `~/proyectos/remotion-test` u otro proyecto Remotion.
- Renderizar composiciones a MP4/still desde CLI.

## Setup (ya hecho en la laptop, verificar si falta)
1. Skills de agente (opcional, para agentes de IA):
   ```bash
   npx -y skills add remotion-dev/skills
   ```
   Instala 12 skills `remotion-*` en `~/.agents/skills/` con symlink automático a Hermes Agent (visibles en skills_list tras reiniciar sesión). Ver `references/remotion-agent-skills.md` para el detalle de cada uno.
2. Proyecto existente: `~/proyectos/remotion-test` (template hello-world, Remotion 4.0.509, bun).

## Crear un proyecto nuevo
```bash
cd ~/proyectos
bun create video <nombre> --hello-world --no-git --yes
cd <nombre> && bun install
```
Templates: `--hello-world` (demo con composiciones HelloWorld y OnlyLogo, 5s 1080p), `--blank`, `--next`, `--remix`, `--tailwind`, `--three`, etc.

## Verificar que el pipeline funciona
```bash
bunx remotion compositions          # lista composiciones; primer run baja Chrome Headless Shell (~92MB)
bunx remotion still <Composition> out/test.png --frame=75   # render rápido de un frame
```

## Render
```bash
bunx remotion render <Composition> out/video.mp4   # video completo
bunx remotion still <Composition> out/frame.png --frame=N
bun run dev                                        # Studio interactivo en navegador
```

## Pitfalls
- **`--template <nombre>` NO funciona con `--yes`**: el CLI rechaza la combinación con "A template must be specified when using --yes". La sintaxis correcta es el flag directo `--<nombre-template>` (ej: `--hello-world`), no `--template hello-world`.
- **WebM transparente roto en Remotion 4.0.509 + ffmpeg del sistema**: el canal alpha se pierde al codificar VP8/VP9/AV1 (salida `yuv420p`) aunque el encoder declare soporte `yuva420p` y se pasen `--codec=vp9 --pixel-format=yuva420p --image-format=png`. Verificado en ffmpeg n9.0.1 (CachyOS) y el empaquetado n7.1 de Remotion. SOLUCIÓN: render ProRes 4444 con alpha (`--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png` → verifica con `ffprobe ... pix_fmt=yuva444p12le`) o secuencia PNG (`ffmpeg -i x.mov -c:v png seq/frame_%04d.png`, pix_fmt rgba64be).
- **`remotion.config.ts` de este proyecto tiene `Config.setVideoImageFormat("jpeg")`**: el CLI `--image-format=png` NO lo sobreescribe (la config gana). Para renders con alpha hay que quitar esa línea de la config temporalmente o renderizar ProRes (que internamente usa PNG igual).
- El primer `remotion compositions`/render descarga Chrome Headless Shell automáticamente; puede tardar ~1 min. No es un error.
- DeprecationWarning de `module.register()` en Node 26 durante el bundle: inofensivo.
- `bunx remotion still` sin `--frame` usa el frame 0; pasar `--frame=N` para un punto medio de la animación.

## Links
- Docs: https://www.remotion.dev/docs
- Prompts oficiales: https://www.remotion.dev/prompts
- Código de los skills: https://github.com/remotion-dev/remotion/tree/main/packages/skills
