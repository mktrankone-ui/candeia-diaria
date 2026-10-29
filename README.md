# Candeia Diária

Gerador de vídeos 9:16 de oração para Instagram e TikTok (@candeiadiaria).

## Estrutura

- `render.py` — monta o vídeo: fundo animado (ou fotos), texto frase a frase com palavra em destaque, marca d'água, trilha e narração opcional
- `roteiros/` — um JSON por vídeo (série, linhas, referência bíblica, CTA, legenda)
- `trilhas/` — trilhas instrumentais livres de direitos
- `fonts/` — Great Vibes, EB Garamond e Cinzel (todas OFL)
- `marca/` — logo e foto de perfil

## Uso

```bash
python3 render.py roteiros/oracao-manha-01.json saida/oracao-manha-01.mp4 --audio trilhas/ambiente-01.mp3
# fundo com fotos:
python3 render.py roteiros/oracao-manha-01.json saida/x.mp4 --fundo fotos:pasta_de_fotos --audio trilhas/ambiente-01.mp3
```

Nos roteiros, palavras entre `*asteriscos*` ficam em dourado.

## Publicação

Os vídeos finais são anexados como arquivos de Release (não ficam no código) e o link direto vai para o agendamento no Metricool.

Chaves de API (Pixabay, voz) ficam em **Settings → Secrets and variables → Actions**, nunca no código.
