#!/usr/bin/env python3
"""BGM tech/chill para reels DevOps (original, libre de copyright).
Genera una pista de DUR segundos; N variantes por seed distinto (una por video).
Conocido-bueno: verificado 2026-08-25 en reels-instagram (4 WAV 23s, seeds 1-4).
Uso: python3 synth_reel_bgm.py <out.wav> [seed]
"""
import sys
import numpy as np
import wave

SR = 44100
DUR = 23.0
N = int(SR * DUR)
t = np.arange(N) / SR
BPM = 118.0
BEAT = 60.0 / BPM  # ~0.508s
BAR = BEAT * 4

rng_seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
rng = np.random.default_rng(rng_seed)


def note_f(freq, t0, dur, gain=0.25, kind="pluck", attack=0.01):
    """kind: pluck|pad|bass|kick|hat|riser"""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    atk = np.minimum(tt / max(attack, 1e-4), 1.0)
    rel = np.minimum((dur - tt) / 0.2, 1.0).clip(0, 1)
    env = atk * rel
    ph = 2 * np.pi * freq * tt
    if kind == "pluck":
        osc = (0.7 * np.sin(ph) + 0.25 * np.sin(2 * ph)) * np.exp(-tt * 5)
    elif kind == "pad":
        osc = (0.5 * np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph))
        osc *= (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * tt))
        env = np.minimum(tt / 0.4, 1.0) * np.minimum((dur - tt) / 0.6, 1.0).clip(0, 1)
    elif kind == "bass":
        osc = 0.7 * np.sin(ph) + 0.3 * np.sin(2 * ph)
        env = np.minimum(tt / 0.02, 1.0) * np.exp(-tt * 2.2)
    elif kind == "kick":
        pd = 90 * np.exp(-tt * 30) + 40
        ph2 = 2 * np.pi * np.cumsum(pd) / SR
        osc = np.sin(ph2) * np.exp(-tt * 16)
        env = np.ones_like(tt)
    elif kind == "hat":
        osc = rng.uniform(-1, 1, n) * np.exp(-tt * 40)
        env = np.ones_like(tt)
    elif kind == "riser":
        sweep_f = 200 + 2800 * (tt / dur) ** 2.2
        osc = (0.6 * np.sin(2 * np.pi * np.cumsum(sweep_f) / SR) +
               0.4 * rng.uniform(-1, 1, n))
        env = (tt / dur) ** 2.5
    else:
        osc = np.sin(ph)
    out = np.zeros(N)
    i0 = int(t0 * SR)
    if i0 >= N:
        return out
    end = min(i0 + n, N)
    out[i0:end] = (osc * env * gain)[: end - i0]
    return out


def chord(freqs, t0, dur, gain=0.1, kind="pad", attack=0.4):
    out = np.zeros(N)
    for f in freqs:
        out += note_f(f, t0, dur, gain=gain, kind=kind, attack=attack)
    return out


# Notas (Am — F — C — G): vibra tech pero relajada
A1, C2, E2, F2, G2 = 55.00, 65.41, 82.41, 87.31, 98.00
A2, B2, C3, D3, E3, F3, G3 = 110.00, 123.47, 130.81, 146.83, 164.81, 174.61, 196.00
A3, B3, C4, D4, E4, F4, G4 = 220.00, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00
A4, C5, E5 = 440.00, 523.25, 659.26

prog = [[A2, C3, E3], [F2, A2, C3], [C3, E3, G3], [G2, B2, D3]]
bass_line = [A1, F2, C2, G2]

mix = np.zeros(N)

# ---- Sección loop (0-20s): 10 compases
n_bars = 10
for c_i in range(n_bars):
    bt = c_i * BAR
    ch = prog[c_i % 4]
    mix += chord(ch, bt, BAR * 0.95, gain=0.085, kind="pad", attack=0.4)
    mix += note_f(bass_line[c_i % 4], bt, BEAT * 0.9, gain=0.24, kind="bass", attack=0.02)
    mix += note_f(bass_line[c_i % 4] * 1.5, bt + BEAT, BEAT * 0.7, gain=0.13, kind="bass", attack=0.02)
    mix += note_f(bass_line[c_i % 4], bt + BEAT * 2, BEAT * 0.9, gain=0.22, kind="bass", attack=0.02)
    mix += note_f(bass_line[c_i % 4] * 1.5, bt + BEAT * 3, BEAT * 0.7, gain=0.13, kind="bass", attack=0.02)
    mix += note_f(50, bt, 0.3, gain=0.5, kind="kick")
    mix += note_f(50, bt + BEAT * 2, 0.3, gain=0.45, kind="kick")
    mix += note_f(8000, bt + BEAT, 0.08, gain=0.09, kind="hat")
    mix += note_f(8000, bt + BEAT * 3, 0.08, gain=0.08, kind="hat")
    arp = [ch[0] * 2, ch[1] * 2, ch[2] * 2, ch[1] * 2,
           ch[0] * 4, ch[1] * 4, ch[2] * 4, ch[1] * 4]
    for e in range(8):
        f = arp[e] * (1.0 if rng.uniform() > 0.15 else 2.0)
        mix += note_f(f, bt + e * BEAT / 2, BEAT * 0.42, gain=0.075, kind="pluck", attack=0.008)

# ---- Outro (20-23s): riser + fade
n_r = int(3.0 * SR)
tt_r = np.arange(n_r) / SR
sweep_f = 200 + 2800 * (tt_r / 3.0) ** 2.2
sr_body = (0.5 * np.sin(2 * np.pi * np.cumsum(sweep_f) / SR) +
           0.4 * rng.uniform(-1, 1, n_r))
sr_env = (tt_r / 3.0) ** 2.5
i0 = int(20.0 * SR)
mix[i0:i0 + n_r] = sr_body * sr_env * 0.14
mix += chord([A2, C3, E3, A3], 21.0, 1.8, gain=0.12, kind="pad", attack=0.5)

# Normalizar + estéreo
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85
delay_n = int(0.014 * SR)
right = np.roll(mix, delay_n)
right[:delay_n] = 0
stereo = np.stack([mix, right], axis=1)
fade_n = int(0.5 * SR)
stereo[:fade_n, :] *= np.linspace(0, 1, fade_n)[:, None]
stereo[-fade_n:, :] *= np.linspace(1, 0, fade_n)[:, None]

pcm = (stereo * 32767).astype(np.int16)
out_path = sys.argv[1]
with wave.open(out_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"OK {out_path} {pcm.shape} {DUR}s seed={rng_seed}")
