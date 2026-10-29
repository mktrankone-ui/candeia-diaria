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
    # estética: cristã/católica, leão (Leão de Judá), pessoas felizes, paisagens, cidades, tons neutros e calmos
    "amanhecer": ["sunrise field", "sunrise cross", "morning light church", "golden hour countryside",
                  "sunrise mountains", "morning window light", "dawn city skyline"],
    "gratidao": ["happy people nature", "family sunset field", "wheat field golden", "hands holding sunset",
                 "woman smiling sunlight", "friends laughing outdoors"],
    "familia": ["happy family walking", "mother child sunset", "family home warm light", "grandparents grandchildren",
                "couple holding hands sunset"],
    "trabalho": ["city morning sunrise", "city skyline dawn", "people walking city morning", "coffee window morning",
                 "office window sunrise"],
    "esperanca": ["sun rays clouds", "lion sunset", "light through trees", "arms raised sunset", "sunrise ocean",
                  "lion portrait golden"],
    "forca": ["lion portrait", "lion sunset", "mountain peak sunrise", "lighthouse storm", "eagle flying sky"],
    "fe": ["cross sunset", "church interior light", "cathedral light", "rosary hands", "candles church",
           "praying hands light", "chapel countryside"],
    "nossa_senhora": ["virgin mary statue", "rosary", "church candles", "cathedral interior", "white roses light",
                      "chapel candles"],
    "noite": ["night sky stars", "candle light dark", "moon clouds night", "city night lights", "starry sky mountains",
              "night lake moon"],
    "paz": ["calm lake", "soft clouds sky", "ocean waves sunset", "peaceful nature neutral", "beige minimal nature",
            "fog forest calm", "dandelion field sunset"],
    "ansiedade": ["calm lake", "soft clouds sky", "breathing nature calm", "ocean waves gentle", "fog mountains calm",
                  "rain window calm"],
    "cura": ["light through window", "hands holding", "candle light", "church interior light", "sunbeam forest",
             "flowers soft light"],
    "dificil": ["storm clouds light", "lighthouse sea", "rain window", "lonely road sunset", "sunbeam dark clouds",
                "lion portrait"],
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "candeia-diaria/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def baixar(url, destino):
    with open(destino, "wb") as f:
        f.write(get(url))


def valido(arq, modo):
    if os.path.getsize(arq) < 20000:
        return False
    if modo == "fotos":
        try:
            from PIL import Image
            with Image.open(arq) as t:
                t.verify()
            return True
        except Exception:
            return False
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                        "-of", "csv=p=0", arq], capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() != ""


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
                if not valido(arq, modo):
                    os.remove(arq); print("arquivo inválido descartado", h["id"]); continue
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
