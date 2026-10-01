---
name: voice-audio-optimization
title: Voice Audio Optimization
description: Clean up voice recordings with ffmpeg/Audacity.
trigger: Use when the user needs to clean, level, or enhance a voice recording for a video project.
category: media
tags: [ffmpeg, audacity, audio, voice, cleaning, eq, compression, noise-reduction]
---

# Voice Audio Optimization

Diagnose → analyze → process → verify voice audio for video.

## Step 1: Diagnostics

```bash
ffprobe -hide_banner "input.mp3"
sox "input.mp3" -n stats
ffmpeg -i "input.mp3" -af "volumedetect" -f null /dev/null 2>&1 | grep -E "(mean|max|histogram)"
sox "input.mp3" -n spectrogram -o /tmp/spectrogram.png
```

Key metrics: RMS level (target -16 dB), peak level (≤ -1 dB), crest factor, DC offset (~0), noise floor.

## Step 2: Spectrogram via vision_analyze

Analyze for: noise floor, mains hum (50/60 Hz), sibilance (6-8 kHz), rumble (<100 Hz), clipping, impulse streaks.

## Step 3: FFmpeg Filter Chain

Adjust based on diagnosis:

```
highpass=f=80,
adeclick=threshold=10:window=30:burst=3,
afftdn=nf=-25,
equalizer=f=150:t=o:w=0.5:g=-4,
equalizer=f=800:t=o:w=1:g=2.5,
equalizer=f=2500:t=o:w=1:g=3.5,
equalizer=f=6000:t=o:w=1:g=2,
acompressor=threshold=-20dB:ratio=3:attack=5:release=200:makeup=2dB,
loudnorm=I=-16:TP=-1.5:LRA=7
```

See `references/ffmpeg-filter-chain.md` for per-filter tuning, platform loudness targets, and when to skip filters.

Output: WAV 44100 Hz 16-bit mono.

```bash
ffmpeg -i input.mp3 -af "<chain>" -ar 44100 -sample_fmt s16p output.wav
```

## Step 4: Verify

```bash
sox "output.wav" -n stats
```

RMS should be higher, crest factor lower, peak < -1 dB.

## Audacity Equivalent

1. Noise reduction (print from silence → 18-24 dB)
2. High-pass 80 Hz
3. Click removal
4. EQ (same frequencies)
5. Compressor (-20 dB, 3:1, 5ms/200ms)
6. Limiter (-1 dB)
7. Export WAV

## Pitfalls

- `adeclick` threshold is 1-100 (NOT 0-1).
- `equalizer` uses `t=o` for octave width, not `width-type`.
- `arnndn` needs a compiled model file — use `afftdn` as model-free fallback.
- Output WAV, never lossy for intermediate steps.
