#!/usr/bin/env python3
"""Candeia Diária — gerador de vídeos 9:16.

Uso:
  python3 render.py roteiros/oracao-manha-01.json saida.mp4 [--fundo procedural|fotos:<pasta>] [--audio trilha.wav] [--narracao voz.mp3]

Cada linha do roteiro entra com fade + leve subida; palavras entre *asteriscos* ficam em dourado.
"""
import json, math, os, subprocess, sys, glob, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BASE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(BASE, "fonts")

CREME = (247, 238, 222)
OURO = (243, 196, 110)
SOMBRA = (10, 6, 3)

ESTILOS = {
    "montserrat": {"titulo": "Montserrat-ExtraBold.ttf", "titulo_tam": 84, "caixa_alta": True, "track": 6,
                   "texto": "Montserrat-SemiBold.ttf", "texto_tam": 66, "entre": 1.35,
                   "ref": "Montserrat-MediumItalic.ttf", "ref_tam": 40},
    "poppins": {"titulo": "Poppins-ExtraBold.ttf", "titulo_tam": 96, "caixa_alta": False, "track": 0,
                "texto": "Poppins-SemiBold.ttf", "texto_tam": 66, "entre": 1.30,
                "ref": "Poppins-MediumItalic.ttf", "ref_tam": 40},
    "classico": {"titulo": "GreatVibes.ttf", "titulo_tam": 150, "caixa_alta": False, "track": 0,
                 "texto": "EBGaramond-Bold.ttf", "texto_tam": 80, "entre": 1.22,
                 "ref": "EBGaramond-SemiBoldItalic.ttf", "ref_tam": 48},
}
ESTILO = ESTILOS[os.environ.get("CANDEIA_ESTILO", "montserrat")]
f_titulo = ImageFont.truetype(f"{FONT}/{ESTILO['titulo']}", ESTILO["titulo_tam"])
f_texto = ImageFont.truetype(f"{FONT}/{ESTILO['texto']}", ESTILO["texto_tam"])
f_ref = ImageFont.truetype(f"{FONT}/{ESTILO['ref']}", ESTILO["ref_tam"])
f_marca = ImageFont.truetype(f"{FONT}/Cinzel-SemiBold.ttf", 34)


# ---------------------------------------------------------------- fundo
class FundoProcedural:
    """Céu de amanhecer animado: gradiente, sol nascendo, raios, colinas, partículas."""

    def __init__(self, dur, seed=7):
        self.dur = dur
        self.w, self.h = W // 2, H // 2
        rng = np.random.default_rng(seed)
        y = np.linspace(0, 1, self.h)[:, None]
        x = np.linspace(0, 1, self.w)[None, :]
        self.x, self.y = x, y
        top = np.array([14, 12, 30]); mid = np.array([92, 48, 58]); hor = np.array([236, 140, 70])
        t = np.clip(y / 0.72, 0, 1)[..., None]
        sky = np.where(t < 0.6, top + (mid - top) * (t / 0.6), mid + (hor - mid) * ((t - 0.6) / 0.4))
        self.sky = np.broadcast_to(sky, (self.h, self.w, 3)).astype(np.float32)
        # colinas (duas camadas)
        xs = np.linspace(0, 1, self.w)
        h1 = 0.74 + 0.03 * np.sin(xs * 5.1 + 1.3) + 0.015 * np.sin(xs * 13 + 0.4)
        h2 = 0.80 + 0.025 * np.sin(xs * 3.3 + 2.1) + 0.012 * np.sin(xs * 17 + 1.7)
        self.m1 = np.clip((y - h1[None, :]) * self.h + 0.5, 0, 1).astype(np.float32)[..., None]
        self.m2 = np.clip((y - h2[None, :]) * self.h + 0.5, 0, 1).astype(np.float32)[..., None]
        # partículas
        n = 70
        self.px = rng.random(n); self.py = rng.random(n)
        self.ps = rng.uniform(1.0, 3.2, n); self.pv = rng.uniform(0.004, 0.012, n)
        self.pp = rng.random(n) * 6.28
        self.grain = [rng.normal(0, 5, (self.h, self.w, 1)).astype(np.float32) for _ in range(6)]
        vx = (x - 0.5) * 1.1; vy = (y - 0.48) * 0.9
        self.vig = np.clip(1 - (vx ** 2 + vy ** 2) * 1.4, 0.25, 1)[..., None].astype(np.float32)

    def frame(self, i):
        t = i / FPS
        p = t / self.dur
        sx, sy = 0.62, 0.745 - 0.06 * p          # sol sobe devagar
        x, y = self.x, self.y * (self.h / self.w)
        d = np.sqrt((x - sx) ** 2 + (y - sy * self.h / self.w) ** 2)
        glow = np.exp(-d * 5.0)[..., None] * np.array([255, 170, 90]) * (0.75 + 0.1 * p)
        core = np.exp(-(d / 0.035) ** 2)[..., None] * np.array([255, 240, 200])
        ang = np.arctan2(y - sy * self.h / self.w, x - sx)
        rays = (0.5 + 0.5 * np.sin(ang * 14 + t * 0.15)) ** 6 * np.exp(-d * 2.2)
        rays = rays[..., None] * np.array([255, 200, 140]) * 0.22
        img = self.sky + glow + core + rays
        hill1 = np.array([38, 22, 26]) * 1.0
        hill2 = np.array([16, 10, 12])
        img = img * (1 - self.m1) + (img * 0.15 + hill1) * self.m1
        img = img * (1 - self.m2) + hill2 * self.m2
        img = img * self.vig + self.grain[i % 6]
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        # partículas (em resolução cheia)
        dr = ImageDraw.Draw(im, "RGBA")
        for k in range(len(self.px)):
            py = (self.py[k] - self.pv[k] * t) % 1.0
            px = self.px[k] + 0.01 * math.sin(t * 0.6 + self.pp[k])
            a = int(110 * (0.5 + 0.5 * math.sin(t * 1.3 + self.pp[k])))
            r = self.ps[k] * 2
            cx, cy = px * W, py * H
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 214, 160, a))
        return im


def _grade_mask():
    y = np.linspace(-1, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
    vig = np.clip(1 - 0.35 * (x ** 2) - 0.30 * (y ** 2), 0.55, 1)
    centro = 1 - 0.22 * np.exp(-((y + 0.12) / 0.45) ** 2)   # escurece a faixa do texto
    return (vig * centro)[..., None].astype(np.float32)


_MASK = None


def gradear(arr):
    """Filtro quente, escurecido e com vinheta para o texto ficar legível."""
    global _MASK
    if _MASK is None:
        _MASK = _grade_mask()
    arr = arr.astype(np.float32) * np.array([1.06, 0.96, 0.84], dtype=np.float32) * 0.66 * _MASK
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


class FundoFotos:
    """Slideshow de fotos com zoom lento (Ken Burns) e crossfade."""

    def __init__(self, dur, pasta, por_foto=5.5, fade=1.1):
        fotos = sorted(glob.glob(os.path.join(pasta, "*.jp*g")) + glob.glob(os.path.join(pasta, "*.png")))
        assert fotos, f"nenhuma foto em {pasta}"
        self.dur, self.por, self.fade = dur, por_foto, fade
        self.passo = por_foto - fade
        n = int(math.ceil(dur / self.passo)) + 1
        self.imgs = []
        for k in range(n):
            im = Image.open(fotos[k % len(fotos)]).convert("RGB")
            s = max(W * 1.15 / im.width, H * 1.15 / im.height)
            im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
            self.imgs.append(im)

    def _quadro(self, k, local):
        im = self.imgs[k]
        p = min(1.0, local / self.por)
        z = 1.0 + 0.10 * (p if k % 2 == 0 else 1 - p)
        cw, ch = W * 1.15 / z, H * 1.15 / z
        dx = (im.width - cw) / 2 + (im.width - cw) * 0.35 * (p - 0.5) * (1 if k % 3 else -1)
        dy = (im.height - ch) / 2
        return im.crop((dx, dy, dx + cw, dy + ch)).resize((W, H), Image.BICUBIC)

    def frame(self, i):
        t = i / FPS
        k = min(int(t // self.passo), len(self.imgs) - 1)
        local = t - k * self.passo
        a = self._quadro(k, local)
        if k > 0 and local < self.fade:
            prev = self._quadro(k - 1, local + self.passo)
            a = Image.blend(prev, a, local / self.fade)
        return gradear(np.asarray(a))


class _Leitor:
    def __init__(self, arquivo, seg):
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
              f"setpts=PTS*1.15")  # levemente mais lento: sensação contemplativa
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-stream_loop", "-1", "-i", arquivo,
                                   "-t", f"{seg + 1:.2f}", "-vf", vf, "-an", "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.ult = np.zeros((H, W, 3), np.uint8)

    def proximo(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self.ult = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        return self.ult

    def fechar(self):
        try:
            self.p.stdout.close(); self.p.kill()
        except Exception:
            pass


class FundoVideos:
    """Sequência de clipes recortados para 9:16, com crossfade."""

    def __init__(self, dur, pasta, seg=6.5, fade=1.0):
        self.clips = sorted(glob.glob(os.path.join(pasta, "*.mp4")))
        assert self.clips, f"nenhum vídeo em {pasta}"
        self.seg, self.fade, self.passo = seg, fade, seg - fade
        self.ativos = {}

    def _leitor(self, k):
        if k not in self.ativos:
            self.ativos[k] = _Leitor(self.clips[k % len(self.clips)], self.seg)
        return self.ativos[k]

    def frame(self, i):
        t = i / FPS
        k = int(t // self.passo)
        local = t - k * self.passo
        a = self._leitor(k).proximo().astype(np.float32)
        if k > 0 and local < self.fade and (k - 1) in self.ativos:
            b = self.ativos[k - 1].proximo().astype(np.float32)
            al = local / self.fade
            a = b * (1 - al) + a * al
        elif (k - 1) in self.ativos:
            self.ativos.pop(k - 1).fechar()
        return gradear(a)


# ---------------------------------------------------------------- texto
PONT = set(".,;:!?…)»\"'")


def tokens(linha):
    """Lista de palavras; cada palavra é uma lista de pedaços (texto, destacado). Pontuação cola na palavra anterior."""
    out, dest = [], False
    for parte in linha.split("*"):
        for j, w in enumerate(parte.split(" ")):
            if not w:
                continue
            colado = j == 0 and out and not parte.startswith(" ") and all(c in PONT for c in w)
            if colado:
                out[-1].append((w, dest))
            else:
                out.append([(w, dest)])
        dest = not dest
    return out


def _larg(fonte, w, track):
    return fonte.getlength(w) + track * max(0, len(w) - 1)


def _escreve(draw, xy, w, fonte, fill, track):
    if not track:
        draw.text(xy, w, font=fonte, fill=fill); return
    x, y = xy
    for ch in w:
        draw.text((x, y), ch, font=fonte, fill=fill)
        x += fonte.getlength(ch) + track


def camada_texto(linha, fonte, largura=900, entre=None, track=0):
    entre = entre or ESTILO["entre"]
    """Renderiza uma frase (quebrada e centralizada) numa camada RGBA com sombra e brilho."""
    toks = tokens(linha)
    esp = fonte.getlength(" ")
    linhas, atual, wa = [], [], 0
    for pedacos in toks:
        lw = sum(_larg(fonte, w, track) for w, _ in pedacos)
        if atual and wa + esp + lw > largura:
            linhas.append(atual); atual, wa = [], 0
        wa += (esp if atual else 0) + lw
        atual.append((pedacos, lw))
    if atual:
        linhas.append(atual)
    asc, desc = fonte.getmetrics()
    lh = int((asc + desc) * entre)
    ch = lh * len(linhas) + 80
    cw = largura + 120
    txt = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    glow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dt, dg = ImageDraw.Draw(txt), ImageDraw.Draw(glow)
    y = 40
    for ln in linhas:
        tot = sum(l for _, l in ln) + esp * (len(ln) - 1)
        x = (cw - tot) / 2
        for pedacos, lw in ln:
            for w, d in pedacos:
                _escreve(dt, (x, y), w, fonte, (OURO if d else CREME) + (255,), track)
                if d:
                    _escreve(dg, (x, y), w, fonte, (255, 170, 70, 220), track)
                x += _larg(fonte, w, track)
            x += esp
        y += lh
    sombra = Image.new("RGBA", (cw, ch), SOMBRA + (0,))
    sombra.putalpha(txt.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, v * 1.6)))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    out.alpha_composite(sombra); out.alpha_composite(glow); out.alpha_composite(txt)
    return out


def cola(base, camada, cx, cy, alpha):
    if alpha <= 0.002:
        return
    c = camada
    if alpha < 0.999:
        c = camada.copy()
        c.putalpha(camada.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- montagem
def montar(roteiro, saida, fundo_spec="procedural", audio=None, narracao=None, por_linha=None):
    r = json.load(open(roteiro, encoding="utf-8"))
    linhas = r["linhas"]
    intro, t_cta = 1.8, 4.5
    tempos_voz = None
    if narracao:
        tj = os.path.splitext(narracao)[0] + ".json"
        if os.path.exists(tj):
            tempos_voz = json.load(open(tj))
            intro = tempos_voz["intro"]
            por_linha = tempos_voz["por_linha"]
            t_cta = max(4.5, tempos_voz["cta_duracao"] + 3.0)
    if por_linha is None:
        por_linha = [max(3.2, 1.6 + 0.075 * len(l.replace("*", ""))) for l in linhas]
    inicios, t = [], intro
    for d in por_linha:
        inicios.append(t); t += d
    t_cta0 = t
    dur = t + t_cta
    nframes = int(dur * FPS)

    if fundo_spec.startswith("fotos:"):
        fundo = FundoFotos(dur, fundo_spec[6:])
    elif fundo_spec.startswith("videos:"):
        fundo = FundoVideos(dur, fundo_spec[7:])
    else:
        fundo = FundoProcedural(dur)

    titulo = r["serie"].upper() if ESTILO["caixa_alta"] else r["serie"]
    tam, tr = ESTILO["titulo_tam"], ESTILO["track"]
    minimo = int(ESTILO["titulo_tam"] * 0.82)   # abaixo disso, quebra em duas linhas
    while tam > minimo and _larg(ImageFont.truetype(f"{FONT}/{ESTILO['titulo']}", tam), titulo, tr) > 940:
        tam -= 4
    cam_titulo = camada_texto(titulo, ImageFont.truetype(f"{FONT}/{ESTILO['titulo']}", tam), largura=940, entre=1.12, track=tr)
    cams = [camada_texto(l, f_texto) for l in linhas]
    ref = r.get("referencia")
    cam_ref = camada_texto(ref["texto"], f_ref) if ref else None
    cams_cta = [camada_texto(c, f_texto if k == 0 else f_ref) for k, c in enumerate(r["cta"])]
    marca = Image.new("RGBA", (600, 70), (0, 0, 0, 0))
    ImageDraw.Draw(marca).text((300, 35), "@candeiadiaria", font=f_marca, fill=(243, 208, 143, 190), anchor="mm")
    lamp = Image.open(os.path.join(BASE, "perfil.png")).convert("RGBA").resize((150, 150), Image.LANCZOS)
    mask = Image.new("L", (150, 150), 0); ImageDraw.Draw(mask).ellipse([0, 0, 149, 149], fill=255)
    lamp.putalpha(mask)

    tmp = saida + ".video.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "27", "-maxrate", "4M", "-bufsize", "8M", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    fd = 0.55
    for i in range(nframes):
        t = i / FPS
        im = fundo.frame(i).convert("RGBA")
        a_tit = ease(t / 1.2) * (1 - ease((t - t_cta0 + 0.2) / 0.6))
        cola(im, cam_titulo, W / 2, 300 + cam_titulo.height / 2 - 60, a_tit)
        for k, (cam, t0) in enumerate(zip(cams, inicios)):
            t1 = t0 + por_linha[k]
            if t0 - 0.1 <= t <= t1 + 0.1:
                a = ease((t - t0) / fd) * (1 - ease((t - (t1 - fd)) / fd))
                dy = 24 * (1 - ease((t - t0) / (fd * 1.4)))
                cola(im, cam, W / 2, H * 0.43 + dy, a)
                if ref and ref["linha"] == k:
                    cola(im, cam_ref, W / 2, H * 0.43 + cam.height / 2 + 30, a * 0.9)
        if t >= t_cta0 - 0.1:
            a = ease((t - t_cta0) / 0.7)
            cola(im, lamp, W / 2, H * 0.36, a)
            cola(im, cams_cta[0], W / 2, H * 0.50, a)
            if len(cams_cta) > 1:
                cola(im, cams_cta[1], W / 2, H * 0.50 + cams_cta[0].height / 2 + cams_cta[1].height / 2 - 20, ease((t - t_cta0 - 0.6) / 0.7))
        cola(im, marca, W / 2, H - 170, 1.0)
        ff.stdin.write(im.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()

    # áudio
    ins, filt = ["-i", tmp], []
    if audio:
        ins += ["-stream_loop", "-1", "-i", audio]
    if narracao:
        ins += ["-i", narracao]
    if audio and narracao:
        filt = ["-filter_complex",
                f"[1:a]volume=0.20,afade=t=in:d=1.5,afade=t=out:st={dur-2.5:.2f}:d=2.5[m];"
                f"[2:a]aresample=44100,volume=1.0,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,apad[v];"
                f"[m][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                "-map", "0:v", "-map", "[a]"]
    elif audio:
        filt = ["-filter_complex", f"[1:a]volume=0.8,afade=t=in:d=1.5,afade=t=out:st={dur-2.5:.2f}:d=2.5[a]", "-map", "0:v", "-map", "[a]"]
    if audio or narracao:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, *filt, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{dur:.2f}", saida], check=True)
        os.remove(tmp)
    else:
        os.replace(tmp, saida)
    return dur


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("roteiro"); ap.add_argument("saida")
    ap.add_argument("--fundo", default="procedural")
    ap.add_argument("--audio"); ap.add_argument("--narracao")
    a = ap.parse_args()
    d = montar(a.roteiro, a.saida, a.fundo, a.audio, a.narracao)
    print(f"ok {a.saida} ({d:.1f}s)")
