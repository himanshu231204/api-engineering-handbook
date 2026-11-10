import json, hashlib, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from script_lines import B
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
k = Kokoro(f"{ROOT}/models/kokoro-v1.0.onnx", f"{ROOT}/models/voices-v1.0.bin")
SPEED = 1.0
SR = 24000
os.makedirs("cache", exist_ok=True)
def trim(s, thr=0.01):
    idx = np.where(np.abs(s) > thr)[0]
    if len(idx)==0: return s
    a = max(0, idx[0]-int(0.02*SR)); b = min(len(s), idx[-1]+int(0.05*SR))
    return s[a:b]
def gen(say):
    h = hashlib.md5(f"{say}|{SPEED}".encode()).hexdigest()
    p = f"cache/{h}.npy"
    if os.path.exists(p): return np.load(p)
    s, sr = k.create(say, voice="am_michael", speed=SPEED, lang="en-us")
    assert sr == SR
    s = trim(s); np.save(p, s); return s
t = 0.25
out = [np.zeros(int(0.25*SR), dtype=np.float32)]
lines = []
for i, ln in enumerate(B):
    s = gen(ln["say"]).astype(np.float32)
    d = len(s)/SR
    nxt = B[i+1] if i+1 < len(B) else None
    if nxt is None: gap = 0.6
    elif nxt["ch"] != ln["ch"] and ln["beat"] != nxt["beat"]: gap = 2.0   # chapter boundary: room for the chapter card
    elif nxt["beat"] != ln["beat"]: gap = 0.45
    else: gap = 0.24
    lines.append({**ln, "start": round(t,3), "end": round(t+d,3), "gap": gap})
    out += [s, np.zeros(int(gap*SR), dtype=np.float32)]
    t += d + gap
    print(i, round(t,1), flush=True)
audio = np.concatenate(out)
audio = audio/np.max(np.abs(audio))*0.95
sf.write("voice.wav", audio, SR)
json.dump({"total": round(len(audio)/SR,3), "lines": lines}, open("timing_raw.json","w"), indent=1)
print("TOTAL", len(audio)/SR)
