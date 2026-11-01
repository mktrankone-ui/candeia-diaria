#!/usr/bin/env python3
"""Teste: (1) procura frases fora do português nos vídeos já publicados; (2) gera amostras das duas vozes."""
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import narrar

OUT = "teste"
os.makedirs(OUT, exist_ok=True)
rel = []
m = narrar._modelo()

# 1) auditoria dos vídeos publicados: idioma de cada trecho falado
for mp4 in sorted(glob.glob("pub/*.mp4")):
    audio = narrar.audio16k(mp4)
    segs, info = m.transcribe(audio, beam_size=1, vad_filter=True, multilingual=True)
    rel.append(f"## {os.path.basename(mp4)} (idioma geral {info.language})")
    for s in segs:
        lang, p = narrar.idioma(audio[int(s.start * 16000):int(s.end * 16000)])
        marca = "" if lang == "pt" else f"   <<< {lang} (pt={p:.2f})"
        rel.append(f"{s.start:6.1f}s {s.text.strip()}{marca}")
    rel.append("")

# 2) amostras das vozes com um roteiro real
rot = "roteiros/publicados/santos-20261101-manha.json"
for tipo in ("feminina", "masculina"):
    os.environ["CANDEIA_VOZ"] = tipo
    t = narrar.narrar(rot, f"{OUT}/amostra-{tipo}.mp3")
    rel.append(f"amostra {tipo}: {json.dumps(t)}")
rel.append(f"pt-BR forçado no SSML aceito pelo serviço: {narrar.FORCAR_PT}")
open(f"{OUT}/relatorio.txt", "w").write("\n".join(rel))
print("\n".join(rel))
