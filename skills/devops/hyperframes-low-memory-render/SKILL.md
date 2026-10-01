---
name: hyperframes-low-memory-render
description: Render HyperFrames despite ffmpeg/Chrome fails on low-RAM.
platforms: [linux]
metadata:
  hermes:
    tags: [hyperframes, video, low-memory, render, ffmpeg]
    category: devops
    requires_toolsets: [terminal]
---

# HyperFrames on low-RAM server

## Context
serverhogar (192.168.1.8) has 3.3GB RAM total, ~2.2-2.6GB consumed by services (omniroute ~494MB, hermes gateway, syncthing 74% CPU, *arr stack, transmission, dockerd). Only ~0.6-1.1GB available. HyperFrames renders Chrome (~260MB) + ffmpeg simultaneously → spawn failures under memory pressure.

## The failure signature
`hyperframes render` exits fast (seconds) with either:
- `✗ FFmpeg cannot start` / `Failed to run "/usr/bin/ffmpeg" -version.` — an INTERMITTENT spawn check that dies when RAM is squeezed. NOT an ffmpeg install problem — `ffmpeg -version` and `npx hyperframes doctor` both pass.
- `Protocol error (Page.captureScreenshot): Target closed` — Chrome got OOM-killed mid-render.

## Non-negotiable render flags (serverhogar)
```bash
npx hyperframes render --quality draft --output out.mp4 --low-memory-mode -w 1
```
- `--low-memory-mode` — auto-pins 1 worker + screenshot capture (auto-detected ≤8GB but force it)
- `-w 1` — single Chrome worker. Never use default auto-workers here.
- AVOID `--no-page-side-compositing` (slower, didn't help).

## Must render in background
Renders take ~1 min per second of video (16s→~5min draft, 24s→~13min). Use terminal `background=true` + `notify_on_complete=true`. Never foreground.

## Retry loop (unblocker)
The ffmpeg check failure is transient — retrying usually succeeds once load/swap settles. Use this instead of a single render call:
```bash
for i in 1 2 3 4 5 6; do
  npx hyperframes render --quality draft -o out.mp4 --low-memory-mode -w 1 >> render.log 2>&1 \
    && break
  echo "retry $i — waiting 20s"; sleep 20
done
```

## If retries keep failing (persistent OOM)
1. Check `free -h` — if available < 0.8GB, RAM is the blocker.
2. Ask the user before stopping ANY service (their rule: diagnose first, never fix without approval). Biggest consumers: omniroute 494MB, hermes gateway 234MB, syncthing 109MB(+74% CPU), *arr stack.
3. Recommended pause candidates (least disruption): syncthing, transmission, lidarr.
4. Alternative: schedule render at night when services idle (cron).

## More reliable than the vision-model: verify renders by pixel
`vision_analyze` was unreliable here (returned 503/400 errors, and once described the ORIGINAL input image instead of the rendered frame). Verify objectively with ffmpeg signalstats:
```bash
for t in 2 4 6 8 10 12 14; do
  echo -n "t=${t}s YMAX="; ffmpeg -ss $t -i out.mp4 -vf "signalstats,metadata=print:file=-" -frames:v 1 -f null - 2>&1 | grep YMAX | tail -1 | sed 's/.*YMAX=//' | tr -d '\r'
done
```
- All black frames → YMAX≈16-25 everywhere.
- Healthy content → YMAX 220-255.
Also cross-check by region with PIL (colored-pixel fraction per column) to confirm bars/donuts/icons regions are populated.

## Pitfall: `class="clip"` batch edit destroys CSS classes
When bulk-adding `class="clip"` to timed elements via regex, inserting `class="clip"` first while `class="litem"` exists later produces a duplicate class attribute. The framework re-serializes keeping only the FIRST → `.litem` etc vanish → GSAP logs `GSAP target .litem not found` and elements render invisible (bars height lost, donut colors lost).
- FIX: write each timed element with BOTH classes in one attribute: `class="litem clip"` and give every timed clip a UNIQUE id. This also eliminates studio_missing_editable_id warnings → "0 errors, 0 warnings".
- Confirm in render log: `grep -c "GSAP target.*not found" render.log` should be 0.

## Verify before delivery
1. `grep -c 'GSAP target.*not found' render.log` → 0
2. `ls -lh out.mp4` non-zero, size grows with content (empty black = ~18KB; real content 1080p = 0.5-1MB+)
3. signalstats YMAX across timestamps
4. `ffprobe -show_entries format=duration` == data-duration