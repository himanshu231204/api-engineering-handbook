import json, re, numpy as np, soundfile as sf
from faster_whisper import WhisperModel
T = json.load(open("timing_raw.json"))
audio, sr = sf.read("voice16.wav", dtype="float32")
m = WhisperModel("base.en", device="cpu", compute_type="int8")
def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())
bad = []
for ln in T["lines"]:
    a, b = int((ln["start"]-0.05)*sr), int((ln["end"]+0.05)*sr)
    clip = audio[max(a,0):b]
    segs, _ = m.transcribe(clip, word_timestamps=True, language="en", beam_size=1)
    words = []
    for s in segs:
        for w in s.words:
            words.append({"w": w.word.strip(), "start": round(ln["start"]-0.05+w.start,3), "end": round(ln["start"]-0.05+w.end,3)})
    ln["words"] = words
    heard = " ".join(w["w"] for w in words)
    ln["heard"] = heard
    print(ln["key"], "|", heard, flush=True)
json.dump(T, open("timing.json","w"), indent=1)
