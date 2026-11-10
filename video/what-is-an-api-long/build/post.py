import json, re, os
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
T = json.load(open("timing.json")); SC = json.load(open("scenes.json"))
FIX = {"e1": "Here's a real request. GET /users/42.", "i2": "One decorator maps GET /users/{user_id} to a Python function.",
       "o2": "Before you go, try the chapter's exercise: add a GET /users endpoint, and decide what it should return when the database is empty."}
def clean(k, s):
    if k in FIX: return FIX[k]
    for a, b in [("A P I", "API"), ("Post gress Q L", "PostgreSQL"), ("Mongo D B", "MongoDB"), ("M D N", "MDN"), ("four zero four", "404"), ("four twenty two", "422"),
                 ("forty-two", "42"), ("Two hundreds", "2xx"), ("Four hundreds", "4xx"), ("Five hundreds", "5xx"), ("Two hundred", "200"), ("two hundred", "200")]:
        s = s.replace(a, b)
    return s
def ts(t):
    h, m = int(t // 3600), int(t % 3600 // 60); sec = t % 60
    return f"{h:02d}:{m:02d}:{int(sec):02d},{int(round((sec % 1) * 1000)):03d}".replace("1000", "999")
import math, textwrap
MAXW, MINDUR = 42, 1.0     # chars per caption line, seconds on screen per cue
cues = []
for ln in T["lines"]:
    text = clean(ln["key"], ln["say"])
    n = max(1, math.ceil(len(text) / (2 * MAXW)))              # cues needed at two lines each
    width = min(MAXW, math.ceil(len(text) / (2 * n)) + 6)      # balanced lines, so no one-word tail cue
    lines = textwrap.wrap(text, width=width)
    while len(lines) > 2 * n and width < MAXW:                 # widen until it fits, but never past 42 chars
        width += 1; lines = textwrap.wrap(text, width=width)
    chunks = ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]
    tot = sum(len(c) for c in chunks); t0 = ln["start"]; d = ln["end"] - ln["start"]
    durs = [max(d * len(c) / tot, min(MINDUR, d)) for c in chunks]
    scale = d / sum(durs); durs = [x * scale for x in durs]
    for c, dd in zip(chunks, durs):
        cues.append((t0, t0 + dd, c)); t0 += dd
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
