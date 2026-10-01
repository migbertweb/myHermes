---
name: remotion-video-production
description: Use when making Remotion videos (promos, logo intros, CTA).
author: Migbert (curator-managed)
license: MIT
metadata:
  hermes:
    tags: [remotion, video, promos, transitions, react]
    related_skills: [remotion-best-practices, remotion-markup, remotion-create]
version: 1.0.0
---

# Remotion Video Production

Agent-side workflow for building programmatic videos with Remotion (React → Chrome-headless render). Complements the externally-maintained `remotion-*` skills (remotion-create, remotion-markup, transitions refs) — load those for framework best practices; this skill carries the workflow, frame math, and pitfalls learned in practice. DO NOT edit the remotion-* skills (external repo); add session learnings here instead.

## When to use
- User asks for a video from images/logos with animated entrances, scene transitions, and a CTA outro (like/subscribe, follow), e.g. promos, channel intros.

## Setup
- Scaffold: `bun create video <name> --hello-world --no-git --yes`. The template name IS the flag (`--hello-world`, `--blank`); `--template X` is REJECTED when `--yes` is set (works only in interactive mode).
- Deps: `bun install`; add packages version-aligned with `bunx remotion add @remotion/transitions`.
- Assets: copy to `public/`, reference via `staticFile("name.jpg")`.
- First bundle auto-downloads Chrome Headless Shell (~90MB) — a long download is normal, not an error.
- Agent skills for Remotion: `npx skills add remotion-dev/skills` → installs to `~/.agents/skills/` and symlinks into Hermes skills.

## Multi-scene structure
- One folder per video (e.g. `src/BrandVideo/`): master component with `<TransitionSeries>`, each scene its own file/component (`SceneA.tsx`, ...).
- Register BOTH the master and each individual scene as `<Composition>` in Root.tsx — per-scene ids let the user open/tune each in Studio and jump from sequences.

## Frame math with transitions (PITFALL)
- Total duration = Σ sequence durations − Σ transition durations (transitions overlap both neighbors).
- Scene N starts at frame: Σ(sequences before N) − Σ(transitions before N). Compute this BEFORE choosing still frames — picking "midpoint of scene duration" lands in the WRONG scene.
- Worked example (seqs 150/150/150/210, 3 transitions × 20f, total 600): scenes start at **0 / 130 / 260 / 390**.
- Verify scene starts with one early still before trusting any frame number.

## Transitions API gotchas
- Read the installed signatures first: `node_modules/@remotion/transitions/dist/presentations/*.d.ts`.
- `clockWipe` REQUIRES `{width, height}` (use `useVideoConfig()`); `flip({direction, perspective})`; `slide({direction})`; `crossZoom({strength})`; `fade()`.
- Import paths: `@remotion/transitions/flip`, `/clock-wipe`, `/fade`, `/slide`; `linearTiming`/`springTiming` from `@remotion/transitions`.
- A varied, "llamativo" sequence that works: flip → clockWipe → fade.

## Entrance & CTA patterns
- Logo entrances: spring pop + rotate + halo (light bg), slide + flash + light sweep (dark bg), 3D flip + pulsing ring + particles. Drive everything with `useCurrentFrame()` + `interpolate()`/`spring()` — CSS transitions/animations do NOT render in Remotion.
- 3D flip: `transform: perspective(1200px) rotateY(...)`; use `scale`/`translate`/`rotate` props elsewhere per remotion-markup.
- CTA outro (like/subscribe): panel slides up with spring; inline SVG YouTube logo + thumbs-up; like pulse (spring twice); red SUSCRIBIRSE button with bell; confetti + final white flash. Full pattern: `references/cta-outro-pattern.md`. Reusable master skeleton: `templates/brand-video-master.tsx`.

## Verification workflow (do this before full render)
1. `bunx tsc --noEmit` — typecheck first.
2. Render one still per scene at the correct start/mid frame, small: `bunx remotion still <id> out/check.png --frame=N --scale=0.5` (0.5 keeps files small/fast and vision-friendly).
3. Inspect each still with vision_analyze before proceeding.
4. Only then render: `bunx remotion render <id> out/video.mp4` in background with notify_on_complete (~600 frames takes minutes). Verify with ffprobe (duration ≈ fps math, codec h264, resolution).

## Studio — lanzar SIEMPRE con NODE_ENV=development (CRITICAL)
- The Hermes terminal backend injects `NODE_ENV=production` into every agent-spawned process. Real source (traced in code): `hermes_cli/main.py:2315` — `env.setdefault("NODE_ENV", "development" if tui_dev else "production")` when launching the TUI. NOT in ~/.zshrc, /etc/environment, profile.d or systemd (the `TERMINAL_*` container vars are a separate, unrelated set). With it, Remotion Studio shows a BLANK page + console `Uncaught ReferenceError: $RefreshSig$ is not defined`.
- Mechanism: react-refresh/runtime.js picks its build by `process.env.NODE_ENV`; the production build THROWS on purpose ("React Refresh runtime should not be included in the production bundle"), which kills the fast-refresh entry so `$RefreshSig$` is never defined and the whole Studio bundle fails.
- Fix (from Hermes sessions):
  ```bash
  cd <proyecto>
  NODE_ENV=development ./node_modules/.bin/remotion studio --no-open
  ```
- Do NOT use `remotionb` / `bun run dev` for the Studio — bun inherits NODE_ENV=production more often. The user's own terminal is fine (no NODE_ENV export); the problem only bites when Hermes launches it.
- **Permanent fix:** `echo 'NODE_ENV=development' >> ~/.hermes/.env` — `load_hermes_dotenv()` runs at import time (hermes_cli/main.py line ~700), i.e. BEFORE the `setdefault` at line 2315, and both use setdefault semantics, so the .env value survives and every future agent-spawned process gets development. Takes effect on the NEXT Hermes session. Side effect: agent-spawned npm/node processes get NODE_ENV=development (fine on the dev laptop; do NOT do this on the server where deploys rely on production).
- Before restarting the Studio: `pkill -f "remotion studio"`, then confirm port free with `ss -tlnp | grep 3000` (killing the wrapper leaves the node child zombie on the port → "Already running on port 3000").
- Debug a blank Studio without the user's browser: Playwright's Chrome headless shell:
  `~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr --v=0 --virtual-time-budget=15000 --dump-dom "http://localhost:3000/BrandVideo" 2>&1 | grep -iE "uncaught|error"`
- Red herrings that do NOT fix it: cache clean (node_modules/.remotion), `--rspack`/`--experimental-rspack` (all bundles fail identically), node vs bun binary, version mismatch (all @remotion packages were 4.0.509). Full diagnosis transcript: `references/studio-blank-page-debug.md`.
- CLI renders are unaffected — `remotion render` works even when the Studio is broken.

## Pitfalls
- vision_analyze returns HTTP 400 on large JPEGs (payload too big after auto-resize). Fix: downscale first — `ffmpeg -y -i in.jpg -vf scale=400:-1 -q:v 8 /tmp/out.jpg`.
- Name every asset by brand/content in the plan immediately ("logo1.jpg → Hermes Agent") so the user can confirm the mapping before you build — avoids mid-task corrections.
- Final scene with an image that already contains text: reveal it (clip-path inset sweep + light edge) instead of overlaying duplicate text; add a blurred dark copy of the same image as background for a premium look.
