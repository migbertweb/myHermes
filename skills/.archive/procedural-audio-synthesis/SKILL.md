---
name: procedural-audio-synthesis
description: Synthesize music/SFX with numpy when a video lacks a track.
---

# Procedural Audio Synthesis (numpy → WAV → ffmpeg)

Cuando un video (HyperFrames, FLUX 3, edición de reel) necesita música o SFX y no hay pista: sintetizar desde cero con numpy y muxear. Cero dependencias de modelos/APIs, determinista, offline, sin copyright.

## Cuándo usar
- Reel/demo sin audio que necesita fondo musical
- SFX específicos (láser pew, whoosh, riser, impact) sincronizados a tiempos exactos del video
- Alternativa a heartmula (Suno) / audiocraft (MusicGen) cuando se quiere control total y sin coste

## Pipeline
1. Sintetizar WAV 44.1 kHz estéreo con numpy (ver `scripts/synth_epic_track.py` como base conocida-buena)
2. Normalizar el pico a ~0.85–0.88 tras mezclar TODAS las capas (no por capa)
3. Muxear sin re-encode de video:
```bash
ffmpeg -y -i video.mp4 -i track.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart video-audio.mp4
```
4. Verificar: `ffprobe -v error -show_entries format=duration -show_entries stream=codec_type` (duración = esperada, streams video+audio)

## Recetas de síntesis (numpy, SR=44100)
- `note_f(freq, t0, dur, gain, kind)` — sintetiza una nota:
  - `string` (cuerdas): saw suave + armónicos 2-4 + chorus, vibrato `freq*(1+v*sin(2π*5.5*t))`
  - `brass` (metales): armónicos impares fuertes (square-ish), ataque rápido
  - `bass`: sine + 2º armónico
  - `timpani`: pitch drop 95→52 Hz con `exp(-t*9)`, env decay
- `chord(freqs, ...)` — suma de `note_f`
- **kick**: sine barrido 52→34 Hz + click de ruido, env `exp(-t*18)`
- **hat**: ruido * `exp(-t*55)`, corto
- **riser**: ruido + sine sweep 200→4200 Hz, env `(t/dur)**2.5` (sube al final)
- **whoosh**: ruido pasa-bajos con kernel fijo (~24 taps) + sweep 300→2900 Hz, env `sin²`
- **pew** (bláster): barrido 900→180 Hz exp + click — SFX láser estilo Star Wars
- **impact** (hit orquestal): bajo 55 Hz + timpani + ráfaga de ruido

## Composición musical (épica / estilo Star Wars)
- Re menor épico: progresión **Dm–Bb–F–A** (i–VI–III–V), 112 BPM, `bar = 60/BPM*4` ≈ 2.14 s
- **Fanfarria de metales**: motivo heroico ORIGINAL — nunca copiar el tema de John Williams (copyright)
- Cuerdas staccato: arpegios del acorde en 8vos (`e*BEAT/2`)
- Timpani en beats 1 y 3 de cada compás
- Sección B lírica: acordes largos (attack 0.3–0.5) + melodía alta con vibrato
- Final: acorde sostenido + impact + bajo
- **Estéreo**: ensanche con `np.roll(mix, int(0.014-0.016*SR))` en el canal derecho
- Fade in/out global de ~0.6–0.8 s

## Pitfalls (todos encontrados en producción)
1. **Buffer overflow**: la última nota/arpegio se sale de `N` → guard `if i0 >= N: return out` en `note_f` y truncar siempre `end = min(i0+n, N)`.
2. **Walrus en slice no funciona**: `out[i0 := int(t0*SR): i0+n]` rompe lint/sintaxis → usar `i0` y `end` explícitos.
3. **Convolución con ventana variable falla**: `window = int(8 + 120*(tt/dur)**2)` → `TypeError: only 0-dimensional arrays...`. Usar kernel fijo.
4. **Constantes de nota faltantes**: definir TODAS las notas usadas (Bb2, C3, E3, G3, A2...) antes de las secciones — NameError típico al extender la progresión.
5. Mux con `-c:v copy` preserva calidad y es instantáneo (60 s de video: ~2 s de mux).
6. **Índice negativo por jitter en t0=0**: si una nota empieza en `t0=0` y se le suma un jitter aleatorio negativo (p.ej. `rng.uniform(-0.04, 0.04)` para timing humano), `i0 = int(t0*SR)` queda negativo → numpy envuelve el slice (`out[-1323:...]` → start > stop → shape (0,)) y el broadcast revienta con `ValueError: could not broadcast input array from shape (n,) into shape (0,)`. Fix: **`i0 = max(0, int(t0 * SR))`** además del guard `if i0 >= N`. El guard de overflow NO cubre el caso negativo.

## Verificación
- `ffprobe` duración = esperada (ej. 60.0 s)
- Pico < 1.0 tras normalizar
- Al entregar: mencionar que la pista es original (libre de copyright) — útil para clientes que piden música

## Related
- `scripts/synth_epic_track.py` — generador completo conocido-bueno (pista épica 60 s + SFX pew/whoosh) con todas las correcciones aplicadas.
- HyperFrames (`hyperframes-*` skills) para el lado video; el audio se muxea después del render.
