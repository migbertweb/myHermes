# FFmpeg Filter Chain Reference

Canonical filter chain for voice audio cleanup, ordered by signal flow.

## Full Chain (Copy-Paste Ready)

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

## Command

```bash
ffmpeg -y -i "voz.mp3" \
  -af "<chain>" \
  -ar 44100 -sample_fmt s16p "voz_optimizado.wav"
```

## Filter Reference

| Filter | Params | Purpose | Adjust If... |
|--------|--------|---------|-------------|
| `highpass` | `f=80` | Cut rumble/sub-bass | Male voice → 60-70 Hz; female → 80-100 Hz; heavy rumble → 120 Hz |
| `adeclick` | `threshold=10:window=30:burst=3` | Remove impulse/clicks | More clicks → threshold=15-20; artifacts → threshold=5-8 |
| `afftdn` | `nf=-25` | FFT broadband noise reduction | Cleaner recording → nf=-35; noisier → nf=-20; check noise floor from sox/ffmpeg |
| `equalizer` | `f=150:t=o:w=0.5:g=-4` | Cut muddiness | Boomy recording → g=-6; thin → g=-2 or skip |
| `equalizer` | `f=800:t=o:w=1:g=2.5` | Add warmth/body | Deeper voice → g=1.5; thin voice → g=3.5 |
| `equalizer` | `f=2500:t=o:w=1:g=3.5` | Presence/intelligibility | Sibilance issues → g=2.0; muffled → g=4.5 |
| `equalizer` | `f=6000:t=o:w=1:g=2` | Air/clarity | Harsh → g=1; dull → g=3 |
| `acompressor` | `threshold=-20dB:ratio=3:attack=5:release=200:makeup=2dB` | Level dynamics | Wide volume swings → ratio=4; too squashed → ratio=2.5 or threshold=-18 |
| `loudnorm` | `I=-16:TP=-1.5:LRA=7` | YouTube loudness standard | Netflix → I=-27; Spotify → I=-14; podcast → I=-16 |

## Per-Filter Tuning Notes

### adeclick
- **threshold**: 1-100 scale. 2 = subtle, 10-15 = moderate, 25+ = aggressive (risk of artifacts)
- **window**: 10-100. Higher = larger analysis window, better for sparse clicks
- **burst**: 0-10. Fuses nearby clicks into one event

### afftdn
- **nf**: Noise floor estimate in dB. Use sox stats RMS Tr dB as starting point
- Can add `:om=1` for output mode (1 = reduce only noise, not voice)
- For changing noise profiles, consider `afftdn=nf=-25:nt=2` (noise tracking enabled)

### equalizer
- **f**: Center frequency in Hz
- **t**: Width type. `o` = octave width, `q` = Q-factor, `h` = Hz width
- **w**: Width value. 1 octave is a good general-purpose width
- **g**: Gain in dB. Negative = cut, positive = boost

### loudnorm
- **I**: Integrated loudness target (LUFS)
- **TP**: True peak limit (dBTP)
- **LRA**: Loudness range (LU). Lower = more uniform

## When to Skip Filters

- **No clicks/impulses** → remove `adeclick` entirely
- **Clean recording** → reduce `afftdn` to `nf=-35` or skip
- **Recording already compressed** → reduce or skip `acompressor`
- **Voice sounds unnatural after EQ** → reduce gains by 50% or skip presence boost
