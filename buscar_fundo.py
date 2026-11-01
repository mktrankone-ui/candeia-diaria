#!/usr/bin/env python3
"""Baixa fundos da Pixabay (fotos verticais ou vídeos) para um roteiro, sem repetir mídia já usada.

Uso: PIXABAY_KEY=... python3 buscar_fundo.py roteiros/x.json pasta_destino [fotos|videos] [quantidade]
Registra os ids usados em usados.json.
"""
import json, math, os, random, sys, urllib.parse, urllib.request

KEY = os.environ.get("PIXABAY_KEY", "")
BASE = os.path.dirname(os.path.abspath(__file__))
USADOS = os.path.join(BASE, "usados.json")

# Estética: natureza grandiosa e serena + símbolos católicos. Nada de objetos aleatórios (comida, mesa,
# enfeite de jardim, brinquedo). Cada tema só tem termos que "conversam" com a oração.
BUSCAS_PADRAO = {
    "amanhecer": ["sunrise mountains", "sunrise ocean", "sunrise field", "sunrise cross", "golden hour meadow",
                  "sun rays forest", "morning mist lake", "sunrise sky clouds"],
    "gratidao": ["wheat field sunset", "person arms open sunrise", "woman walking field sunset", "sunrise mountains",
                 "golden hour meadow", "waterfall sunlight"],
    "familia": ["family walking beach sunset", "family walking field", "mother child sunset", "couple walking sunset",
                "father son nature", "family hug sunset"],
    "trabalho": ["person walking road sunrise", "man walking mountain sunrise", "road mountains sunrise",
                 "sunrise field", "hands holding sunset", "path forest light"],
    "esperanca": ["sun rays clouds", "light through trees", "sunrise ocean", "rainbow sky", "lion sunset",
                  "person mountain top sunrise", "waterfall sunlight"],
    "forca": ["lion portrait", "lion sunset", "lion walking", "eagle flying sky", "mountain peak sunrise",
              "lighthouse waves", "waves rocks ocean"],
    "fe": ["cross sunset", "cross hill sky", "church interior light", "cathedral light", "rosary hands",
           "praying hands light", "chapel mountains", "church candles"],
    "nossa_senhora": ["virgin mary statue", "our lady statue", "rosary", "rosary hands", "virgin mary",
                      "church candles", "white roses", "cathedral interior"],
    "jesus": ["cross sunset", "jesus christ", "lamb", "lamb field", "lion portrait", "eucharist", "communion host",
              "crucifix church", "cross hill sky"],
    "terco": ["rosary", "rosary hands", "rosary bible", "praying hands rosary", "church candles"],
    "eucaristia": ["eucharist", "communion host", "chalice church", "church altar", "monstrance"],
    "noite": ["night sky stars", "milky way", "starry sky mountains", "moon clouds night", "night lake moon",
              "candle light dark", "moonlight ocean"],
    "paz": ["calm lake", "lake mountains reflection", "ocean waves sunset", "waterfall forest", "river forest",
            "fog forest", "clouds sky", "desert dunes sunset"],
    "ansiedade": ["calm lake", "ocean waves gentle", "river stream forest", "fog mountains", "clouds sky",
                  "woman sitting lake", "rain window"],
    "cura": ["light through window", "sunbeam forest", "waterfall sunlight", "hands holding", "candle light",
             "couple hug sunset", "river stream forest"],
    "dificil": ["storm clouds light", "lighthouse waves", "sunbeam dark clouds", "man thinking nature",
                "woman thinking window", "lonely road sunset", "desert dunes"],
    "saude": ["sunbeam forest", "waterfall sunlight", "hands holding", "light through window", "river stream forest",
              "praying hands light"],
    "luto": ["sunset clouds", "cemetery flowers", "candle light dark", "sun rays clouds", "white roses",
             "person standing ocean sunset"],
    "pessoas": ["woman walking field", "man walking mountain", "person standing ocean sunset", "woman thinking nature",
                "couple hug sunset", "friends hug", "woman praying nature"],
}

# Tags que denunciam fundo fora de propósito: se aparecerem na mídia, ela é descartada.
PROIBIDAS = {
    "gnome", "gnomes", "dwarf", "garden gnome", "figurine", "toy", "toys", "doll", "cookie", "cookies", "biscuit",
    "biscuits", "cake", "dessert", "food", "meal", "breakfast", "coffee", "cup", "table", "kitchen", "restaurant",
    "drink", "wine", "beer", "pumpkin", "halloween", "skull", "zombie", "santa claus", "easter bunny", "egg",
    "buddha", "buddhism", "hindu", "ganesha", "shiva", "temple", "mosque", "islam", "muslim", "pagoda", "zen",
    "angel statue", "cupid", "bikini", "sexy", "model", "fashion", "party", "money", "dollar", "car", "cars",
    "computer", "laptop", "phone", "smartphone", "business", "office", "shopping", "cat", "dog", "pet", "selfie",
    "covid", "covid-19", "coronavirus", "virus", "soap", "hygiene", "washing", "bathroom", "mask", "strawberry",
    "fruit", "abstract", "digital", "technology", "brain", "intelligence", "artificial", "cyber", "futuristic",
    "fantasy", "particles", "network", "data", "honeymoon", "lovers", "kiss", "wedding dress", "graffiti", "text", "lettering", "sign", "logo", "advertisement", "cartoon", "illustration", "3d", "render",
}
# Palavras genéricas da busca que não servem para confirmar se a mídia tem a ver com o termo.
GENERICAS = {"light", "sky", "nature", "people", "person", "golden", "hour", "calm", "gentle", "dark", "soft"}
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


def adequado(hit, termo):
    """A mídia precisa ter a ver com o termo buscado e não ter nenhuma tag proibida."""
    tags = {t.strip().lower() for t in hit.get("tags", "").split(",") if t.strip()}
    palavras = {w for t in tags for w in t.split()}
    if tags & PROIBIDAS or palavras & PROIBIDAS:
        return False
    if hit.get("type") == "animation":          # vídeos animados/renderizados ficam de fora
        return False
    t = termo.lower()
    if palavras & {"statue", "sculpture", "figure"} and not ("statue" in t or "mary" in t or "lady" in t):
        return False                            # estátua só quando a cena pede (Nossa Senhora)
    chave = {w for w in termo.lower().split() if w not in GENERICAS} or set(termo.lower().split())
    # exige quase todas as palavras-chave: "praying hands" não pode virar "lavando as mãos"
    precisa = len(chave) if len(chave) <= 2 else math.ceil(len(chave) * 2 / 3)
    return len(chave & palavras) >= precisa


def carregar_usados():
    try:
        return json.load(open(USADOS))
    except Exception:
        return {"fotos": [], "videos": []}


def _url(termo, modo, pagina):
    q = urllib.parse.quote_plus(termo)
    if modo == "fotos":
        return (f"https://pixabay.com/api/?key={KEY}&q={q}&image_type=photo&orientation=vertical"
                f"&min_height=1600&safesearch=true&per_page=40&page={pagina}")
    return f"https://pixabay.com/api/videos/?key={KEY}&q={q}&safesearch=true&per_page=40&page={pagina}"


def _pegar_um(termo, modo, usados, destino, ordem):
    """Baixa uma mídia adequada para o termo. Devolve o id ou None."""
    for pagina in random.sample([1, 2, 3], 3):
        try:
            hits = json.loads(get(_url(termo, modo, pagina))).get("hits", [])
        except Exception as e:
            print("busca falhou", termo, e); continue
        random.shuffle(hits)
        for h in hits:
            if h["id"] in usados[modo] or h.get("isAiGenerated"):
                continue
            if not adequado(h, termo):
                continue
            try:
                if modo == "fotos":
                    link = h.get("largeImageURL") or h["webformatURL"]
                    arq = os.path.join(destino, f"{ordem:02d}-{h['id']}.jpg")
                else:
                    v = h["videos"]
                    if h.get("duration", 0) < 6:
                        continue
                    esc = v["medium"] if v["medium"]["size"] and v["medium"]["size"] < 60e6 else v["small"]
                    if not esc["url"]:
                        continue
                    link = esc["url"]
                    arq = os.path.join(destino, f"{ordem:02d}-{h['id']}.mp4")
                baixar(link, arq)
                if not valido(arq, modo):
                    os.remove(arq); print("arquivo inválido descartado", h["id"]); continue
                usados[modo].append(h["id"])
                print("ok", ordem, termo, h["id"], "|", h.get("tags", ""), flush=True)
                return h["id"]
            except Exception as e:
                print("download falhou", h.get("id"), e)
        if pagina == 1 and not hits:
            break
    return None


def buscar(roteiro, destino, modo="fotos", qtd=None):
    """Com "cenas" no roteiro (um termo por frase), baixa uma mídia por cena, na ordem da narração.
    Sem "cenas", usa "busca" ou o tema e baixa qtd mídias variadas."""
    assert KEY, "PIXABAY_KEY não definida"
    r = json.load(open(roteiro, encoding="utf-8"))
    usados = carregar_usados()
    os.makedirs(destino, exist_ok=True)
    pegos = []
    tema = BUSCAS_PADRAO.get(r.get("tema", "amanhecer"), BUSCAS_PADRAO["amanhecer"])
    cenas = r.get("cenas")
    if cenas:
        for k, termo in enumerate(cenas):
            alternativas = [termo] + random.sample(tema, len(tema))   # se o termo não render, cai no tema
            for t in alternativas:
                got = _pegar_um(t, modo, usados, destino, k)
                if got:
                    pegos.append(got); break
    else:
        termos = list(r.get("busca") or tema); random.shuffle(termos)
        qtd = qtd or (9 if modo == "fotos" else 6)
        for termo in termos * 2:
            if len(pegos) >= qtd:
                break
            got = _pegar_um(termo, modo, usados, destino, len(pegos))
            if got:
                pegos.append(got)
    json.dump(usados, open(USADOS, "w"))
    return pegos


if __name__ == "__main__":
    modo = sys.argv[3] if len(sys.argv) > 3 else "fotos"
    qtd = int(sys.argv[4]) if len(sys.argv) > 4 else None
    print(len(buscar(sys.argv[1], sys.argv[2], modo, qtd)), "arquivos")
