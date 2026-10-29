#!/usr/bin/env python3
"""Gera os vídeos de todos os roteiros que ainda não têm vídeo publicado.

Roda no GitHub Actions. Para cada roteiros/*.json sem entrada em publicados/indice.json:
  1. busca fundo na Pixabay (fotos ou vídeos, campo "fundo" do roteiro; padrão alterna)
  2. gera a narração (voz Thalita) frase a frase
  3. renderiza com uma trilha sorteada de trilhas/
  4. copia o mp4 para publicados/ (que o workflow envia ao ramo "videos")
"""
import glob, json, os, random, shutil, subprocess, sys, traceback

BASE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(BASE, "publicados")
REPO = os.environ.get("GITHUB_REPOSITORY", "mktrankone-ui/candeia-diaria")
RAW = f"https://raw.githubusercontent.com/{REPO}/videos/"

sys.path.insert(0, BASE)
import buscar_fundo, narrar, render  # noqa: E402


def main(apenas=None):
    os.makedirs(PUB, exist_ok=True)
    idx_path = os.path.join(PUB, "indice.json")
    indice = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    trilhas = sorted(glob.glob(os.path.join(BASE, "trilhas", "*.mp3")) + glob.glob(os.path.join(BASE, "trilhas", "*.wav")))
    roteiros = sorted(glob.glob(os.path.join(BASE, "roteiros", "*.json")))
    feitos = 0
    for k, rp in enumerate(roteiros):
        rid = os.path.splitext(os.path.basename(rp))[0]
        if rid in indice or (apenas and rid not in apenas):
            continue
        r = json.load(open(rp, encoding="utf-8"))
        print(f"== {rid}", flush=True)
        trab = os.path.join(BASE, "trabalho", rid)
        shutil.rmtree(trab, ignore_errors=True); os.makedirs(trab)
        try:
            modo = r.get("fundo") or ("fotos" if len(indice) % 2 == 0 else "videos")
            fundo = "procedural"
            if os.environ.get("PIXABAY_KEY"):
                n = buscar_fundo.buscar(rp, os.path.join(trab, "fundo"), modo)
                if n:
                    fundo = f"{modo}:{os.path.join(trab, 'fundo')}"
            voz = os.path.join(trab, "voz.mp3")
            narrar.narrar(rp, voz)
            trilha = random.choice(trilhas) if trilhas else None
            saida = os.path.join(PUB, f"{rid}.mp4")
            dur = render.montar(rp, saida, fundo, trilha, voz)
            indice[rid] = {"arquivo": f"{rid}.mp4", "url": RAW + f"{rid}.mp4", "serie": r.get("serie"),
                           "legenda": r.get("legenda", ""), "duracao": round(dur, 1), "fundo": fundo.split(":")[0],
                           "trilha": os.path.basename(trilha) if trilha else None}
            json.dump(indice, open(idx_path, "w"), ensure_ascii=False, indent=1)
            feitos += 1
            print(f"ok {rid} ({dur:.1f}s, fundo={fundo.split(':')[0]})", flush=True)
        except Exception:
            traceback.print_exc()
    print(f"{feitos} vídeo(s) gerado(s)")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
