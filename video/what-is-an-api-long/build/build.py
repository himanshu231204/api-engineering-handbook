#!/usr/bin/env python3
"""Generate the HyperFrames project (hf/) from timing.json. Every time comes from the voice data."""
import json, math, os, re, html as H
from script_lines import CHAPTERS

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
HF = ROOT + "/hf"
T = json.load(open(ROOT + "/build/timing.json"))
LINES = {l["key"]: l for l in T["lines"]}
TOTAL = math.ceil(T["total"] * 30) / 30
W, Hh = 1920, 1080

YEL, PINK, CYAN, LIME, ORG, VIO, RED = "#FFE500", "#FF2E88", "#00F0FF", "#39FF88", "#FF9100", "#9D4EFF", "#FF3B3B"
GREY, INK = "#A0A0B0", "#0E0622"

SFX = []          # (time, kind)
SCENES = []       # for root index + script.json
os.makedirs(HF + "/compositions", exist_ok=True)


def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())


def tw(key, phrase=None, frac=None):
    """Absolute time of a spoken word in line `key`. Falls back to proportional word position."""
    ln = LINES[key]
    if phrase is None and frac is None: return ln["start"]
    say = [norm(w) for w in ln["say"].split()]
    heard = ln["words"]
    if frac is None:
        p = norm(phrase)
        idx = next((i for i, w in enumerate(say) if w.startswith(p)), None)
        if idx is None: return ln["start"]
        if len(heard) == len(say): j = idx
        else: j = round(idx * (len(heard) - 1) / max(len(say) - 1, 1))
        # prefer an exact ASR match near the proportional guess
        for k in range(max(0, j - 2), min(len(heard), j + 3)):
            if norm(heard[k]["w"]).startswith(p): j = k; break
        return heard[min(j, len(heard) - 1)]["start"] if heard else ln["start"]
    return ln["start"] + frac * (ln["end"] - ln["start"])


def hexa(c, a):
    c = c.lstrip("#"); r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


class Scene:
    def __init__(self, sid, keys, kind, start, end, chapter, first=False, fade_out=False, assets=None, pill=None):
        self.id, self.keys, self.kind, self.start, self.end = sid, keys, kind, start, end
        self.chapter, self.first, self.fade_out = chapter, first, fade_out
        self.assets, self.pill_text = assets or [], pill
        self.h, self.js, self.n = [], [], 0

    def t(self, key, phrase=None, frac=None):
        return round(max(tw(key, phrase, frac) - self.start - 0.05, 0.02), 3)

    def local(self, abs_t): return round(abs_t - self.start, 3)

    def uid(self):
        self.n += 1; return f"{self.id}-e{self.n}"

    def el(self, inner, x, y, w=None, h=None, style="", anim="fade", t=0.0, out=None, cls="", sfx=None):
        i = self.uid()
        st = f"left:{x}px;top:{y}px;" + (f"width:{w}px;" if w else "") + (f"height:{h}px;" if h else "") + style
        self.h.append(f'<div id="{i}" class="el {cls}" style="{st}">{inner}</div>')
        self.js.append(f'A("{i}","{anim}",{t},{"null" if out is None else out});')
        if sfx: SFX.append((self.start + t, sfx))
        return i

    # ---- components ----
    def text(self, s, x, y, w=1000, size=64, color="#fff", weight=900, align="left", **kw):
        st = f"font-size:{size}px;font-weight:{weight};color:{color};text-align:{align};line-height:1.12;"
        return self.el(s, x, y, w, style=st + kw.pop("style", ""), **kw)

    def box(self, x, y, w, h, color, title, sub=None, dashed=False, tsize=44, **kw):
        bd = f"border:5px {'dashed' if dashed else 'solid'} {color};background:{hexa(color, .09)};box-shadow:0 0 28px {hexa(color, .30)};"
        inner = f'<div class="bt" style="font-size:{tsize}px;color:#fff">{title}</div>'
        if sub: inner += f'<div class="bs">{sub}</div>'
        kw.setdefault("anim", "pop")
        kw.setdefault("sfx", "pop")
        return self.el(inner, x, y, w, h, style=bd, cls="box", **kw)

    def chip(self, s, x, y, color=CYAN, w=None, size=34, ink=True, **kw):
        st = f"background:{color};color:{INK if ink else '#fff'};font-size:{size}px;"
        kw.setdefault("anim", "pop")
        return self.el(s, x, y, w, style=st, cls="chip", **kw)

    def note(self, s, x, y, color=YEL, size=58, rot=-3, w=600, **kw):
        kw.setdefault("anim", "wipe")
        return self.el(s, x, y, w, style=f"font-family:'Caveat';font-weight:700;font-size:{size}px;color:{color};transform-origin:left center;line-height:1;", cls="note", **kw)

    def arrow(self, x1, y1, x2, y2, color=GREY, t=0.0, label=None, label_dy=-44, dash=False, width=6, out=None):
        i = self.uid(); L = math.hypot(x2 - x1, y2 - y1)
        ang = math.atan2(y2 - y1, x2 - x1); hs = 22
        bx, by = x2 - math.cos(ang) * hs, y2 - math.sin(ang) * hs
        p1 = (bx + math.cos(ang + 2.5) * hs * .75 * -1, by + math.sin(ang + 2.5) * hs * .75 * -1)
        # arrowhead polygon
        a1 = ang + math.pi - 0.45; a2 = ang + math.pi + 0.45
        pts = f"{x2},{y2} {x2 + math.cos(a1) * hs},{y2 + math.sin(a1) * hs} {x2 + math.cos(a2) * hs},{y2 + math.sin(a2) * hs}"
        da = f'stroke-dasharray="{L:.1f}" ' if not dash else 'stroke-dasharray="14 12" '
        self.h.append(
            f'<svg id="{i}" class="svgl" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}"><line id="{i}-l" x1="{x1}" y1="{y1}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round" {da}/>'
            f'<polygon id="{i}-h" points="{pts}" fill="{color}"/></svg>')
        if dash:
            self.js.append(f'D("{i}",{t},{L:.1f},false,{"null" if out is None else out});')
        else:
            self.js.append(f'D("{i}",{t},{L:.1f},true,{"null" if out is None else out});')
        if label:
            self.text(label, min(x1, x2) - 20, (y1 + y2) / 2 + label_dy, abs(x2 - x1) + 40, size=32, color=color if color != GREY else "#fff", weight=700, align="center", t=t + .15, out=out, anim="fade")
        return i

    def pill(self, s, key, phrase=None):
        i = self.uid()
        self.h.append(f'<div id="{i}" class="pillwrap"><div class="pill" id="{i}-p">{s}</div></div>')
        self.js.append(f'PILL("{i}",{self.t(key, phrase)});')

    def code(self, x, y, w, lines, title, size=30, lh=46, times=None, bg="#0A0A0A", out=None, tcolor=GREY):
        """lines: list of html strings. times: list of local seconds (typing start per line)."""
        n = len(lines)
        h = 78 + lh * n + 26
        cid = self.uid()
        dots = '<span class="dot" style="background:#FF5F57"></span><span class="dot" style="background:#FEBC2E"></span><span class="dot" style="background:#28C840"></span>'
        self.h.append(f'<div id="{cid}" class="el codecard" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{bg}"><div class="bar">{dots}<span class="ttl" style="color:{tcolor}">{title}</span></div></div>')
        self.js.append(f'A("{cid}","fade",{times[0] - 0.25 if times else 0},{"null" if out is None else out});')
        ids = []
        for k, ln in enumerate(lines):
            i = f"{cid}-L{k}"
            self.h.append(f'<div id="{i}" class="el mono" style="left:{x + 34}px;top:{y + 78 + k * lh}px;width:{w - 60}px;font-size:{size}px;height:{lh}px;white-space:pre">{ln}</div>')
            tt = times[k] if times else 0
            self.js.append(f'A("{i}","wipe",{tt},{"null" if out is None else out});')
            if ln.strip() and tt > 0.3: SFX.append((self.start + tt, "tick"))
            ids.append(i)
        return cid, ids, (y + 78, lh)

    def hl(self, x, y0, lh, w, steps, color=YEL, out=None):
        """steps: [(local_time, line_index)] moving highlight bar."""
        i = self.uid()
        self.h.append(f'<div id="{i}" class="el" style="left:{x}px;top:{y0}px;width:{w}px;height:{lh}px;background:{hexa(color, .16)};border-left:6px solid {color};opacity:0"></div>')
        t0, k0 = steps[0]
        self.js.append(f'tl.fromTo("#{i}",{{opacity:0,y:{k0 * lh}}},{{opacity:1,y:{k0 * lh},duration:.2}},{t0});')
        for (ta, ka), (tb, kb) in zip(steps, steps[1:]):
            self.js.append(f'tl.fromTo("#{i}",{{y:{ka * lh}}},{{y:{kb * lh},duration:.3,ease:"power2.inOut",immediateRender:false}},{tb});')
        if out is not None:
            self.js.append(f'tl.fromTo("#{i}",{{opacity:1}},{{opacity:0,duration:.2,immediateRender:false}},{out});')
        return i

    def img(self, src, x, y, w, h, t=0.0, out=None, title=None, zoom=(1.0, 1.08), dur=10, frame=True):
        i = self.uid()
        bar = ""
        if frame:
            bar = '<div class="bar" style="height:46px"><span class="dot" style="background:#FF5F57"></span><span class="dot" style="background:#FEBC2E"></span><span class="dot" style="background:#28C840"></span>' + (f'<span class="url">{title}</span>' if title else "") + '</div>'
        top = 46 if frame else 0
        self.h.append(f'<div id="{i}" class="el shot" style="left:{x}px;top:{y}px;width:{w}px;height:{h + top}px">{bar}<div class="vp" style="top:{top}px;height:{h}px"><img id="{i}-i" src="{src}" style="width:{w}px;height:{h}px"/></div></div>')
        self.js.append(f'A("{i}","fade",{t},{"null" if out is None else out});')
        self.js.append(f'tl.fromTo("#{i}-i",{{scale:{zoom[0]}}},{{scale:{zoom[1]},duration:{dur},ease:"none"}},{t});')
        SFX.append((self.start + t, "shutter"))
        return i, top

    def svg_reveal(self, path, x, y, scale, axis, steps, out=None, glow=None):
        """Inline a repo SVG / rendered Mermaid SVG (path relative to hf/) and reveal it step by step.
        axis 'y' = top-to-bottom, 'x' = left-to-right; steps = [(local_time, svg_units_revealed)]."""
        svg = open(f"{HF}/{path}").read()
        vb = re.search(r'viewBox="([\-\d\.]+) ([\-\d\.]+) ([\d\.]+) ([\d\.]+)"', svg)
        vw, vh = float(vb.group(3)), float(vb.group(4))
        w, h = vw * scale, vh * scale
        svg = re.sub(r"<svg ", f'<svg style="width:{w:.0f}px;height:{h:.0f}px;display:block;overflow:visible" ', svg, count=1)
        i = self.uid()
        self.h.append(f'<div id="{i}" class="el" style="left:{x}px;top:{y}px;width:{w:.0f}px;height:{h:.0f}px">{svg}</div>')
        total = vh if axis == "y" else vw
        def clip(u):
            r = max(0.0, 100.0 * (1 - u / total))
            return f"inset(0 0 {r:.2f}% 0)" if axis == "y" else f"inset(0 {r:.2f}% 0 0)"
        full = "inset(0 0 100% 0)" if axis == "y" else "inset(0 100% 0 0)"
        t0, u0 = steps[0]
        self.js.append(f'tl.fromTo("#{i}",{{opacity:1,clipPath:"{full}"}},{{opacity:1,clipPath:"{clip(u0)}",duration:.5,ease:"power2.out"}},{t0});')
        for (ta, ua), (tb, ub) in zip(steps, steps[1:]):
            self.js.append(f'tl.fromTo("#{i}",{{clipPath:"{clip(ua)}"}},{{clipPath:"{clip(ub)}",duration:.5,ease:"power2.out",immediateRender:false}},{tb});')
        if out is not None:
            self.js.append(f'tl.fromTo("#{i}",{{opacity:1}},{{opacity:0,duration:.2,immediateRender:false}},{out});')
        SFX.append((self.start + t0, "shutter"))
        return i, (w, h)

    def ring(self, x, y, w, h, color=YEL, t=0.0, out=None, r=18):
        i = self.uid()
        self.h.append(f'<svg id="{i}" class="svgl" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}"><rect id="{i}-r" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="{color}" stroke-width="6" stroke-dasharray="{2 * (w + h):.0f}" stroke-dashoffset="{2 * (w + h):.0f}" stroke-linecap="round"/></svg>')
        self.js.append(f'RING("{i}",{t},{2 * (w + h):.0f},{"null" if out is None else out});')

    def stat(self, num, suffix, x, y, w, color, label, t, size=150):
        i = self.uid()
        self.h.append(f'<div id="{i}" class="el" style="left:{x}px;top:{y}px;width:{w}px"><div id="{i}-n" class="num" style="font-size:{size}px;color:{color}">{num}{suffix}</div><div class="lab">{label}</div></div>')
        self.js.append(f'STAT("{i}",{t},{num},"{suffix}");')
        SFX.append((self.start + t, "thunk"))

    # ---- output ----
    def write(self, extra_css=""):
        dur = round(self.end - self.start, 3)
        fo = ""
        if self.fade_out:
            fo = f'tl.fromTo("#{self.id}-stage",{{opacity:1}},{{opacity:0,duration:.2,immediateRender:false}},{dur - 0.22});'
        enter = "" if self.first else f'tl.fromTo("#{self.id}-stage",{{opacity:0,scale:1.04}},{{opacity:1,scale:1,duration:.22,ease:"power3.out"}},0);'
        body = "\n".join(self.h)
        doc = f"""<template>
<style>{BASE_CSS}{extra_css}</style>
<div id="root" data-composition-id="{self.id}" data-width="{W}" data-height="{Hh}">
<div id="{self.id}-stage" class="stage">
{body}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{JSLIB}
{enter}
{chr(10).join(self.js)}
{fo}
window.__timelines = window.__timelines || {{}};
window.__timelines["{self.id}"] = tl;
</script>
</div>
</template>
"""
        open(f"{HF}/compositions/{self.id}.html", "w").write(doc)
        SCENES.append(dict(id=self.id, start=round(self.start, 3), dur=dur, kind=self.kind, chapter=self.chapter, keys=self.keys, assets=self.assets, pill=self.pill_text))


BASE_CSS = """
@font-face{font-family:'Caveat';src:url('assets/fonts/caveat-700.woff2') format('woff2');font-weight:700;}
#root{position:absolute;inset:0;font-family:'Inter',sans-serif;color:#fff;}
.stage{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:50% 50%;}
.el{position:absolute;opacity:0;}
.svgl{position:absolute;left:0;top:0;pointer-events:none;overflow:visible}
.box{border-radius:26px;padding:22px 26px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;box-sizing:border-box}
.bt{font-weight:900;line-height:1.1}
.bs{font-size:30px;font-weight:700;color:#A0A0B0;margin-top:10px;line-height:1.2}
.chip{display:inline-block;padding:12px 28px;border-radius:999px;font-weight:900;white-space:nowrap;text-align:center}
.mono{font-family:'JetBrains Mono',monospace;font-weight:700;color:#E8E8F0}
.codecard{border-radius:24px;border:1px solid #2A2A2A;overflow:hidden;box-sizing:border-box}
.bar{height:62px;background:#111;display:flex;align-items:center;padding-left:24px;gap:10px;border-bottom:1px solid #2A2A2A;box-sizing:border-box}
.dot{display:inline-block;width:18px;height:18px;border-radius:50%}
.ttl,.url{font-size:28px;font-weight:700;margin-left:18px;font-family:'JetBrains Mono',monospace}
.url{background:#222;border-radius:999px;padding:6px 22px;color:#C8C8D4}
.k{color:#FF2E88}.s{color:#39FF88}.f{color:#00F0FF}.c{color:#7A7A90}.d{color:#FF9100}.n{color:#FFE500}.g{color:#39FF88}.o{color:#FF9100}.r{color:#FF3B3B}.m{color:#7A7A90}
.pillwrap{position:absolute;left:0;top:806px;width:1920px;text-align:center;opacity:0}
.pill{display:inline-block;background:#111;border:1px solid #2A2A2A;border-radius:999px;padding:12px 40px;font-size:38px;font-weight:900;color:#A0A0B0}
.shot{border-radius:22px;border:1px solid #2A2A2A;overflow:hidden;background:#0A0A0A;box-sizing:border-box}
.vp{position:absolute;left:0;width:100%;overflow:hidden}
.vp img{position:absolute;left:0;top:0;transform-origin:50% 50%}
.num{font-weight:900;line-height:1}
.lab{font-size:40px;font-weight:900;color:#fff;margin-top:6px}
"""

JSLIB = """
const A=(id,kind,t,out)=>{const s='#'+id;
 if(kind==='fade') tl.fromTo(s,{opacity:0,y:20},{opacity:1,y:0,duration:.3,ease:'power3.out'},t);
 else if(kind==='pop') tl.fromTo(s,{opacity:0,scale:.6},{opacity:1,scale:1,duration:.34,ease:'back.out(1.9)'},t);
 else if(kind==='wipe') tl.fromTo(s,{opacity:1,clipPath:'inset(0 100% 0 0)'},{opacity:1,clipPath:'inset(0 0% 0 0)',duration:.45,ease:'none'},t);
 else if(kind==='slam') tl.fromTo(s,{opacity:0,scale:1.8},{opacity:1,scale:1,duration:.3,ease:'back.out(1.4)'},t);
 else if(kind==='grey') tl.fromTo(s,{opacity:.45},{opacity:1,duration:.35,ease:'power2.out'},t);
 else if(kind==='static') tl.set(s,{opacity:1},0);
 if(out!==null) tl.fromTo(s,{opacity:1},{opacity:0,duration:.2,ease:'power2.in',immediateRender:false},out);
};
const D=(id,t,L,solid,out)=>{
 if(solid){ tl.fromTo('#'+id+'-l',{strokeDashoffset:L},{strokeDashoffset:0,duration:.45,ease:'power2.out'},t);
   tl.fromTo('#'+id+'-h',{opacity:0},{opacity:1,duration:.12},t+.38);
 } else { tl.fromTo('#'+id+'-l',{opacity:0},{opacity:1,duration:.3},t); tl.fromTo('#'+id+'-h',{opacity:0},{opacity:1,duration:.12},t+.25); }
 if(out!==null) tl.fromTo('#'+id,{opacity:1},{opacity:0,duration:.2,immediateRender:false},out);
};
const RING=(id,t,L,out)=>{ tl.fromTo('#'+id+'-r',{strokeDashoffset:L},{strokeDashoffset:0,duration:.5,ease:'power2.out'},t);
 if(out!==null) tl.fromTo('#'+id,{opacity:1},{opacity:0,duration:.2,immediateRender:false},out); };
const PILL=(id,t)=>{ tl.fromTo('#'+id,{opacity:0,y:14},{opacity:1,y:0,duration:.3,ease:'power3.out'},t-0.1);
 tl.fromTo('#'+id+'-p',{color:'#A0A0B0'},{color:'#ffffff',duration:.4,ease:'power2.out'},t); };
const STAT=(id,t,v,suf)=>{ const o={v:0}; const n=document.getElementById(id+'-n');
 tl.fromTo('#'+id,{opacity:0,scale:1.5},{opacity:1,scale:1,duration:.32,ease:'back.out(1.4)'},t);
 tl.fromTo(o,{v:0},{v:v,duration:.9,ease:'power2.out',onUpdate:()=>{n.textContent=Math.round(o.v)+suf;}},t); };
"""

# ---------- timing of scenes ----------
BEAT_ORDER = []
for ln in T["lines"]:
    if not BEAT_ORDER or BEAT_ORDER[-1][0] != ln["beat"]: BEAT_ORDER.append([ln["beat"], []])
    BEAT_ORDER[-1][1].append(ln["key"])
BEAT_INFO = {}
for bi, (bid, keys) in enumerate(BEAT_ORDER):
    first, last = LINES[keys[0]], LINES[keys[-1]]
    BEAT_INFO[bid] = dict(keys=keys, ch=first["ch"], start=first["start"], last_end=last["end"], i=bi)

# chapter-card slots: inserted where the chapter number changes
CARDS = []
SC_TIMES = {}
for bi, (bid, keys) in enumerate(BEAT_ORDER):
    info = BEAT_INFO[bid]
    nxt = BEAT_INFO[BEAT_ORDER[bi + 1][0]] if bi + 1 < len(BEAT_ORDER) else None
    start = 0.0 if bi == 0 else max(info["start"] - 0.08, 0)
    if nxt and nxt["ch"] != info["ch"]:
        end = info["last_end"] + 0.25
        cstart, cend = end, max(nxt["start"] - 0.08, end + 0.9)
        CARDS.append(dict(ch=nxt["ch"], start=cstart, end=cend, fade=True))
        SC_TIMES[bid] = (start, end, True)
    else:
        end = (nxt["start"] - 0.08) if nxt else TOTAL
        SC_TIMES[bid] = (start, end, False)


def sc(bid, kind, **kw):
    s, e, fo = SC_TIMES[bid]
    return Scene(bid, BEAT_INFO[bid]["keys"], kind, s, e, BEAT_INFO[bid]["ch"], first=(bid == "hook"), fade_out=fo, **kw)


def hilite(s): return s


# ===================== BEATS =====================
def beat_hook():
    S = sc("hook", "logo_reveal", assets=["svg/emblem"], pill=None)
    # frame 0 is fully built: emblem + hook title (no entrance)
    S.el(f'<svg width="300" height="300" viewBox="0 0 300 300"><circle cx="150" cy="150" r="136" fill="none" stroke="{YEL}" stroke-width="10"/>'
         f'<text x="150" y="182" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="92" fill="{YEL}">&lt;/&gt;</text></svg>',
         150, 130, anim="static", style="filter:drop-shadow(0 0 14px rgba(255,229,0,.55))")
    S.text(f'WHAT IS AN <span style="color:{YEL}">API</span>?', 500, 150, 1300, size=148, anim="static")
    S.text("The promise between two programs.", 506, 345, 1200, size=50, color=GREY, weight=700, anim="static")
    # diagram: your app -> ??? server
    S.box(250, 560, 480, 200, CYAN, "Your app", "the client", t=S.t("h1", "app"))
    S.box(1190, 560, 480, 200, SLATE, "Server", "you never see it", dashed=True, t=S.t("h1", "server"))
    S.arrow(740, 640, 1180, 640, GREY, t=S.t("h1", "never"))
    S.chip("GET /users/42", 840, 520, YEL, t=S.t("h2", "saying"), size=32)
    S.text("?", 1190, 400, 480, size=130, color=SLATE, weight=900, align="center", t=S.t("h2", "works"), anim="slam")
    S.write()


SLATE = "#7C8DA6"


def beat_road():
    S = sc("road", "roadmap", pill="5 parts")
    S.text("THE PLAN", 560, 110, 800, size=84, color=YEL, anim="fade", t=S.t("r1", "plan"))
    rows = [("1", "The contract", "r2", "contract", CYAN), ("2", "A request, line by line", "r2", "request", LIME),
            ("3", "The server side", "r2", "server", PINK), ("4", "Who calls APIs", "r3", "calls", ORG), ("5", "Five mistakes", "r3", "mistakes", RED)]
    for i, (n, label, key, ph, col) in enumerate(rows):
        y = 250 + i * 108
        S.chip(n, 560, y, col, w=72, size=44, t=S.t(key, ph))
        S.text(label, 664, y + 2, 900, size=60, anim="fade", t=S.t(key, ph) + 0.05)
    S.pill("Five parts · about six minutes", "r1", "five")
    S.write()


def beat_c1a():
    S = sc("c1a", "svg_diagram", pill="API = a contract")
    t_out = S.t("a2") - 0.05
    for i, (word, col, ph) in enumerate([("Application", CYAN, "Application"), ("Programming", LIME, "Programming"), ("Interface", PINK, "Interface")]):
        S.chip(word, 150 + i * 560, 150, col, w=520, size=54, t=S.t("a1", ph), out=t_out)
    S.text(f'= a <span style="color:{YEL}">contract</span>', 160, 320, 1600, size=170, align="center", anim="slam", t=S.t("a1", "contract"), out=t_out)
    # a2: program A -> program B
    S.box(180, 160, 520, 190, CYAN, "Program A", "asks", t=S.t("a2"))
    S.box(1220, 160, 520, 190, SLATE, "Program B", "how it works inside: unknown", dashed=True, t=S.t("a2", "another"))
    S.arrow(710, 255, 1210, 255, GREY, t=S.t("a2", "asks"), label="asks for something")
    # a3: glossary card from the repo
    cid = S.uid()
    S.h.append(f'<div id="{cid}" class="el" style="left:260px;top:430px;width:1400px;border:2px solid {LIME};border-radius:26px;padding:34px 44px;background:{hexa(LIME, .07)};box-shadow:0 0 30px {hexa(LIME, .25)};box-sizing:border-box">'
               f'<div style="font-size:28px;font-weight:900;color:{LIME};letter-spacing:.08em">FROM THE HANDBOOK GLOSSARY</div>'
               f'<div style="font-size:48px;font-weight:700;line-height:1.28;margin-top:14px">“A <span style="color:{YEL}">defined contract</span> that lets one piece of software request functionality or data from another, <span style="color:{YEL}">without needing to know its internal implementation</span>.”</div></div>')
    S.js.append(f'A("{cid}","fade",{S.t("a3")},null);')
    SFX.append((S.start + S.t("a3"), "shutter"))
    S.pill("API = a contract", "a1", "contract")
    S.write()


def beat_c1b():
    S = sc("c1b", "svg_flow", pill="the shape of the socket is the promise")
    S.box(130, 250, 480, 240, ORG, "Lamp", "just plugs in", t=S.t("b1", "lamp"))
    S.box(720, 230, 480, 280, LIME, "Wall socket", "the contract", tsize=50, t=S.t("b1", "socket"))
    S.box(1310, 250, 480, 240, SLATE, "Power station", "hidden, free to change", dashed=True, t=S.t("b1", "station"))
    S.arrow(620, 370, 710, 370, GREY, t=S.t("b1", "plug"))
    S.arrow(1210, 370, 1300, 370, GREY, t=S.t("b1", "station"))
    S.note("the shape = the promise", 640, 560, YEL, 78, w=900, t=S.t("b2", "shape"))
    S.write()


def beat_c1c():
    S = sc("c1c", "svg_analogy", pill="change the kitchen, keep the menu", assets=["repo/svg/00-what-is-an-api.svg"])
    oc = S.t("c4") - 0.05
    S.box(110, 190, 440, 220, CYAN, "You", "the client", t=S.t("c1", "restaurant"), out=oc)
    S.box(740, 170, 440, 260, LIME, "Menu + waiter", "the API contract", tsize=44, t=S.t("c1", "menu"), out=oc)
    S.box(1370, 190, 440, 220, SLATE, "Kitchen", "the server", dashed=True, t=S.t("c1", "kitchen"), out=oc)
    S.arrow(560, 270, 730, 270, CYAN, t=S.t("c1", "tell"), label="order", label_dy=-42, out=oc)
    S.arrow(730, 350, 560, 350, LIME, t=S.t("c1", "cooks"), out=oc)
    S.arrow(1190, 270, 1360, 270, GREY, t=S.t("c1", "kitchen"), out=oc)
    S.arrow(1360, 350, 1190, 350, GREY, t=S.t("c1", "cooks"), label="dish", label_dy=18, out=oc)
    for i, (txt, ph) in enumerate([("new chefs", "chefs"), ("new stove", "stove"), ("new recipe", "recipe")]):
        S.chip(txt, 1450, 470 + i * 78, ORG, w=290, size=36, t=S.t("c2", ph), out=oc)
    S.text("✓", 905, 440, 110, size=140, color=LIME, align="center", anim="slam", t=S.t("c3", "menu"), sfx="thunk", out=oc)
    S.note("same menu, nobody notices", 140, 590, YEL, 62, w=760, t=S.t("c3", "notice"), out=oc)
    # the handbook's own diagram for this chapter (docs/assets/diagrams/00-what-is-an-api.svg), revealed as the line is spoken
    S.chip("from the handbook", 300, 76, LIME, size=30, t=S.t("c4", "whole"))
    S.svg_reveal("assets/repo/svg/00-what-is-an-api.svg", 300, 130, 1.5, "y",
                 [(S.t("c4", "whole"), 76), (S.t("c4", "Both"), 296), (S.t("c4", "holds"), 420)])
    S.write()


def beat_c2a():
    S = sc("c2a", "svg_flow", pill="the client always starts it", assets=["shots/mdn_crop.png"])
    S.box(120, 150, 520, 200, CYAN, "Client", "browser · app · script", t=S.t("d1", "client"))
    S.box(1280, 150, 520, 200, SLATE, "Server", "listens and answers", dashed=False, t=S.t("d1", "server"))
    S.arrow(660, 215, 1260, 215, CYAN, t=S.t("d1", "request"), label="HTTP request")
    S.arrow(1260, 295, 660, 295, LIME, t=S.t("d1", "response"), label="HTTP response", label_dy=14)
    t_out = S.local(LINES["d2"]["end"] - 0.05)
    for i, (txt, ph, col) in enumerate([("Browser", "browser", CYAN), ("Phone app", "phone", LIME), ("Another service", "service", PINK), ("Script", "script", ORG)]):
        S.chip(txt, 150 + (i % 2) * 330 if False else 130 + i * 300, 440, col, w=270 if i != 2 else 330, size=32, t=S.t("d2", ph), out=t_out) if False else None
    xs = [130, 410, 700, 1060]
    ws = [250, 270, 330, 220]
    for i, (txt, ph, col) in enumerate([("Browser", "browser", CYAN), ("Phone app", "phone", LIME), ("Another service", "service", PINK), ("Script", "script", ORG)]):
        S.chip(txt, xs[i], 440, col, w=ws[i], size=34, t=S.t("d2", ph), out=t_out)
    # MDN proof screenshot with marker highlight
    sc_w = 1320; s = sc_w / 830; hh = int(200 * s)
    iid, top = S.img("assets/shots/mdn_crop.png", 300, 440, sc_w, hh, t=S.t("d3"), title="developer.mozilla.org/…/Overview_of_HTTP", dur=9)
    ry = 440 + top + int(100 * s * 0.62)
    S.ring(300 + 6, 440 + top + int(88 * s), 1300, int(66 * s), YEL, t=S.t("d3", "always"))
    S.chip("MDN says", 300, 396, YEL, size=30, t=S.t("d3"))
    S.write()


def beat_c2b():
    S = sc("c2b", "code_card", pill="GET /users/42")
    lines = [f'<span class="k">GET</span> <span class="f">/users/42</span> <span class="m">HTTP/1.1</span>',
             f'<span class="f">Host:</span> api.example.com',
             f'<span class="f">Accept:</span> application/json',
             f'<span class="f">Authorization:</span> Bearer eyJhbGciOi...']
    times = [S.t("e1", "GET"), S.t("e3", "Headers"), S.t("e3", "Headers") + 0.35, S.t("e3", "Headers") + 0.7]
    cid, ids, (y0, lh) = S.code(120, 170, 1080, lines, "request · HTTP/1.1", size=36, lh=84, times=times)
    S.chip("METHOD · what to do", 1260, 232, CYAN, size=34, t=S.t("e2", "method"))
    S.chip("PATH · which thing", 1260, 304, LIME, size=34, t=S.t("e2", "path"))
    S.arrow(1250, 250, 1130, 250, CYAN, t=S.t("e2", "method"), width=4)
    S.chip("Accept → I want JSON", 1260, 484, PINK, size=32, t=S.t("e3", "Accept"))
    S.chip("Authorization → who I am", 1260, 556, ORG, size=32, t=S.t("e3", "Authorization"))
    S.hl(120, y0, lh, 1080, [(S.t("e2", "GET"), 0), (S.t("e3", "Headers"), 1), (S.t("e3", "Authorization"), 3)])
    S.note("this is real text, just lines", 140, 580, YEL, 60, w=900, t=S.t("e1", "request") + 0.4) if False else None
    S.write()


def beat_c2b2():
    S = sc("c2b2", "svg_diagram", pill="same four-part shape, both ways", assets=["repo/svg/01-http-request-anatomy.svg"])
    S.chip("from the handbook", 460, 44, LIME, size=30, t=S.t("e4", "Every"))
    S.svg_reveal("assets/repo/svg/01-http-request-anatomy.svg", 322, 100, 1.45, "y",
                 [(S.t("e4", "Every"), 92), (S.t("e4", "start"), 165), (S.t("e4", "headers"), 272), (S.t("e4", "empty"), 308),
                  (S.t("e4", "optional"), 378), (S.t("e4", "body") + 0.5, 470)])
    S.write()


def beat_c2e():
    S = sc("c2e", "svg_diagram", pill="the first digit tells you whose move it is", assets=["repo/svg/01-status-code-families.svg"])
    S.chip("from the handbook", 460, 44, LIME, size=30, t=S.t("f2", "Status"))
    S.svg_reveal("assets/repo/svg/01-status-code-families.svg", 300, 100, 1.5, "y",
                 [(S.t("f2", "Status"), 80), (S.t("f2", "families"), 150), (S.t("f2", "Two"), 222), (S.t("f2", "Four"), 366), (S.t("f2", "Five"), 440)])
    S.write()


def beat_c3m():
    S = sc("c3m", "svg_flow", pill="the whole trip, in one diagram", assets=["repo/mermaid/what-is-an-api-sequence.svg"])
    X0, Y0, SC_ = 143, 95, 1.4
    S.chip("Mermaid diagram from the handbook chapter", 460, 44, LIME, size=30, t=S.t("q1", "Now"))
    S.svg_reveal("assets/repo/mermaid/what-is-an-api-sequence.svg", X0, Y0, SC_, "y",
                 [(S.t("q1", "Now"), 92), (S.t("q2", "request"), 145), (S.t("q2", "matches"), 192), (S.t("q3", "fetches"), 236),
                  (S.t("q3", "database"), 282), (S.t("q3", "result"), 326), (S.t("q3", "response"), 372), (S.t("q3", "response") + 0.7, 489)])
    # q4: the API boundary. Client + API on the left depend on the contract; the right side is free to change
    S.ring(173, Y0 + 2, 760, 640, LIME, t=S.t("q4", "depends"))
    S.ring(950, Y0 + 2, 830, 640, PINK, t=S.t("q4", "free"))
    S.chip("the client depends on this", 183, 748, LIME, size=30, t=S.t("q4", "depends"))
    S.chip("free to change", 960, 748, PINK, size=30, ink=False, t=S.t("q4", "free"))
    S.write()


def beat_c2c():
    S = sc("c2c", "code_card", pill="status first, then the body")
    lines = [f'<span class="k">HTTP/1.1</span> <span class="g">200 OK</span>', f'<span class="f">Content-Type:</span> application/json', '',
             '{', f'  <span class="f">"id"</span>: <span class="n">42</span>,', f'  <span class="f">"name"</span>: <span class="s">"Priya Sharma"</span>,',
             f'  <span class="f">"email"</span>: <span class="s">"priya@example.com"</span>', '}']
    t1, t3 = S.t("f1", "status"), S.t("f3", "body")
    times = [t1, t1 + 0.3, 0.1, t3, t3 + 0.25, t3 + 0.5, t3 + 0.75, t3 + 1.0]
    cid, ids, (y0, lh) = S.code(120, 140, 960, lines, "response", size=36, lh=54, times=times)
    S.stat(200, "", 1180, 120, 560, LIME, "OK", S.t("f1", "200"), size=210)
    # f4: where did the data come from?
    t4 = S.t("f4", "PostgreSQL")
    for i, (txt, col) in enumerate([("PostgreSQL?", CYAN), ("MongoDB?", LIME), ("a dict?", PINK)]):
        S.box(120 + i * 330, 716, 300, 80, col, txt, tsize=32, dashed=True, t=S.t("f4", ["PostgreSQL", "MongoDB", "dictionary"][i]))
    S.note("the client can't tell", 1180, 700, YEL, 66, w=640, t=S.t("f4", "point") - 0.2)
    S.write()


def beat_c2d():
    S = sc("c2d", "svg_flow", pill="stateless: say who you are every time")
    S.box(120, 230, 440, 220, CYAN, "Client", None, t=S.t("g1", "HTTP"))
    S.box(1360, 230, 440, 220, SLATE, "Server", "no memory of the last request", t=S.t("g1", "HTTP"), tsize=44)
    S.arrow(580, 290, 1340, 290, CYAN, t=S.t("g1", "Every"), label="request #1")
    S.arrow(580, 400, 1340, 400, PINK, t=S.t("g1", "alone"), label="request #2")
    S.chip("STATELESS", 760, 130, YEL, size=44, t=S.t("g1", "stateless"), sfx="thunk")
    S.chip("send a token or cookie each time", 620, 520, ORG, size=40, t=S.t("g1", "remember"))
    S.note("each request stands alone", 640, 640, YEL, 70, w=900, t=S.t("g1", "alone"))
    S.write()


CODE = [
    f'<span class="k">from</span> fastapi <span class="k">import</span> FastAPI, HTTPException',
    f'app = <span class="f">FastAPI</span>()',
    f'FAKE_USERS_DB = {{',
    f'    <span class="n">42</span>: {{<span class="s">"id"</span>: <span class="n">42</span>, <span class="s">"name"</span>: <span class="s">"Priya Sharma"</span>, <span class="s">"email"</span>: <span class="s">"priya@example.com"</span>}}',
    f'}}',
    '',
    f'<span class="d">@app.get</span>(<span class="s">"/users/{{user_id}}"</span>)',
    f'<span class="k">def</span> <span class="f">get_user</span>(user_id: <span class="k">int</span>):',
    f'    user = FAKE_USERS_DB.<span class="f">get</span>(user_id)',
    f'    <span class="k">if</span> user <span class="k">is</span> <span class="k">None</span>:',
    f'        <span class="k">raise</span> <span class="f">HTTPException</span>(status_code=<span class="n">404</span>, detail=<span class="s">"User not found"</span>)',
    f'    <span class="k">return</span> user',
]


def beat_c3a():
    S = sc("c3a", "code_card", pill="the route is the contract", assets=["demo/main.py"])
    t1, t2, t3, t4 = S.t("i1", "complete"), S.t("i2", "decorator"), S.t("i3", "function"), S.t("i4", "integer")
    times = [t1, t1 + .3, t1 + .6, t1 + .8, t1 + 1.0, 0.2, t2, t2 + .4, t3, t3 + .25, t3 + .5, t3 + .8]
    cid, ids, (y0, lh) = S.code(90, 110, 1420, CODE, "main.py  ·  from the handbook chapter", size=29, lh=50, times=times)
    S.chip("FastAPI", 1540, 120, LIME, size=30, t=S.t("i1", "FastAPI"))
    S.hl(90, y0, lh, 1420, [(t2, 6), (t2 + .5, 7), (t3, 9), (t3 + .8, 10), (t4, 7)])
    S.chip("route → function", 1540, 330, CYAN, size=28, w=290, t=t2 + .1)
    S.chip("no user → 404", 1540, 520, ORG, size=28, w=290, t=t3 + .6)
    S.chip("int → validated", 1540, 400, PINK, size=28, w=290, t=t4 + .1)
    S.write()


def beat_c3b():
    S = sc("c3b", "terminal_clip", pill="real run: 200, 404, 422", assets=["demo/real_output_8000.txt"])
    tj1, tj2, tj3 = S.t("j1", "ask"), S.t("j2", "status"), S.t("j3", "Ask")
    t_404, t_422 = S.t("j3", "doesn't"), S.t("j3", "banana")
    ln = [
        f'<span class="g">$</span> curl -i localhost:8000/users/42',
        f'<span class="k">HTTP/1.1</span> <span class="g">200 OK</span>',
        f'<span class="f">content-type:</span> application/json',
        f'{{"id":42,"name":"Priya Sharma","email":"priya@example.com"}}',
        '',
        f'<span class="g">$</span> curl -i localhost:8000/users/7',
        f'<span class="k">HTTP/1.1</span> <span class="o">404 Not Found</span>',
        f'{{"detail":"User not found"}}',
        '',
        f'<span class="g">$</span> curl -i localhost:8000/users/banana',
        f'<span class="k">HTTP/1.1</span> <span class="o">422 Unprocessable Content</span>',
        f'{{"detail":[{{"type":"int_parsing","loc":["path","user_id"],…',
    ]
    times = [tj1, tj1 + .6, tj2, tj2 + .6, 0, t_404 - .8, t_404, t_404 + .4, 0, t_422 - .9, t_422, t_422 + .4]
    S.code(110, 120, 1300, ln, "terminal  ·  uvicorn main:app", size=31, lh=46, times=times, bg="#000000")
    S.chip("status line", 1460, 230, LIME, size=30, t=S.t("j2", "status"))
    S.chip("headers", 1460, 290, CYAN, size=30, t=S.t("j2", "headers"))
    S.chip("JSON", 1460, 350, PINK, size=30, t=S.t("j2", "JSON"))
    S.text("some headers trimmed", 1460, 560, 380, size=28, color=GREY, weight=700, t=tj1 + .8)
    S.write()


def beat_c3c():
    S = sc("c3c", "svg_compare", pill="swap the backend, keep the contract")
    S.box(110, 190, 440, 260, CYAN, "Client", "GET /users/42", tsize=50, t=S.t("k1", "Today"))
    S.box(700, 150, 560, 340, LIME, "", None, t=S.t("k1", "Today"), tsize=50)
    S.text("The contract", 700, 168, 560, size=46, align="center", t=S.t("k1", "Today"))
    for i, (txt, ph) in enumerate([("same URL", "URL"), ("same JSON shape", "JSON"), ("same status codes", "status")]):
        S.text("✓ " + txt, 740, 245 + i * 76, 500, size=40, color=LIME, weight=900, t=S.t("k2", ph), anim="pop", sfx="pop")
    S.arrow(560, 320, 690, 320, GREY, t=S.t("k1", "Today"))
    S.arrow(1270, 320, 1350, 320, GREY, t=S.t("k1", "Today"))
    S.box(1360, 130, 460, 120, SLATE, "fake dict", None, dashed=True, tsize=38, t=S.t("k1", "dictionary"), out=S.t("k1", "Next") + 0.0)
    S.box(1360, 290, 460, 120, VIO, "PostgreSQL", None, tsize=40, t=S.t("k1", "Post"), out=S.t("k1", "service") - 0.1)
    S.box(1360, 450, 460, 120, PINK, "another service", None, tsize=38, t=S.t("k1", "service"))
    S.text(f'The <span style="color:{YEL}">contract</span> doing its job', 110, 640, 1700, size=76, align="center", t=S.t("k3", "contract") - 0.4)
    S.write()


def beat_c4a():
    S = sc("c4a", "svg_icons", pill="web, apps, services, AI: all callers")
    S.text("Who calls APIs?", 110, 100, 1700, size=96, align="center", t=S.t("l1", "Who"))
    for i, (txt, col, ph) in enumerate([("Weather app", CYAN, "weather"), ("Sign in with Google", LIME, "sign"), ("Payment form", PINK, "payment"), ("Backend service", ORG, "backend")]):
        S.chip(txt, 110 + [0, 360, 800, 1190][i] if False else [110, 440, 900, 1290][i], 290, col, size=38, t=S.t("l2", ph))
    t3 = S.t("l3", "AI")
    S.chip("AI model", 110, 470, VIO, size=44, ink=False, t=t3)
    lines = [f'<span class="k">POST</span> <span class="f">/chat</span> <span class="m">HTTP/1.1</span>', f'{{ <span class="s">"messages"</span>: [ … ] }}', f'<span class="g">200 OK</span>  <span class="m">→ JSON back</span>']
    S.code(110, 540, 1100, lines, "an LLM call is just a web API", size=34, lh=56, times=[S.t("l3", "POST"), S.t("l3", "JSON") + 0.0, S.t("l3", "coming")], bg="#0A0A0A")
    S.write()


def beat_c4b():
    S = sc("c4b", "stat_drop", pill="Postman 2025 · a vendor survey", assets=["shots/postman_crop.png"])
    t_out = S.t("m2", "Postman") - 0.05
    S.box(300, 200, 520, 200, VIO, "A model", "the kitchen you never see", dashed=True, t=S.t("m1", "kitchen"), out=t_out)
    S.text("Same contract.", 260, 470, 1400, size=84, t=S.t("m1", "contract"), out=t_out)
    sw = 1000; sh = int(540 * sw / 1600)
    iid, top = S.img("assets/shots/postman_crop.png", 100, 160, sw, sh, t=S.t("m2", "Postman"), title="postman.com/state-of-api/2025", dur=16)
    S.ring(100 + 6, 160 + top + int(0.605 * sh) + 0, 560, 50, YEL, t=S.t("m2", "survey") + 0.1)
    S.chip("Postman says", 100, 100, YEL, size=30, t=S.t("m2", "Postman"))
    S.stat(89, "%", 1180, 90, 640, CYAN, "use generative AI", S.t("m2", "eighty") - 0.1)
    S.stat(24, "%", 1180, 320, 640, PINK, "design APIs for AI agents", S.t("m3", "twenty") - 0.1)
    S.stat(65, "%", 1180, 550, 640, LIME, "earn revenue from APIs", S.t("m4", "sixty") - 0.1)
    S.write()


def mistake(bid, key, n, bad_title, bad_lines, good_title, good_lines, pill, bad_note, ph_bad, ph_good):
    S = sc(bid, "svg_compare", pill=pill)
    S.text(f"Mistake {n}", 110, 80, 700, size=96, color=YEL, weight=900, t=S.t(key, "Mistake") - 0.05, anim="slam")
    # left bad card
    def card(x, color, mark, title, lines, tt):
        h = 130 + 72 * len(lines)
        inner = f'<div style="font-size:32px;font-weight:900;color:{color};letter-spacing:.06em">{mark} {title}</div>' + "".join(f'<div class="mono" style="font-size:40px;margin-top:22px;line-height:1.25">{l}</div>' for l in lines)
        S.el(inner, x, 250, 800, h, style=f"border:4px solid {color};border-radius:26px;padding:28px 36px;background:{hexa(color, .08)};box-shadow:0 0 28px {hexa(color, .28)};box-sizing:border-box", anim="fade", t=tt, sfx="pop")
    card(110, RED, "✗", bad_title, bad_lines, S.t(key, ph_bad))
    card(1010, LIME, "✓", good_title, good_lines, S.t(key, ph_good))
    S.note(bad_note, 130, 640, ORG, 70, w=800, t=S.t(key, ph_bad) + 0.6)
    S.write()


def beat_m1():
    S = sc("m1", "svg_diagram", pill="API ⊃ web API ⊃ REST")
    key = "x1"
    S.text("Mistake 1", 110, 80, 700, size=96, color=YEL, t=S.t(key, "Mistake") - 0.05, anim="slam")
    S.chip('"API" ≠ "REST API"', 110, 220, RED, ink=False, size=46, t=S.t(key, "Saying"))
    S.el(f'<div style="font-size:30px;font-weight:900;color:{CYAN}">API</div><div style="font-size:28px;font-weight:700;color:{GREY}">function signatures · OS calls · web APIs</div>', 800, 160, 1010, 600,
         style=f"border:4px solid {CYAN};border-radius:36px;padding:26px 34px;background:{hexa(CYAN, .05)};box-sizing:border-box", anim="fade", t=S.t(key, "APIs"))
    S.el(f'<div style="font-size:30px;font-weight:900;color:{LIME}">Web API</div><div style="font-size:28px;font-weight:700;color:{GREY}">over HTTP</div>', 860, 330, 890, 380,
         style=f"border:4px solid {LIME};border-radius:32px;padding:22px 30px;background:{hexa(LIME, .06)};box-sizing:border-box", anim="fade", t=S.t(key, "web"))
    S.el(f'<div style="font-size:34px;font-weight:900;color:{PINK}">REST</div><div style="font-size:28px;font-weight:700;color:{GREY}">one architectural style</div>', 920, 480, 450, 190,
         style=f"border:4px solid {PINK};border-radius:28px;padding:20px 28px;background:{hexa(PINK, .08)};box-sizing:border-box", anim="pop", t=S.t(key, "REST") if False else S.t(key, "architectural") - 0.4)
    S.note("REST is one style of web API", 110, 340, YEL, 62, w=640, t=S.t(key, "architectural"))
    S.write()


def beat_m2():
    mistake("m2", "x2", 2, "RESPONSE COPIES THE DATABASE", ['{ "usr_nm_v2": "Priya" }', '', 'rename the column…'], "RESPONSE IS THE CONTRACT",
            ['{ "name": "Priya" }', '', 'columns change, clients don\'t'], "design the contract first, then the code", "every client breaks", "Copying", "Design")


def beat_m3():
    mistake("m3", "x3", 3, "ERROR HIDDEN IN A 200", ['HTTP/1.1 <span class="g">200 OK</span>', '{ "error": "not found" }'], "STATUS CODE TELLS THE TRUTH",
            ['HTTP/1.1 <span class="o">404 Not Found</span>', '{ "detail": "User not found" }'], "the status code is part of the contract", "clients think it worked", "Returning", "status")


def beat_m4():
    S = sc("m4", "svg_flow", pill="a UI consumes an API")
    key = "x4"
    S.text("Mistake 4", 110, 80, 700, size=96, color=YEL, t=S.t(key, "Mistake") - 0.05, anim="slam")
    S.box(110, 300, 420, 140, CYAN, "Website", None, tsize=40, t=S.t(key, "website"))
    S.box(110, 480, 420, 140, PINK, "Mobile app", None, tsize=40, t=S.t(key, "mobile"))
    S.box(760, 330, 440, 260, LIME, "The API", "the contract", tsize=52, t=S.t(key, "consumes") - 0.3)
    S.box(1420, 330, 400, 260, SLATE, "Everything else", "logic · data · services", dashed=True, tsize=40, t=S.t(key, "system"))
    S.arrow(540, 370, 750, 440, GREY, t=S.t(key, "consumes"))
    S.arrow(540, 550, 750, 480, GREY, t=S.t(key, "consumes") + 0.1)
    S.arrow(1210, 460, 1410, 460, GREY, t=S.t(key, "consumes") + 0.2)
    S.chip("API ≠ the whole system", 760, 190, RED, ink=False, size=36, t=S.t(key, "system"))
    S.write()


def beat_m5():
    S = sc("m5", "svg_compare", pill="document the contract")
    key = "x5"
    S.text("Mistake 5", 110, 80, 700, size=96, color=YEL, t=S.t(key, "mistake") - 0.05, anim="slam")
    S.box(110, 250, 760, 260, RED, "undocumented", "callers reverse-engineer your behavior", dashed=True, tsize=48, t=S.t(key, "Leaving"))
    S.text("???", 110, 540, 760, size=120, color=RED, align="center", t=S.t(key, "reverse"), anim="slam")
    lines = [f'<span class="f">GET</span> /openapi.json', f'<span class="f">GET</span> /docs', f'<span class="m">generated from your code</span>']
    S.code(1010, 250, 800, lines, "FastAPI · OpenAPI", size=36, lh=58, times=[S.t(key, "Part"), S.t(key, "Part") + .3, S.t(key, "covers")])
    S.chip("Part 3 · OpenAPI", 1010, 560, LIME, size=40, t=S.t(key, "Part"))
    S.write()


def beat_rec():
    S = sc("rec", "recap_grid", pill="one contract, many callers")
    S.text("RECAP", 110, 80, 700, size=96, color=YEL, t=S.t("n1", "recap"), anim="slam")
    items = [("n2", "contract", "An API is a contract", CYAN), ("n3", "request", "A web API is a request + a response", LIME), ("n4", "free", "The server behind it can change", PINK),
             ("n5", "caller", "Anyone can call it, even an AI", ORG), ("n6", "protect", "Your job: protect the contract", RED)]
    pos = [(110, 250), (700, 250), (1290, 250), (400, 520), (990, 520)]
    for i, ((k, ph, txt, col), (x, y)) in enumerate(zip(items, pos)):
        S.box(x, y, 520, 230, col, f"{i + 1}", txt, tsize=64, t=S.t(k), sfx="pop")
    S.write()


def beat_out():
    S = sc("out", "end_screen", pill=None)
    S.el(f'<svg width="170" height="170" viewBox="0 0 300 300"><circle cx="150" cy="150" r="136" fill="none" stroke="{YEL}" stroke-width="10"/>'
         f'<text x="150" y="182" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="92" fill="{YEL}">&lt;/&gt;</text></svg>', 110, 110, anim="fade", t=0.1)
    S.text("API Engineering Handbook", 330, 150, 700, size=48, color="#fff", t=0.2)
    S.box(110, 340, 860, 150, CYAN, "Next: Part 1", "How the Internet Works", tsize=48, t=S.t("o1", "Part"))
    S.box(110, 520, 860, 190, LIME, "Try it yourself", "add GET /users · what if the database is empty?", tsize=44, t=S.t("o2", "exercise"))
    S.chip("Subscribe", 110, 760, PINK, ink=False, size=50, t=S.t("o3", "Subscribe"), sfx="thunk")
    S.write()


for fn in (beat_hook, beat_road, beat_c1a, beat_c1b, beat_c1c, beat_c2a, beat_c2b, beat_c2b2, beat_c2c, beat_c2e, beat_c2d, beat_c3m, beat_c3a, beat_c3b, beat_c3c, beat_c4a, beat_c4b,
           beat_m1, beat_m2, beat_m3, beat_m4, beat_m5, beat_rec, beat_out):
    fn()

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
