#!/usr/bin/env python3
"""Gera uma trilha ambiente calma (pad + piano suave) para testes. Uso: python3 trilha_sintetica.py saida.wav [segundos]"""
import sys, wave
import numpy as np

SR = 44100
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 60
n = int(SR * dur)
t = np.arange(n) / SR
rng = np.random.default_rng(3)

def hz(m):  # nota MIDI -> Hz
    return 440 * 2 ** ((m - 69) / 12)

# progressão em Ré maior: D - Bm - G - A (6 s cada)
acordes = [[50, 57, 62, 66, 69], [47, 54, 59, 62, 66], [43, 50, 55, 59, 62], [45, 52, 57, 61, 64]]
L = 6.0
pad = np.zeros(n)
for k in range(int(dur / L) + 1):
    notas = acordes[k % 4]
    s, e = int(k * L * SR), min(n, int((k * L + L + 2) * SR))
    if s >= n:
        break
    tt = t[s:e] - k * L
    env = np.minimum(1, tt / 2.0) * np.clip((L + 2 - tt) / 2.5, 0, 1)
    for m in notas:
        f = hz(m)
        v = sum(np.sin(2 * np.pi * f * d * tt + rng.random() * 6) for d in (0.997, 1.0, 1.003)) / 3
        v += 0.25 * np.sin(2 * np.pi * 2 * f * tt)
        pad[s:e] += v * env * 0.09

piano = np.zeros(n)
melodia = [74, 76, 78, 81, 78, 76, 74, 73, 71, 74, 78, 76, 74, 69, 73, 76]
passo = 1.5
for j, m in enumerate(melodia * int(dur / (passo * len(melodia)) + 1)):
    s = int((1.0 + j * passo) * SR)
    if s >= n:
        break
    e = min(n, s + int(4 * SR))
    tt = t[s:e] - t[s]
    f = hz(m)
    env = np.exp(-tt * 1.4) * np.minimum(1, tt / 0.01)
    v = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 3) + 0.12 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 5)
    piano[s:e] += v * env * (0.16 if j % 4 else 0.2)

mix = pad + piano
# reverb simples por convolução com ruído decaindo
ir_t = np.arange(int(SR * 2.8)) / SR
ir = rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t * 2.2)
ir[0] = 6
wet = np.fft.irfft(np.fft.rfft(mix, n + len(ir)) * np.fft.rfft(ir, n + len(ir)))[:n]
wet /= np.max(np.abs(wet)) + 1e-9
out = 0.55 * mix / (np.max(np.abs(mix)) + 1e-9) + 0.6 * wet
# leve passa-baixa
k = np.ones(6) / 6
out = np.convolve(out, k, mode="same")
out = out / np.max(np.abs(out)) * 0.8
fade = int(SR * 3)
out[-fade:] *= np.linspace(1, 0, fade)
st = np.stack([out, np.roll(out, 300)], 1)
pcm = (st * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", sys.argv[1])
