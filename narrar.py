#!/usr/bin/env python3
"""Gera a narração de um roteiro, frase a frase, e devolve os tempos de cada linha.

Uso: python3 narrar.py roteiros/x.json saida/x-voz.mp3  → grava também saida/x-voz.json com os tempos
"""
import asyncio, json, os, subprocess, sys, tempfile

VOZ = os.environ.get("CANDEIA_VOZ", "pt-BR-ThalitaMultilingualNeural")
RATE = os.environ.get("CANDEIA_RATE", "-12%")
PITCH = os.environ.get("CANDEIA_PITCH", "-2Hz")
INTRO = 1.6      # silêncio antes da primeira frase (título aparecendo)
PAUSA = 0.85     # respiro depois de cada frase
CTA_PAUSA = 0.6


def duracao(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


async def tts(texto, destino):
    import edge_tts
    await edge_tts.Communicate(texto, VOZ, rate=RATE, pitch=PITCH).save(destino)


def limpar(t):
    return t.replace("*", "").strip()


def narrar(roteiro, saida):
    r = json.load(open(roteiro, encoding="utf-8"))
    tmp = tempfile.mkdtemp()
    falas = [limpar(l) for l in r["linhas"]]
    cta = r.get("cta_falado") or limpar(r["cta"][0]) + "."
    partes, por_linha = [], []
    for k, f in enumerate(falas + [cta]):
        p = os.path.join(tmp, f"{k:02d}.mp3")
        asyncio.run(tts(f, p))
        partes.append(p)
    # silêncios
    def silencio(seg, nome):
        p = os.path.join(tmp, nome)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                        "-t", f"{seg:.3f}", "-c:a", "libmp3lame", "-b:a", "96k", p], check=True)
        return p
    lista = [silencio(INTRO, "intro.mp3")]
    sp = silencio(PAUSA, "pausa.mp3")
    for p in partes[:-1]:
        d = duracao(p)
        por_linha.append(round(d + PAUSA, 3))
        lista += [p, sp]
    lista += [silencio(CTA_PAUSA, "pcta.mp3"), partes[-1]]
    cat = os.path.join(tmp, "lista.txt")
    with open(cat, "w") as f:
        for p in lista:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", cat,
                    "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "160k", saida], check=True)
    tempos = {"intro": INTRO, "por_linha": por_linha, "cta_inicio": INTRO + sum(por_linha) + CTA_PAUSA,
              "cta_duracao": duracao(partes[-1]), "total": duracao(saida)}
    json.dump(tempos, open(os.path.splitext(saida)[0] + ".json", "w"), indent=1)
    return tempos


if __name__ == "__main__":
    print(json.dumps(narrar(sys.argv[1], sys.argv[2]), indent=1))
