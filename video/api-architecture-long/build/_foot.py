# ---------- chapter cards ----------
for ci, c in enumerate(CARDS):
    sid = f"card{c['ch']}"
    S = Scene(sid, [], "chapter_card", c["start"], c["end"], c["ch"])
    ch = c["ch"]
    if ch <= 5:
        S.text(f"CHAPTER {ch}", 0, 330, 1920, size=96, color=YEL, align="center", t=0.05, anim="slam", style="font-family:'Caveat';font-weight:700;")
        S.text(CHAPTERS[ch], 0, 450, 1920, size=120, align="center", t=0.15)
        dots = "".join(f'<span style="display:inline-block;width:{44 if i == ch else 20}px;height:20px;border-radius:10px;background:{YEL if i == ch else "#2A2A2A"};margin:0 8px"></span>' for i in range(1, 6))
        S.el(dots, 0, 640, 1920, style="text-align:center", anim="fade", t=0.2)
    else:
        S.text("RECAP", 0, 400, 1920, size=140, color=YEL, align="center", t=0.05, anim="slam")
    SFX.append((S.start + 0.05, "thunk")); SFX.append((S.start, "whoosh"))
    S.write()
    SCENES[-1]["card"] = True

# whoosh on beat changes (not first)
for sdef in SCENES:
    if sdef["id"] not in ("hook",) and not sdef.get("card"): SFX.append((sdef["start"], "whoosh"))

# ---------- HUD (progress bar + chapter title) ----------
hud_ticks = ""
card_windows = [(c["start"], c["end"]) for c in CARDS]
ch_starts = {}
for bid, info in BEAT_INFO.items():
    ch_starts.setdefault(info["ch"], info["start"])
for ch in range(1, 7): hud_ticks += f'<div class="tick" style="left:{20 + 1880 * (ch_starts[ch] / TOTAL):.1f}px"></div>'
hud_titles = "".join(f'<div id="hud-t{ch}" class="ht">{CHAPTERS[ch] if ch else ""}</div>' for ch in range(0, 7))
hud_js = [f'tl.fromTo("#hud-fill",{{scaleX:0}},{{scaleX:1,duration:{TOTAL},ease:"none"}},0);']
chap_bounds = sorted(ch_starts.items())
for ch in range(1, 7):
    st = ch_starts[ch]; en = ch_starts[ch + 1] if ch + 1 in ch_starts else TOTAL
    hud_js.append(f'tl.fromTo("#hud-t{ch}",{{opacity:0}},{{opacity:1,duration:.2}},{st + 0.5:.2f});')
    hud_js.append(f'tl.fromTo("#hud-t{ch}",{{opacity:1}},{{opacity:0,duration:.15,immediateRender:false}},{en - 0.3:.2f});')
for (a, b) in card_windows:
    hud_js.append(f'tl.fromTo("#hud-bar",{{opacity:1}},{{opacity:0,duration:.15,immediateRender:false}},{a:.2f});')
    hud_js.append(f'tl.fromTo("#hud-bar",{{opacity:0}},{{opacity:1,duration:.2,immediateRender:false}},{b:.2f});')
open(f"{HF}/compositions/hud.html", "w").write(f"""<template>
<style>
#root{{position:absolute;inset:0;font-family:'Inter',sans-serif}}
#hud-bar{{position:absolute;left:0;top:0;width:1920px;height:80px}}
#hud-track{{position:absolute;left:20px;top:8px;width:1880px;height:4px;background:#1A1A1A}}
#hud-fill{{position:absolute;left:20px;top:8px;width:1880px;height:4px;background:#FFE500;transform-origin:0 50%}}
.tick{{position:absolute;top:2px;width:3px;height:16px;background:#666}}
.ht{{position:absolute;left:24px;top:26px;font-size:28px;font-weight:700;color:#A0A0B0;opacity:0}}
</style>
<div id="root" data-composition-id="hud" data-width="1920" data-height="1080">
<div id="hud-bar"><div id="hud-track"></div><div id="hud-fill"></div>{hud_ticks}{hud_titles}</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(hud_js)}
window.__timelines = window.__timelines || {{}};
window.__timelines["hud"] = tl;
</script>
</div>
</template>
""")

# ---------- captions ----------
cap_html, cap_js = [], []
for ln in T["lines"]:
    cap = ln["cap"]
    toks = re.findall(r"\[[^\]]+\]|[^\s\[\]]+(?:\s*(?=\[)|)", cap)
    # build word list with keyword flags
    words = []
    for m in re.finditer(r"\[([^\]]+)\](\S*)|(\S+)", cap):
        if m.group(1):
            kws = m.group(1).split()
            kws[-1] += m.group(2) or ""
            words += [(w, True) for w in kws]
        else: words.append((m.group(3), False))
    # words directly adjacent to a bracket (e.g. "[Request]." ) keep punctuation: fine.
    total_chars = sum(len(w) + 1 for w, _ in words)
    cid = f"cap-{ln['key']}"
    spans = "".join(f'<span id="{cid}-w{i}" class="w{" kw" if kw else ""}">{H.escape(w)} </span>' for i, (w, kw) in enumerate(words))
    cap_html.append(f'<div id="{cid}" class="cap">{spans}</div>')
    cap_js.append(f'tl.fromTo("#{cid}",{{opacity:0}},{{opacity:1,duration:.12}},{ln["start"] - 0.05:.3f});')
    cap_js.append(f'tl.fromTo("#{cid}",{{opacity:1}},{{opacity:0,duration:.12,immediateRender:false}},{ln["end"] + 0.1:.3f});')
    cur = ln["start"]
    dur = ln["end"] - ln["start"]
    for i, (w, kw) in enumerate(words):
        d = dur * (len(w) + 1) / total_chars
        cap_js.append(f'tl.fromTo("#{cid}-w{i}",{{color:"{YEL if kw else "#ffffff"}"}},{{color:"{YEL}",duration:.01,immediateRender:false}},{cur:.3f});')
        if not kw:
            cap_js.append(f'tl.fromTo("#{cid}-w{i}",{{color:"{YEL}"}},{{color:"#ffffff",duration:.01,immediateRender:false}},{cur + d:.3f});')
        cur += d
open(f"{HF}/compositions/captions.html", "w").write(f"""<template>
<style>
#root{{position:absolute;inset:0;font-family:'Inter',sans-serif}}
.cap{{position:absolute;left:210px;top:918px;width:1500px;text-align:center;font-size:50px;font-weight:700;line-height:1.18;color:#fff;opacity:0;
 -webkit-text-stroke:8px #0E0622;paint-order:stroke fill;}}
.w{{color:#fff}}.kw{{color:{YEL}}}
</style>
<div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
{chr(10).join(cap_html)}
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cap_js)}
window.__timelines = window.__timelines || {{}};
window.__timelines["captions"] = tl;
</script>
</div>
</template>
""")

# ---------- index.html ----------
hosts = []
allscenes = sorted(SCENES, key=lambda s: s["start"])
for i, s in enumerate(allscenes):
    hosts.append(f'<div id="{s["id"]}" class="clip" data-composition-id="{s["id"]}" data-composition-src="compositions/{s["id"]}.html" data-start="{s["start"]}" data-duration="{s["dur"]}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>')
html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="assets/vendor/gsap.min.js"></script>
<style>
:root{{--bg:#000000}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:var(--bg)}}
#main{{position:absolute;left:0;top:0;width:1920px;height:1080px;background:var(--bg)}}
</style>
</head>
<body>
<div id="main" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
<div id="hud" class="clip" data-composition-id="hud" data-composition-src="compositions/hud.html" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:50"></div>
<div id="captions" class="clip" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="3" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index:60"></div>
<audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{TOTAL:.3f}" data-track-index="4" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
open(HF + "/index.html", "w").write(html_doc)

json.dump(sorted(SFX), open(ROOT + "/build/sfx.json", "w"))
json.dump(allscenes, open(ROOT + "/build/scenes.json", "w"), indent=1)
print("scenes", len(allscenes), "sfx", len(SFX), "total", TOTAL)
