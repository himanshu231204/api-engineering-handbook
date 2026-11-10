import json, re, os
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
T = json.load(open("timing.json")); SC = json.load(open("scenes.json"))
FIX = {"e1": "Here's a real request. GET /users/42.", "i2": "One decorator maps GET /users/{user_id} to a Python function.",
       "o2": "Before you go, try the chapter's exercise: add a GET /users endpoint, and decide what it should return when the database is empty."}
def clean(k, s):
    if k in FIX: return FIX[k]
    for a, b in [("A P I", "API"), ("Post gress Q L", "PostgreSQL"), ("Mongo D B", "MongoDB"), ("M D N", "MDN"), ("four zero four", "404"), ("four twenty two", "422"),
                 ("forty-two", "42"), ("Two hundred", "200"), ("two hundred", "200"), ("Two hundreds", "2xx"), ("Four hundreds", "4xx"), ("Five hundreds", "5xx")]:
        s = s.replace(a, b)
    return s
def ts(t):
    h, m = int(t // 3600), int(t % 3600 // 60); sec = t % 60
    return f"{h:02d}:{m:02d}:{int(sec):02d},{int(round((sec % 1) * 1000)):03d}".replace("1000", "999")
cues = []
for ln in T["lines"]:
    text = clean(ln["key"], ln["say"])
    words = text.split()
    chunks, cur = [], []
    for w in words:
        if len(" ".join(cur + [w])) > 80 and cur: chunks.append(cur); cur = []
        cur.append(w)
    if cur: chunks.append(cur)
    tot = sum(len(" ".join(c)) for c in chunks); t0 = ln["start"]; d = ln["end"] - ln["start"]
    for c in chunks:
        s = " ".join(c); dd = d * len(s) / tot
        # wrap to 2 lines of <= 42 chars
        if len(s) > 42:
            mid = s.rfind(" ", 0, 43); s = s[:mid] + "\n" + s[mid + 1:]
        cues.append((t0, t0 + dd, s)); t0 += dd
with open(ROOT + "/captions.srt", "w") as f:
    for i, (a, b, s) in enumerate(cues, 1): f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{s}\n\n")
print("srt cues", len(cues))

# script.json (one object per line)
beat_info = {s["id"]: s for s in SC if not s.get("card")}
out, seen = [], set()
for ln in T["lines"]:
    o = {"say": clean(ln["key"], ln["say"]), "cap": ln["cap"], "chapter": f'{ln["ch"]} · {ln["beat"]}' if False else ln["ch"], "beat": ln["beat"]}
    if ln["beat"] not in seen:
        seen.add(ln["beat"]); b = beat_info[ln["beat"]]
        o.update(scene=b["kind"], pill=b["pill"], asset=b["assets"])
    o["start"] = round(ln["start"], 2); o["end"] = round(ln["end"], 2)
    out.append(o)
json.dump(out, open(ROOT + "/script.json", "w"), indent=1, ensure_ascii=False)

# script.md + chapters
from script_lines import CHAPTERS
cards = {s["chapter"]: s for s in SC if s.get("card")}
def mmss(t): return f"{int(t // 60):02d}:{int(t % 60):02d}"
chap = [("00:00", "Intro: what is an API?")] + [(mmss(cards[c]["start"]), CHAPTERS[c] if c < 6 else "Recap and what's next") for c in range(1, 7)]
json.dump(chap, open("chapters.json", "w"))
md = ["# Script — What Is an API? (long)", "", f"Runtime {mmss(T['total'])}. Chapters:", ""] + [f"- {t} {n}" for t, n in chap] + [""]
cur = None
for ln in T["lines"]:
    if ln["ch"] != cur:
        cur = ln["ch"]; md += ["", f"## {CHAPTERS[cur]}", ""]
    md.append(f"- **{mmss(ln['start'])}** {clean(ln['key'], ln['say'])}")
open(ROOT + "/script.md", "w").write("\n".join(md) + "\n")
print(chap)
