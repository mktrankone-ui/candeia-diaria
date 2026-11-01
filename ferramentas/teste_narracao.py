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
for mp4 in sorted(glob.glob("pub/perdao*.mp4")):
    audio = narrar.audio16k(mp4)
    segs, info = m.transcribe(audio, beam_size=1, vad_filter=True, multilingual=True)
    rel.append(f"## {os.path.basename(mp4)} (idioma geral {info.language})")
    for s in segs:
        lang, p = narrar.idioma(audio[int(s.start * 16000):int(s.end * 16000)])
        marca = "" if lang == "pt" else f"   <<< {lang} (pt={p:.2f})"
        rel.append(f"{s.start:6.1f}s {s.text.strip()}{marca}")
    rel.append("")

# 2) amostras das vozes com um roteiro real
# o roteiro do perdão é o que teve o "Amém!" lido em outro idioma
rot = "roteiros/publicados/perdao-20261101-noite.json"
for tipo in ("feminina", "masculina"):
    os.environ["CANDEIA_VOZ"] = tipo
    arq = f"{OUT}/amostra-{tipo}.mp3"
    t = narrar.narrar(rot, arq)
    rel.append(f"## amostra {tipo}: {json.dumps(t)}")
    audio = narrar.audio16k(arq)
    ini = t["intro"]
    for k, d in enumerate(t["por_linha"] + [t["cta_duracao"] + t["cta_inicio"] - ini - sum(t["por_linha"])]):
        trecho = audio[int(ini * 16000):int((ini + d) * 16000)]
        lang, p = narrar.idioma(trecho)
        segs, _ = m.transcribe(trecho, beam_size=1, language="pt", without_timestamps=True)
        rel.append(f"{ini:6.2f}s [{lang} pt={p:.2f}] {''.join(s.text for s in segs).strip()}")
        ini += d
open(f"{OUT}/relatorio.txt", "w").write("\n".join(rel))
print("\n".join(rel))

# 3) vídeo completo de exemplo com voz masculina e fundo por cena
import buscar_fundo, render, shutil
r = json.load(open(rot, encoding="utf-8"))
r.update({"id": "teste-cenas", "voz": "masculina", "fundo": "videos", "cta_tipo": "enviar",
          "cta": ["Envie para quem *precisa*", "Uma oração pode mudar o dia de alguém"],
          "cta_falado": "Envie esta oração para alguém que precisa dela hoje.",
          "cenas": ["person standing ocean sunset", "man thinking nature", "praying hands light", "storm clouds light",
                    "sunbeam forest", "couple hug sunset", "cross sunset", "crucifix church", "sun rays clouds"]})
rp = f"{OUT}/teste-cenas.json"
json.dump(r, open(rp, "w"), ensure_ascii=False, indent=1)
if os.environ.get("PIXABAY_KEY"):
    shutil.rmtree("trab-teste", ignore_errors=True)
    buscar_fundo.USADOS = "/tmp/usados-teste.json"
    buscar_fundo.buscar(rp, "trab-teste/fundo", "videos")
    os.environ.pop("CANDEIA_VOZ", None)
    narrar.narrar(rp, "trab-teste/voz.mp3")
    dur = render.montar(rp, f"{OUT}/teste-cenas.mp4", "videos:trab-teste/fundo", None, "trab-teste/voz.mp3")
    print("vídeo de teste", dur)
