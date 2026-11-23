import json, wave
import numpy as np
from faster_whisper import WhisperModel
with wave.open("/tmp/voz.wav") as w:
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe(audio, language="pt", word_timestamps=True, vad_filter=False, beam_size=5)
out = [{"start": s.start, "end": s.end, "text": s.text, "words": [{"w": x.word, "s": x.start, "e": x.end} for x in s.words]} for s in segs]
json.dump(out, open("narracao-ecotacoes/transcricao.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(out))
