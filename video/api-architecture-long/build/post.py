import json, re, os
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
T = json.load(open("timing.json")); SC = json.load(open("scenes.json"))
FIX = {"d1": "Request one, a simple read: GET /products/9. It hits the CDN first.", "w1": "Request two, a write: POST /orders. This is the handbook's end to end view of it.",
       "z1": "Quick check before you go. A POST /orders request must also send a confirmation email. How do you avoid making the client wait for it?",
       "p2": "Or try the chapter's exercise: the layers a GET /orders/{id} request passes through, in a food delivery app.",
       "g1": "Zoom in on the gateway: one front door, one address for web, mobile and partner clients."}
def clean(k, s):
    if k in FIX: return FIX[k]
    for a, b in [("Fast A P I", "FastAPI"), ("A P I", "API"), ("C D N", "CDN"), ("L L M", "LLM"), ("C R U D", "CRUD"), ("Post gress Q L", "PostgreSQL"), ("Red iss", "Redis"),
                 ("four zero one", "401"), ("four twenty nine", "429"), ("two hundred one", "201"), ("Parts fourteen to seventeen", "Parts 14 to 17"), ("Part eleven", "Part 11"),
                 ("Part eighteen", "Part 18"), ("twenty to one hundred fifty milliseconds", "20 to 150 milliseconds"), ("one millisecond", "1 millisecond"), ("all twenty parts", "all 20 parts")]:
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
chap = [("00:00", "Intro: API architecture at a glance")] + [(mmss(cards[c]["start"]), CHAPTERS[c] if c < 6 else "Recap, quiz and what's next") for c in range(1, 7)]
json.dump(chap, open("chapters.json", "w"))
md = ["# Script — API Architecture at a Glance (long)", "", f"Runtime {mmss(T['total'])}. Chapters:", ""] + [f"- {t} {n}" for t, n in chap] + [""]
cur = None
for ln in T["lines"]:
    if ln["ch"] != cur:
        cur = ln["ch"]; md += ["", f"## {CHAPTERS[cur]}", ""]
    md.append(f"- **{mmss(ln['start'])}** {clean(ln['key'], ln['say'])}")
open(ROOT + "/script.md", "w").write("\n".join(md) + "\n")
print(chap)
