#!/usr/bin/env python3
"""Baixa fundos da Pixabay (fotos verticais ou vídeos) para um roteiro, sem repetir mídia já usada.

Uso: PIXABAY_KEY=... python3 buscar_fundo.py roteiros/x.json pasta_destino [fotos|videos] [quantidade]
Registra os ids usados em usados.json.
"""
import json, os, random, sys, urllib.parse, urllib.request

KEY = os.environ.get("PIXABAY_KEY", "")
BASE = os.path.dirname(os.path.abspath(__file__))
USADOS = os.path.join(BASE, "usados.json")

BUSCAS_PADRAO = {
    "amanhecer": ["sunrise mountains", "sunrise clouds", "morning light field", "golden sunrise sky", "dawn landscape"],
    "noite": ["night sky stars", "moon clouds night", "candle light dark", "starry sky", "night lake moon"],
    "paz": ["calm lake", "peaceful nature", "soft clouds sky", "meadow sunset", "quiet forest light"],
    "esperanca": ["sun rays clouds", "light through trees", "sunrise ocean", "rainbow sky", "golden field sunset"],
    "dificil": ["storm clouds light", "rain window", "lonely road sunset", "sunbeam dark clouds", "lighthouse sea"],
    "familia": ["family walking sunset", "hands holding sunset", "home warm light", "children field sunset"],
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "candeia-diaria/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def baixar(url, destino):
    with open(destino, "wb") as f:
        f.write(get(url))


def carregar_usados():
    try:
        return json.load(open(USADOS))
    except Exception:
        return {"fotos": [], "videos": []}


def buscar(roteiro, destino, modo="fotos", qtd=None):
    assert KEY, "PIXABAY_KEY não definida"
    r = json.load(open(roteiro, encoding="utf-8"))
    termos = r.get("busca") or BUSCAS_PADRAO.get(r.get("tema", "amanhecer"), BUSCAS_PADRAO["amanhecer"])
    termos = list(termos); random.shuffle(termos)
    usados = carregar_usados()
    os.makedirs(destino, exist_ok=True)
    qtd = qtd or (9 if modo == "fotos" else 6)
    pegos = []
    for termo in termos * 2:
        if len(pegos) >= qtd:
            break
        q = urllib.parse.quote_plus(termo)
        pagina = random.randint(1, 3)
        if modo == "fotos":
            url = (f"https://pixabay.com/api/?key={KEY}&q={q}&image_type=photo&orientation=vertical"
                   f"&min_height=1600&safesearch=true&per_page=40&page={pagina}")
        else:
            url = f"https://pixabay.com/api/videos/?key={KEY}&q={q}&safesearch=true&per_page=40&page={pagina}"
        try:
            hits = json.loads(get(url)).get("hits", [])
        except Exception as e:
            print("busca falhou", termo, e); continue
        random.shuffle(hits)
        for h in hits:
            if len(pegos) >= qtd or h["id"] in usados[modo]:
                continue
            if h.get("isAiGenerated"):
                continue
            try:
                if modo == "fotos":
                    link = h.get("largeImageURL") or h["webformatURL"]
                    arq = os.path.join(destino, f"{len(pegos):02d}-{h['id']}.jpg")
                else:
                    v = h["videos"]
                    if h.get("duration", 0) < 6:
                        continue
                    esc = v["medium"] if v["medium"]["size"] and v["medium"]["size"] < 60e6 else v["small"]
                    if not esc["url"]:
                        continue
                    link = esc["url"]
                    arq = os.path.join(destino, f"{len(pegos):02d}-{h['id']}.mp4")
                baixar(link, arq)
                pegos.append(h["id"]); usados[modo].append(h["id"])
                print("ok", termo, h["id"], arq)
            except Exception as e:
                print("download falhou", h.get("id"), e)
    json.dump(usados, open(USADOS, "w"))
    return pegos


if __name__ == "__main__":
    modo = sys.argv[3] if len(sys.argv) > 3 else "fotos"
    qtd = int(sys.argv[4]) if len(sys.argv) > 4 else None
    print(len(buscar(sys.argv[1], sys.argv[2], modo, qtd)), "arquivos")
