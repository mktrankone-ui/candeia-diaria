#!/usr/bin/env python3
"""Gera a narração de um roteiro, frase a frase, e devolve os tempos de cada linha.

Uso: python3 narrar.py roteiros/x.json saida/x-voz.mp3  → grava também saida/x-voz.json com os tempos

Vozes (campo "voz" do roteiro): "feminina" (Thalita) ou "masculina" (Antonio).
Toda frase é conferida com o Whisper: se não sair em português, é refeita; se insistir,
a narração inteira passa para a voz de reserva (monolíngue, não troca de idioma).
"""
import asyncio, json, os, subprocess, sys, tempfile

VOZES = {
    # Thalita é "multilingual": sem dica de idioma ela pode ler uma frase curta em francês/espanhol.
    "feminina": {"voz": "pt-BR-ThalitaMultilingualNeural", "rate": "-12%", "pitch": "-2Hz",
                 "reserva": "pt-BR-FranciscaNeural"},
    # Antonio é monolíngue pt-BR. Mais lento e mais grave: voz grossa e suave.
    "masculina": {"voz": "pt-BR-AntonioNeural", "rate": "-14%", "pitch": "-9Hz", "reserva": None},
}
INTRO = 0.15     # a voz entra já no primeiro segundo (gancho falado imediatamente)
PAUSA = 0.70     # respiro depois de cada frase
CTA_PAUSA = 0.5
TENTATIVAS = 3


def duracao(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


_ORIGINAL = None
FORCAR_PT = True


def _ssml(forcar):
    """Faz o edge-tts declarar pt-BR no SSML (o padrão é en-US, o que deixa a voz multilíngue 'adivinhar')."""
    global _ORIGINAL
    from edge_tts import communicate as c
    if _ORIGINAL is None:
        _ORIGINAL = c.mkssml
    if not forcar:
        c.mkssml = _ORIGINAL
        return
    def mkssml(tc, escaped_text):
        if isinstance(escaped_text, bytes):
            escaped_text = escaped_text.decode("utf-8")
        return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='pt-BR'>"
                f"<voice name='{tc.voice}'><lang xml:lang='pt-BR'>"
                f"<prosody pitch='{tc.pitch}' rate='{tc.rate}' volume='{tc.volume}'>{escaped_text}</prosody>"
                "</lang></voice></speak>")
    c.mkssml = mkssml


async def _tts(texto, destino, voz, rate, pitch):
    import edge_tts
    await edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch).save(destino)


def tts(texto, destino, voz, rate, pitch):
    global FORCAR_PT
    if os.path.exists(destino):
        os.remove(destino)
    try:
        _ssml(FORCAR_PT)
        asyncio.run(_tts(texto, destino, voz, rate, pitch))
    except Exception as e:
        if not FORCAR_PT:
            raise
        # o serviço recusou o SSML com <lang>: segue no padrão (o Whisper confere o idioma de cada frase)
        print("AVISO: pt-BR forçado no SSML recusado, usando padrão:", e, flush=True)
        FORCAR_PT = False
        _ssml(False)
        asyncio.run(_tts(texto, destino, voz, rate, pitch))
    if not os.path.exists(destino) or os.path.getsize(destino) < 2000:
        raise RuntimeError(f"áudio vazio para: {texto}")


# ---------------------------------------------------------------- conferência de idioma
_MODELO = None


def _modelo():
    global _MODELO
    if _MODELO is None:
        from faster_whisper import WhisperModel
        _MODELO = WhisperModel(os.environ.get("CANDEIA_WHISPER", "small"), device="cpu", compute_type="int8")
    return _MODELO


def idioma(arquivo):
    """Devolve (idioma, probabilidade de português). Sem Whisper instalado devolve ('?', 1.0)."""
    try:
        m = _modelo()
    except Exception as e:
        print("AVISO: Whisper indisponível, idioma não conferido:", e, flush=True)
        return "?", 1.0
    _, info = m.transcribe(arquivo, beam_size=1, without_timestamps=True)
    probs = dict(info.all_language_probs or [])
    return info.language, probs.get("pt", 1.0 if info.language == "pt" else 0.0)


def em_portugues(arquivo):
    lang, p = idioma(arquivo)
    ok = lang in ("pt", "?") and p >= 0.5
    return ok, lang, p


def frase_ok(texto, destino, cfg, voz):
    for n in range(TENTATIVAS):
        tts(texto, destino, voz, cfg["rate"], cfg["pitch"])
        ok, lang, p = em_portugues(destino)
        if ok:
            return True
        print(f"  idioma errado ({lang}, pt={p:.2f}) tentativa {n + 1}: {texto}", flush=True)
    return False


# ---------------------------------------------------------------- montagem
def limpar(t):
    return t.replace("*", "").strip()


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

    def gerar_todas(voz):
        partes = []
        for k, f in enumerate(textos):
            p = os.path.join(tmp, f"{voz}-{k:02d}.mp3")
            if not frase_ok(f, p, cfg, voz):
                return None
            partes.append(p)
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

    # corta o silêncio que o TTS deixa no começo de cada frase (deixa a fala colada no início)
    aparadas = []
    for k, p in enumerate(partes):
        q = os.path.join(tmp, f"ap-{k:02d}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02",
                        "-ar", "24000", "-ac", "1", q], check=True)
        if duracao(q) < 0.3:  # filtro comeu demais: usa a frase inteira
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ar", "24000", "-ac", "1", q], check=True)
        aparadas.append(q)

    lista, por_linha = [silencio(INTRO, "intro.wav")], []
    sp = silencio(PAUSA, "pausa.wav")
    for p in aparadas[:-1]:
        d = duracao(p)
        por_linha.append(round(d + PAUSA, 3))
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
