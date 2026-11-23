"""Gera um mp3 por cena a partir de narracao-ecotacoes/textos.json (voz Antonio, edge-tts)."""
import asyncio, json, os, subprocess
import edge_tts

BASE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(BASE, "textos.json"), encoding="utf-8"))
out = os.path.join(BASE, "audio"); os.makedirs(out, exist_ok=True)

async def gerar(cena):
    p = os.path.join(out, cena["id"] + ".mp3")
    for tentativa in range(3):
        try:
            await edge_tts.Communicate(cena["texto"], cfg["voz"], rate=cfg["rate"], pitch=cfg["pitch"]).save(p)
            break
        except Exception as e:
            print("erro", cena["id"], e); await asyncio.sleep(3)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                             capture_output=True, text=True).stdout.strip() or 0)
    print(cena["id"], round(d, 2), "s")
    return {"id": cena["id"], "duracao": d}

async def main():
    res = [await gerar(c) for c in cfg["cenas"]]
    json.dump(res, open(os.path.join(out, "duracoes.json"), "w"), indent=1)

asyncio.run(main())
