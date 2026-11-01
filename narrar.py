#!/usr/bin/env python3
"""Gera a narração de um roteiro, frase a frase, e devolve os tempos de cada linha.

Uso: python3 narrar.py roteiros/x.json saida/x-voz.mp3  → grava também saida/x-voz.json com os tempos

Vozes (campo "voz" do roteiro): "feminina" (Thalita) ou "masculina" (Antonio).

Idioma: a Thalita é "multilingual" e, numa frase muito curta e solta ("Amém!"), pode ler em outro
idioma. Por isso:
  1. frases curtas (até 3 palavras) são sintetizadas junto da frase vizinha, para a voz ter
     contexto de português, e depois separadas pelo tempo exato das palavras;
  2. cada trecho é conferido com o Whisper; se não sair em português é refeito e, se insistir,
     a narração inteira passa para a voz de reserva (Francisca, monolíngue pt-BR).
"""
import asyncio, json, os, re, subprocess, sys, tempfile

VOZES = {
    "feminina": {"voz": "pt-BR-ThalitaMultilingualNeural", "rate": "-12%", "pitch": "-2Hz",
                 "reserva": "pt-BR-FranciscaNeural"},
    # Antonio é monolíngue pt-BR. Mais lento e mais grave: voz grossa e suave.
    "masculina": {"voz": "pt-BR-AntonioNeural", "rate": "-14%", "pitch": "-9Hz", "reserva": None},
}
INTRO = 0.15     # a voz entra já no primeiro segundo (gancho falado imediatamente)
PAUSA = 0.70     # respiro depois de cada frase
CTA_PAUSA = 0.5
CURTA = 3        # frases com até 3 palavras são sintetizadas junto da vizinha
TENTATIVAS = 2


def duracao(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def palavras(t):
    return re.findall(r"[0-9A-Za-zÀ-ÿ]+", t)


def norm(t):
    return "".join(palavras(t)).lower()


async def _tts(texto, destino, voz, rate, pitch):
    """Sintetiza e devolve as marcas de tempo de cada palavra [(inicio_s, fim_s, texto)]."""
    import edge_tts
    com = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch, boundary="WordBoundary")
    marcas = []
    with open(destino, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                marcas.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    return marcas


def tts(texto, destino, voz, rate, pitch):
    marcas = asyncio.run(_tts(texto, destino, voz, rate, pitch))
    if not os.path.exists(destino) or os.path.getsize(destino) < 2000:
        raise RuntimeError(f"áudio vazio para: {texto}")
    return marcas


# ---------------------------------------------------------------- conferência de idioma
_MODELO = None


def _modelo():
    global _MODELO
    if _MODELO is None:
        from faster_whisper import WhisperModel
        _MODELO = WhisperModel(os.environ.get("CANDEIA_WHISPER", "small"), device="cpu", compute_type="int8")
    return _MODELO


def audio16k(arquivo, ini=None, fim=None):
    """Lê o áudio com o ffmpeg (16 kHz mono float32) — evita depender do PyAV do faster-whisper."""
    import numpy as np
    corte = (["-ss", f"{ini:.2f}"] if ini is not None else []) + (["-to", f"{fim:.2f}"] if fim is not None else [])
    out = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", arquivo, *corte, "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32)


def idioma(arquivo):
    """Devolve (idioma, probabilidade de português). Sem Whisper instalado devolve ('?', 1.0)."""
    try:
        m = _modelo()
    except Exception as e:
        print("AVISO: Whisper indisponível, idioma não conferido:", e, flush=True)
        return "?", 1.0
    _, info = m.transcribe(audio16k(arquivo) if isinstance(arquivo, str) else arquivo,
                           beam_size=1, without_timestamps=True)
    probs = dict(info.all_language_probs or [])
    return info.language, probs.get("pt", 1.0 if info.language == "pt" else 0.0)


def em_portugues(arquivo):
    lang, p = idioma(arquivo)
    return lang in ("pt", "?") and p >= 0.5, lang, p


# ---------------------------------------------------------------- frases e grupos
def limpar(t):
    return t.replace("*", "").strip()


def curta(t):
    return len(palavras(t)) <= CURTA


def agrupar(textos):
    """Junta cada frase curta à anterior (a primeira, se curta, vai com a segunda). Devolve listas de índices."""
    grupos = []
    for k, t in enumerate(textos):
        if grupos and len(grupos[-1]) == 1 and (curta(t) or (k == 1 and curta(textos[0]))):
            grupos[-1].append(k)
        else:
            grupos.append([k])
    return grupos


def _corte(marcas, segunda):
    """Instante para separar o áudio antes da frase `segunda` (pelas marcas das palavras)."""
    alvo, acc = norm(segunda), ""
    for i in range(len(marcas) - 1, 0, -1):
        acc = norm(marcas[i][2]) + acc
        if acc == alvo:
            return (marcas[i - 1][1] + marcas[i][0]) / 2
        if len(acc) > len(alvo):
            break
    return None


def _recorta(src, dst, ini=None, fim=None):
    corte = (["-ss", f"{ini:.3f}"] if ini is not None else []) + (["-to", f"{fim:.3f}"] if fim is not None else [])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, *corte, "-ar", "24000", "-ac", "1", dst],
                   check=True)


def sintetiza_grupo(textos, idx, cfg, voz, tmp):
    """Gera o áudio de um grupo (1 ou 2 frases), confere o idioma e devolve um wav por frase."""
    texto = " ".join(textos[i] for i in idx)
    base = os.path.join(tmp, f"{voz}-{idx[0]:02d}-{len(idx)}")
    for n in range(TENTATIVAS):
        marcas = tts(texto, base + ".mp3", voz, cfg["rate"], cfg["pitch"])
        ok, lang, p = em_portugues(base + ".mp3")
        if ok:
            break
        print(f"  idioma errado ({lang}, pt={p:.2f}) tentativa {n + 1}: {texto}", flush=True)
    else:
        return None
    if len(idx) == 1:
        _recorta(base + ".mp3", base + "-a.wav")
        return [base + "-a.wav"]
    c = _corte(marcas, textos[idx[1]])
    if c is None:  # não achou o ponto de corte: sintetiza separado (cada um conferido)
        print("  sem marca de corte, separando:", texto, flush=True)
        out = []
        for i in idx:
            r = sintetiza_grupo(textos, [i], cfg, voz, tmp)
            if r is None:
                return None
            out += r
        return out
    _recorta(base + ".mp3", base + "-a.wav", fim=c)
    _recorta(base + ".mp3", base + "-b.wav", ini=c)
    return [base + "-a.wav", base + "-b.wav"]


def escolher_voz(r):
    v = (r.get("voz") or os.environ.get("CANDEIA_VOZ") or "feminina").lower()
    return "masculina" if v.startswith("mascul") or "antonio" in v else "feminina"


def narrar(roteiro, saida):
    r = json.load(open(roteiro, encoding="utf-8"))
    tipo = escolher_voz(r)
    cfg = VOZES[tipo]
    tmp = tempfile.mkdtemp()
    falas = [limpar(l) for l in r["linhas"]]
    cta = r.get("cta_falado") or limpar(r["cta"][0]) + "."
    textos = falas + [cta]
    grupos = agrupar(falas) + [[len(falas)]]

    def gerar_todas(voz):
        partes = []
        for g in grupos:
            res = sintetiza_grupo(textos, g, cfg, voz, tmp)
            if res is None:
                return None
            partes += res
        return partes

    voz_usada = cfg["voz"]
    partes = gerar_todas(voz_usada)
    if partes is None and cfg["reserva"]:
        print(f"  trocando a narração inteira para a voz de reserva {cfg['reserva']}", flush=True)
        voz_usada = cfg["reserva"]
        partes = gerar_todas(voz_usada)
    if partes is None:
        raise RuntimeError("narração não saiu em português após todas as tentativas")

    def silencio(seg, nome):
        p = os.path.join(tmp, nome)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                        "-t", f"{seg:.3f}", "-c:a", "pcm_s16le", p], check=True)
        return p

    # tira o silêncio do começo e do fim de cada frase: a fala começa colada e o respiro é sempre o mesmo
    aparadas = []
    filtro = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,"
              "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse")
    for k, p in enumerate(partes):
        q = os.path.join(tmp, f"ap-{k:02d}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af", filtro, "-ar", "24000", "-ac", "1", q],
                       check=True)
        aparadas.append(q if duracao(q) > 0.25 else p)

    lista, por_linha = [silencio(INTRO, "intro.wav")], []
    sp = silencio(PAUSA, "pausa.wav")
    for p in aparadas[:-1]:
        por_linha.append(round(duracao(p) + PAUSA, 3))
        lista += [p, sp]
    lista += [silencio(CTA_PAUSA, "pcta.wav"), aparadas[-1]]
    cat = os.path.join(tmp, "lista.txt")
    with open(cat, "w") as f:
        for p in lista:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", cat,
                    "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "160k", saida], check=True)
    tempos = {"intro": INTRO, "por_linha": por_linha, "cta_inicio": INTRO + sum(por_linha) + CTA_PAUSA,
              "cta_duracao": duracao(aparadas[-1]), "total": duracao(saida), "voz": voz_usada, "tipo_voz": tipo}
    json.dump(tempos, open(os.path.splitext(saida)[0] + ".json", "w"), indent=1)
    return tempos


if __name__ == "__main__":
    print(json.dumps(narrar(sys.argv[1], sys.argv[2]), indent=1))
