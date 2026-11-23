import json
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe("/tmp/voz.wav", language="pt", word_timestamps=True, vad_filter=False, beam_size=5)
out = []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text, "words": [{"w": w.word, "s": w.start, "e": w.end} for w in s.words]})
json.dump(out, open("narracao-ecotacoes/transcricao.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(out))
