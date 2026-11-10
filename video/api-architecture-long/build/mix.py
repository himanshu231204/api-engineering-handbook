import json, numpy as np, soundfile as sf
SR = 24000
voice, sr = sf.read("voice.wav", dtype="float32"); assert sr == SR
sfx = json.load(open("sfx.json"))
rng = np.random.default_rng(7)
n = len(voice); out = np.zeros(n + SR, dtype=np.float32)
def env(L, a=.005, d=.15):
    t = np.arange(L)/SR; return np.minimum(t/a, 1) * np.exp(-t/d)
def whoosh():
    L = int(.38*SR); x = rng.standard_normal(L).astype(np.float32)
    # band sweep via moving average of varying width (cheap)
    y = np.convolve(x, np.ones(40)/40, mode="same") - np.convolve(x, np.ones(400)/400, mode="same")
    e = np.sin(np.linspace(0, np.pi, L))**2
    return y*e*0.9
def thunk():
    L = int(.3*SR); t = np.arange(L)/SR
    return np.sin(2*np.pi*(90 - 40*t/0.3)*t)*env(L, .002, .09)*1.2
def pop():
    L = int(.12*SR); t = np.arange(L)/SR
    return np.sin(2*np.pi*(520+900*t)*t)*env(L, .002, .03)
def tick():
    L = int(.04*SR); x = rng.standard_normal(L).astype(np.float32)
    return x*env(L, .001, .008)*0.6
def shutter():
    L = int(.14*SR); x = rng.standard_normal(L).astype(np.float32)
    return (x*env(L, .001, .02) + np.roll(x, 900)*env(L, .001, .02)*0.5)*0.6
G = {"whoosh": (whoosh, .10), "thunk": (thunk, .16), "pop": (pop, .07), "tick": (tick, .06), "shutter": (shutter, .08)}
last = {}
vp = np.max(np.abs(voice))
for t, k in sfx:
    if k not in G: continue
    if t - last.get(k, -9) < (0.15 if k in ("pop", "tick") else 0.4): continue
    last[k] = t
    f, g = G[k]; s = f().astype(np.float32); s = s/np.max(np.abs(s)) * g
    i = int(t*SR)
    if i + len(s) < len(out): out[i:i+len(s)] += s
mix = voice + out[:n]
fade = int(.6*SR); mix[-fade:] *= np.linspace(1, 0, fade)
mix = mix/np.max(np.abs(mix))*0.84   # ~ -1.5 dB
sf.write("../hf/assets/mix.wav", mix, SR)
print("mixed", n/SR, "s; sfx events:", len(sfx))
