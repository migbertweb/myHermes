#!/usr/bin/env python3
"""Pista épica estilo Star Wars (original, Re menor) + SFX láser/whoosh. 60s.
Conocido-bueno: todas las correcciones de pitfalls aplicadas.
Uso: python3 synth_epic_track.py [output.wav]
"""
import sys
import numpy as np
import wave

SR = 44100
DUR = 60.0
N = int(SR * DUR)
t = np.arange(N) / SR
BPM = 112.0
BEAT = 60.0 / BPM  # 0.5357s


def note_f(freq, t0, dur, gain=0.25, kind="string", vibrato=0.0, attack=0.05):
    """Sintetiza una nota. kind: string|brass|bass|timpani"""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    atk = np.minimum(tt / attack, 1.0)
    rel = np.minimum((dur - tt) / 0.15, 1.0).clip(0, 1)
    env = atk * rel
    vib = 1.0 + vibrato * np.sin(2 * np.pi * 5.5 * tt)
    ph = 2 * np.pi * freq * np.cumsum(vib) / SR
    if kind == "string":
        osc = (0.55 * np.sin(ph) + 0.25 * np.sin(2 * ph) +
               0.12 * np.sin(3 * ph) + 0.08 * np.sin(4 * ph))
        osc *= (0.8 + 0.2 * np.sin(2 * np.pi * 0.4 * tt + freq))
    elif kind == "brass":
        osc = (0.5 * np.sin(ph) + 0.32 * np.sin(3 * ph) + 0.18 * np.sin(5 * ph))
        osc *= (0.85 + 0.15 * np.sin(2 * np.pi * 6.0 * tt))
    elif kind == "bass":
        osc = 0.7 * np.sin(ph) + 0.3 * np.sin(2 * ph)
    elif kind == "timpani":
        pd = 95 * np.exp(-tt * 9) + 52
        ph2 = 2 * np.pi * np.cumsum(pd) / SR
        osc = np.sin(ph2) * np.exp(-tt * 3.5)
        env = np.ones_like(tt)
    else:
        osc = np.sin(ph)
    out = np.zeros(N)
    i0 = int(t0 * SR)
    if i0 >= N:  # PITFALL 1: guard de buffer overflow
        return out
    end = min(i0 + n, N)
    out[i0:end] = (osc * env * gain)[: end - i0]
    return out


def chord(freqs, t0, dur, gain=0.12, kind="string", attack=0.3):
    out = np.zeros(N)
    for f in freqs:
        out += note_f(f, t0, dur, gain=gain, kind=kind, attack=attack)
    return out


def pew(t0, base=700, drop=180, dur=0.22, gain=0.30):
    """SFX bláster: barrido descendente + click."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = base * np.exp(-tt * 14) + drop
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 22)
    click = np.random.default_rng(3).uniform(-1, 1, n) * np.exp(-tt * 160) * 0.3
    out = np.zeros(N)
    i0 = int(t0 * SR)
    end = min(i0 + n, N)
    out[i0:end] = ((body + click) * gain)[: end - i0]
    return out


def whoosh(t0, dur=0.7, gain=0.16):
    """Whoosh: ruido pasa-bajos kernel FIJO + barrido de tono (PITFALL 3)."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    rng = np.random.default_rng(9)
    noise = rng.uniform(-1, 1, n)
    k = 24
    kern = np.ones(k) / k
    filt = np.convolve(noise, kern, mode="same")
    sweep_f = 300 + 2600 * (tt / dur) ** 2
    sweep = np.sin(2 * np.pi * np.cumsum(sweep_f) / SR) * 0.4
    env = np.sin(np.pi * tt / dur) ** 2
    out = np.zeros(N)
    i0 = int(t0 * SR)
    end = min(i0 + n, N)
    out[i0:end] = ((filt + sweep) * env * gain)[: end - i0]
    return out


def impact(t0, gain=0.5):
    """Hit orquestal: bajo + timpani + ruido."""
    out = np.zeros(N)
    out += note_f(55, t0, 1.2, gain=gain * 0.5, kind="bass", attack=0.005)
    out += note_f(110, t0, 0.9, gain=gain * 0.3, kind="timpani")
    n = int(0.4 * SR)
    tt = np.arange(n) / SR
    rng = np.random.default_rng(11)
    i0 = int(t0 * SR)
    end = min(i0 + n, N)
    out[i0:end] += (rng.uniform(-1, 1, n) * np.exp(-tt * 20) * gain * 0.25)[: end - i0]
    return out


# ---------- Notas (Re menor épico) — PITFALL 4: definir TODAS antes de usar ----------
D2, A1, C2, Bb1 = 73.42, 55.00, 65.41, 58.27
Bb2 = 116.54
C3, E3, G3, A2 = 130.81, 164.81, 196.00, 110.00
D3, A3, F3, Bb3, C4 = 146.83, 220.00, 174.61, 233.08, 261.63
D4, E4, F4, G4, A4, Bb4 = 293.66, 329.63, 349.23, 392.00, 440.00, 466.16
D5, C5 = 587.33, 523.25

mix = np.zeros(N)

# Progresión por compás (112 BPM, compás = 4 beats): Dm Bb F A
prog = [[D3, F3, A3], [D3, F3, Bb3], [C4, F3, A3], [C4, E4, A3]]
bar = BEAT * 4

# ---- Intro (0-8s): timpani + cuerdas largas + riser
for i in range(8):
    mix += note_f(73.42, i * BEAT * 2, 0.6, gain=0.42, kind="timpani")
mix += chord([D3, F3, A3], 0, 8, gain=0.10, attack=1.0)
mix += whoosh(5.5, 2.2, 0.18)

# ---- A (8-32s): tema épico — fanfarria ORIGINAL (no el tema de Williams)
fanfaria = [
    (0.0, D4, 0.5), (0.5, F4, 0.5), (1.0, A4, 1.0),
    (2.0, Bb4, 0.9), (3.0, A4, 0.9),
    (4.0, F4, 0.4), (4.4, G4, 0.4), (5.2, A4, 1.4),
    (7.0, F4, 0.8), (8.0, D4, 0.6), (8.6, F4, 0.6),
    (9.2, A4, 1.2), (10.2, Bb4, 1.8),
    (12.0, A4, 0.5), (12.5, G4, 0.5), (13.0, F4, 1.0),
    (14.0, E4, 1.6), (16.0, F4, 0.4), (16.4, G4, 0.4), (17.2, A4, 1.6),
    (19.0, Bb4, 1.0), (20.0, A4, 0.4), (20.4, G4, 0.4), (21.2, F4, 2.2),
]
for off, f, d in fanfaria:
    mix += note_f(f, 8 + off * BEAT, d * BEAT, gain=0.16, kind="brass", attack=0.03)

# Cuerdas staccato: arpegios en 8vos
for c_i in range(12):
    base_t = 8 + c_i * bar
    ch = prog[c_i % 4]
    for e in range(8):
        f = ch[e % 3] * (1 if e < 6 else 2)
        mix += note_f(f, base_t + e * BEAT / 2, BEAT * 0.45, gain=0.055, kind="string", attack=0.01)

# Bajo
bass_line = [D2, D2, C2, A1]
for c_i in range(12):
    mix += note_f(bass_line[c_i % 4], 8 + c_i * bar, bar * 0.95, gain=0.22, kind="bass", attack=0.02)

# Timpani: beats 1 y 3
for c_i in range(12):
    bt = 8 + c_i * bar
    mix += note_f(73.42, bt, 0.5, gain=0.35, kind="timpani")
    mix += note_f(73.42, bt + BEAT * 2, 0.5, gain=0.30, kind="timpani")

# ---- B (32-44s): sección lírica
lyric = [[D3, F3, A3], [Bb2, D3, F3], [C3, E3, G3], [A2, C3, E3]]
for c_i in range(6):
    bt = 32 + c_i * bar
    mix += chord(lyric[c_i % 4], bt, bar * 0.9, gain=0.11, attack=0.35)
    mix += note_f(D4, bt, bar * 0.9, gain=0.10, kind="string", vibrato=0.004, attack=0.3)
melB = [(0.0, F4, 1.0), (1.0, A4, 1.0), (2.0, D5, 2.0), (4.0, C5, 1.0),
        (5.0, A4, 1.0), (6.0, G4, 2.0), (8.0, E4, 1.0), (9.0, F4, 1.0), (10.0, G4, 2.0),
        (12.0, E4, 1.0), (13.0, C4, 1.0), (14.0, A3, 2.0)]
for off, f, d in melB:
    mix += note_f(f, 32 + off * BEAT, d * BEAT, gain=0.11, kind="string", vibrato=0.005, attack=0.15)
mix += whoosh(31.4, 0.7, 0.14)

# ---- A' (44-60s): final épico con hit
for off, f, d in fanfaria[:8]:
    mix += note_f(f, 44 + off * BEAT, d * BEAT, gain=0.18, kind="brass", attack=0.02)
for c_i in range(8):
    bt = 44 + c_i * bar
    ch = prog[c_i % 4]
    for e in range(8):
        f = ch[e % 3] * (1 if e < 6 else 2)
        mix += note_f(f, bt + e * BEAT / 2, BEAT * 0.45, gain=0.06, kind="string", attack=0.01)
for c_i in range(8):
    mix += note_f(bass_line[c_i % 4], 44 + c_i * bar, bar * 0.9, gain=0.24, kind="bass", attack=0.02)
for c_i in range(8):
    bt = 44 + c_i * bar
    mix += note_f(73.42, bt, 0.5, gain=0.38, kind="timpani")
    mix += note_f(73.42, bt + BEAT * 2, 0.5, gain=0.32, kind="timpani")
mix += chord([D3, F3, A3, D4], 56, 4, gain=0.12, attack=0.5)
mix += impact(58.0, 0.5)
mix += note_f(D3, 58.0, 2.0, gain=0.3, kind="bass", attack=0.005)

# ---- SFX láser (pew) en transiciones y whoosh en sweeps ----
mix += pew(19.7, base=900, gain=0.28)
mix += pew(20.1, base=600, gain=0.22)
mix += whoosh(19.6, 0.7, 0.16)
mix += pew(39.7, base=900, gain=0.28)
mix += pew(40.1, base=600, gain=0.22)
mix += whoosh(39.6, 0.7, 0.16)
mix += pew(56.5, base=950, gain=0.25)
mix += pew(57.0, base=650, gain=0.2)

# Normalizar + estéreo (ensanche con delay)
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.88
delay_n = int(0.016 * SR)
right = np.roll(mix, delay_n)
right[:delay_n] = 0
stereo = np.stack([mix, right], axis=1)
fade_n = int(0.6 * SR)
stereo[:fade_n, :] *= np.linspace(0, 1, fade_n)[:, None]
stereo[-fade_n:, :] *= np.linspace(1, 0, fade_n)[:, None]

pcm = (stereo * 32767).astype(np.int16)
out_path = sys.argv[1] if len(sys.argv) > 1 else "epic_track.wav"
with wave.open(out_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"OK {out_path} {pcm.shape} {DUR}s")
