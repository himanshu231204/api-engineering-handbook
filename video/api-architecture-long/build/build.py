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
        t = max(t, 0.0)     # a negative start would shift the whole scene timeline (GSAP smoothChildTiming)
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
        self.js.append(f'A("{cid}","fade",{max(times[0] - 0.25, 0) if times else 0},{"null" if out is None else out});')
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

    def svg_reveal(self, path, x, y, scale, axis, steps, out=None, glow=None, view_h=None, pan=None, sticky=None):
        """Inline a repo SVG / rendered Mermaid SVG (path relative to hf/) and reveal it step by step.
        axis 'y' = top-to-bottom, 'x' = left-to-right; steps = [(local_time, svg_units_revealed)]."""
        svg = open(f"{HF}/{path}").read()
        vb = re.search(r'viewBox="([\-\d\.]+) ([\-\d\.]+) ([\d\.]+) ([\d\.]+)"', svg)
        vw, vh = float(vb.group(3)), float(vb.group(4))
        w, h = vw * scale, vh * scale
        svg = re.sub(r"<svg ", f'<svg style="width:{w:.0f}px;height:{h:.0f}px;display:block;overflow:visible" ', svg, count=1)
        i = self.uid()
        if view_h:   # tall diagram inside a fixed window: the inner element can be panned (pan=[(local_time, y_px_offset)])
            vp = self.uid()
            hh = round(sticky * scale) if sticky else 0     # sticky = height (svg units) of a header strip that stays pinned while the body pans
            if sticky:
                hid = self.uid()
                hsvg = svg.replace('id="', 'id="h-').replace('url(#', 'url(#h-')
                self.h.append(f'<div id="{hid}" class="el" style="left:{x}px;top:{y}px;width:{w:.0f}px;height:{hh}px;overflow:hidden"><div style="position:absolute;left:0;top:0;width:{w:.0f}px;height:{h:.0f}px">{hsvg}</div></div>')
                sticky_id = hid
            self.h.append(f'<div id="{vp}" style="position:absolute;left:{x}px;top:{y + hh}px;width:{w:.0f}px;height:{view_h - hh}px;overflow:hidden">'
                          f'<div id="{i}" class="el" style="left:0px;top:{-hh}px;width:{w:.0f}px;height:{h:.0f}px">{svg}</div></div>')
        else:
            self.h.append(f'<div id="{i}" class="el" style="left:{x}px;top:{y}px;width:{w:.0f}px;height:{h:.0f}px">{svg}</div>')
        total = vh if axis == "y" else vw
        def clip(u):
            r = max(0.0, 100.0 * (1 - u / total))
            return f"inset(0 0 {r:.2f}% 0)" if axis == "y" else f"inset(0 {r:.2f}% 0 0)"
        full = "inset(0 0 100% 0)" if axis == "y" else "inset(0 100% 0 0)"
        # two reveal steps must never share a start time (the later clip-path tween would override the earlier one)
        fixed = [steps[0]]
        for ts_, us_ in steps[1:]:
            fixed.append((max(ts_, fixed[-1][0] + 0.2), us_))
        steps = fixed
        t0, u0 = steps[0]
        self.js.append(f'tl.fromTo("#{i}",{{opacity:1,clipPath:"{full}"}},{{opacity:1,clipPath:"{clip(u0)}",duration:.5,ease:"power2.out"}},{t0});')
        for (ta, ua), (tb, ub) in zip(steps, steps[1:]):
            self.js.append(f'tl.fromTo("#{i}",{{clipPath:"{clip(ua)}"}},{{clipPath:"{clip(ub)}",duration:.5,ease:"power2.out",immediateRender:false}},{tb});')
        if view_h and sticky:
            self.js.append(f'tl.fromTo("#{sticky_id}",{{opacity:0}},{{opacity:1,duration:.4}},{t0});')
            if out is not None:
                self.js.append(f'tl.fromTo("#{sticky_id}",{{opacity:1}},{{opacity:0,duration:.2,immediateRender:false}},{out});')
        if pan:
            py = 0
            for tp, ny in pan:
                self.js.append(f'tl.fromTo("#{i}",{{y:{py}}},{{y:{ny},duration:.9,ease:"power2.inOut",immediateRender:false}},{tp});')
                py = ny
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
SLATE = "#7C8DA6"
RP = "assets/repo/"          # repo assets inside hf/


def R(x0, y0, k, u, v, w, h, pad=8):
    """Rect of an SVG-local box (u, v, w, h) once the SVG is placed at (x0, y0) with scale k."""
    return (round(x0 + u * k - pad), round(y0 + v * k - pad), round(w * k + 2 * pad), round(h * k + 2 * pad))


def tag(S, text="from the handbook", x=460, t=0.0, out=None):
    S.chip(text, x, 44, LIME, size=30, t=t, out=out)


def beat_hook():
    S = sc("hook", "logo_reveal", pill=None)
    S.el(f'<svg width="300" height="300" viewBox="0 0 300 300"><circle cx="150" cy="150" r="136" fill="none" stroke="{YEL}" stroke-width="10"/>'
         f'<text x="150" y="182" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="92" fill="{YEL}">&lt;/&gt;</text></svg>',
         150, 120, anim="static", style="filter:drop-shadow(0 0 14px rgba(255,229,0,.55))")
    S.text(f'API <span style="color:{YEL}">ARCHITECTURE</span>', 500, 150, 1350, size=118, anim="static")
    S.text("A production API, at a glance.", 506, 320, 1200, size=50, color=GREY, weight=700, anim="static")
    layers = [("Client", CYAN, "browser · app · agent"), ("Edge", LIME, "CDN · load balancer"), ("Gateway", PINK, "auth · rate limits"),
              ("Application", ORG, "the real work"), ("Data + AI", VIO, "DB · cache · queue · LLM")]
    t0 = S.t("h1", "crosses")
    for i, (name, col, sub) in enumerate(layers):
        x = 125 + i * 345
        S.box(x, 520, 290, 210, col, name, sub, tsize=42, t=t0 + i * 0.3)
        if i:
            S.arrow(x - 52, 625, x - 6, 625, GREY, t=t0 + i * 0.3 + 0.1, width=5)
    S.note("the wrong layer = weeks of debugging", 520, 770, ORG, 64, w=1100, t=S.t("h2", "weeks"))
    S.ring(105, 500, 1710, 250, YEL, t=S.t("h3", "name"))
    S.write()


def beat_road():
    S = sc("road", "roadmap", pill=f"5 parts · about {round(TOTAL / 60)} minutes")
    S.text("THE PLAN", 560, 110, 800, size=84, color=YEL, anim="fade", t=S.t("r1", "plan"))
    rows = [("1", "The big map", "r2", "big", CYAN), ("2", "Who does what", "r2", "Two", LIME), ("3", "Three requests", "r2", "three", PINK),
            ("4", "See it run", "r3", "Four", ORG), ("5", "When not to add a layer", "r3", "five", RED)]
    for i, (n, label, key, ph, col) in enumerate(rows):
        y = 250 + i * 108
        S.chip(n, 560, y, col, w=72, size=44, t=S.t(key, ph))
        S.text(label, 664, y + 2, 1000, size=60, anim="fade", t=S.t(key, ph) + 0.05)
    S.write()


# ---------------------------------------------------------------- chapter 1: the big map
def beat_air():
    S = sc("air", "svg_analogy", pill="one narrow job per layer")
    cols = [(140, CYAN, "Check-in", "CDN", "a1", "Check"), (725, LIME, "Security", "API gateway", "a1", "security"), (1310, PINK, "The gate", "application service", "a1", "gate")]
    for x, col, title, real, key, ph in cols:
        S.box(x, 190, 470, 220, col, title, None, tsize=54, t=S.t(key, ph))
    S.arrow(620, 300, 715, 300, GREY, t=S.t("a1", "security") + 0.1)
    S.arrow(1205, 300, 1300, 300, GREY, t=S.t("a1", "gate") + 0.1)
    # a2 maps each airport step to the real layer
    S.chip("CDN", 225, 440, CYAN, w=300, size=44, t=S.t("a2", "C"))
    S.chip("Gateway", 810, 440, LIME, w=300, size=44, t=S.t("a2", "gateway"))
    S.chip("App", 1395, 440, PINK, w=300, size=44, t=S.t("a2", "app"))
    S.box(1050, 610, 340, 130, ORG, "Database", None, tsize=40, t=S.t("a2", "database"))
    S.box(1460, 610, 340, 130, VIO, "AI model", None, tsize=40, t=S.t("a2", "AI"))
    S.arrow(1545, 520, 1250, 600, GREY, t=S.t("a2", "database"), width=5)
    S.arrow(1545, 520, 1630, 600, GREY, t=S.t("a2", "AI"), width=5)
    S.write()


def beat_map():
    S = sc("map", "svg_flow", pill="client → edge → gateway → application → data / AI", assets=["repo/mermaid/api-architecture-layers-td.svg"])
    X0, Y0, K = 160, 120, 1.4
    tag(S, "Mermaid diagram from the handbook chapter", t=S.t("m1", "whole"))
    S.svg_reveal(RP + "mermaid/api-architecture-layers-td.svg", X0, Y0, K, "y",
                 [(S.t("m1", "Here"), 82), (S.t("m2", "C"), 172), (S.t("m2", "gateway"), 284), (S.t("m2", "application"), 372),
                  (S.t("m3", "four"), 480)])
    nodes = [("cache", 8, 424, 165, 48, LIME), ("database", 213, 424, 254, 48, CYAN), ("message", 507, 424, 283, 48, ORG), ("AI", 830, 424, 305, 48, VIO)]
    for i, (ph, u, v, w, h, col) in enumerate(nodes):
        t0 = S.t("m3", ph)
        t1 = S.t("m3", nodes[i + 1][0]) - 0.05 if i + 1 < len(nodes) else None
        S.ring(*R(X0, Y0, K, u - 4, v - 4, w, h), col, t=t0, out=t1)
    S.write()


def beat_lay():
    S = sc("lay", "svg_flow", pill="five layers, one narrow job each", assets=["repo/mermaid/api-architecture-layers-lr.svg"])
    K = 1.1
    X0, Y0 = round((1920 - 1524 * K) / 2), 100
    tag(S, "Mermaid diagram from the handbook chapter", t=S.t("l1", "chapter"))
    S.svg_reveal(RP + "mermaid/api-architecture-layers-lr.svg", X0, Y0, K, "x", [(S.t("l1", "chapter"), 420), (S.t("l1", "layers"), 1524)])
    # (u, v, w, h) of each cluster in SVG units, from the rendered diagram; chip sits above ("up") or to the left ("left") of its ring
    L_ = [("Edge", 4, 242, 376, 123, CYAN, "EDGE", "up"), ("Gateway", 440, 242, 200, 123, LIME, "GATEWAY", "up"),
          ("Application", 760, 150, 200, 221, PINK, "APPLICATION", "up"), ("Data", 1100, 4, 212, 387, ORG, "DATA", "left"),
          ("AI", 1100, 431, 412, 221, VIO, "AI", "left")]
    for i, (ph, u, v, w, h, col, label, side) in enumerate(L_):
        t0 = S.t("l2", ph)
        t1 = S.t("l2", L_[i + 1][0]) - 0.05 if i + 1 < len(L_) else None
        rx, ry, rw, rh = R(X0, Y0, K, u, v, w, h)
        cx, cy = (rx, ry - 66) if side == "up" else (rx - 230, ry + 40)
        S.ring(rx, ry, rw, rh, col, t=t0, out=t1)
        S.chip(label, cx, cy, col, size=34, ink=(col != VIO), t=t0, out=t1)
    S.write()


# ---------------------------------------------------------------- chapter 2: who does what
def beat_org():
    S = sc("org", "svg_icons", pill="a company org chart, not one person doing everything")
    S.text("THE ORG CHART", 110, 100, 1000, size=80, color=YEL, t=S.t("o1", "company"))
    items = [(110, 220, CYAN, "Receptionist", "CDN · cached answers", "o2", "receptionist"), (700, 220, LIME, "Security + routing", "API gateway", "o3", "gateway"),
             (1290, 220, PINK, "The department", "application service", "o4", "application"), (110, 500, ORG, "Filing cabinet", "database", "o4", "database"),
             (700, 500, SLATE, "Ticket system", "message queue", "o5", "queue"), (1290, 500, VIO, "Specialist team", "AI gateway", "o5", "AI")]
    for x, y, col, title, sub, key, ph in items:
        S.box(x, y, 520, 240, col, title, sub, tsize=52, t=S.t(key, ph))
    S.write()


def beat_gw():
    S = sc("gw", "svg_diagram", pill="one front door for every client", assets=["repo/svg/11-api-gateway.svg"])
    X0, Y0, K = 322, 72, 1.45
    tag(S, "from the handbook · Part 11", t=S.t("g1", "Zoom"))
    S.svg_reveal(RP + "svg/11-api-gateway.svg", X0, Y0, K, "y",
                 [(S.t("g1", "Zoom"), 76), (S.t("g1", "front"), 200), (S.t("g1", "address"), 392), (S.t("g3", "Fail"), 480), (S.t("g4", "dumb"), 560)])
    steps = [("authenticate", (288, 196, 268, 50), CYAN), ("rate", (288, 256, 268, 50), LIME), ("route", (288, 316, 268, 50), PINK)]
    for i, (ph, box, col) in enumerate(steps):
        t0 = S.t("g2", ph)
        t1 = S.t("g2", steps[i + 1][0]) - 0.05 if i + 1 < len(steps) else S.t("g3", "Fail") - 0.05
        S.ring(*R(X0, Y0, K, *box, pad=6), col, t=t0, out=t1)
    S.ring(*R(X0, Y0, K, 272, 412, 140, 52, pad=6), RED, t=S.t("g3", "four"), out=None)
    S.ring(*R(X0, Y0, K, 432, 412, 140, 52, pad=6), ORG, t=S.t("g3", "twenty"), out=None)
    S.ring(*R(X0, Y0, K, 32, 504, 816, 40, pad=6), YEL, t=S.t("g4", "dumb") + 0.3)
    S.write()


def beat_cache():
    S = sc("cache", "svg_diagram", pill="cache-aside: check the cache first", assets=["repo/svg/07-cache-aside.svg"])
    X0, Y0, K = 256, 80, 1.6
    tag(S, "from the handbook · Part 7", t=S.t("c1", "cache"))
    S.svg_reveal(RP + "svg/07-cache-aside.svg", X0, Y0, K, "y",
                 [(S.t("c1", "cache"), 76), (S.t("c1", "Reads"), 180), (S.t("c2", "miss"), 310), (S.t("c3", "write"), 470), (S.t("c3", "stale"), 500)])
    S.ring(*R(X0, Y0, K, 620, 112, 228, 64, pad=6), LIME, t=S.t("c2", "hit"), out=S.t("c2", "miss") - 0.05)
    S.ring(*R(X0, Y0, K, 380, 228, 468, 76, pad=6), ORG, t=S.t("c2", "miss") + 0.2)
    S.ring(*R(X0, Y0, K, 32, 332, 816, 120, pad=6), PINK, t=S.t("c3", "delete"))
    S.write()


def beat_queue():
    S = sc("queue", "svg_diagram", pill="answer fast, work later", assets=["repo/svg/08-message-queue.svg"])
    X0, Y0, K = 278, 76, 1.55
    tag(S, "from the handbook · Part 8", t=S.t("q1", "queue"))
    S.svg_reveal(RP + "svg/08-message-queue.svg", X0, Y0, K, "y",
                 [(S.t("q1", "queue"), 76), (S.t("q2", "validates"), 250), (S.t("q3", "Workers"), 380), (S.t("q4", "buys"), 512)])
    S.write()


def beat_ai():
    S = sc("ai", "svg_diagram", pill="one front door for every model call", assets=["repo/svg/15-llm-gateway.svg"])
    X0, Y0, K = 190, 100, 1.75
    tag(S, "from the handbook · Part 15", t=S.t("i1", "AI"))
    S.svg_reveal(RP + "svg/15-llm-gateway.svg", X0, Y0, K, "y", [(S.t("i1", "AI"), 76), (S.t("i1", "front"), 200), (S.t("i1", "Your"), 440)])
    S.ring(*R(X0, Y0, K, 272, 92, 336, 316, pad=6), LIME, t=S.t("i2", "handles"), out=S.t("i2", "down") - 0.05)
    S.ring(*R(X0, Y0, K, 678, 116, 170, 268, pad=6), VIO, t=S.t("i2", "down"))
    S.write()


# ---------------------------------------------------------------- chapter 3: three requests
def beat_read():
    S = sc("read", "svg_flow", pill="GET /products/9", assets=["repo/mermaid/api-request-flow.svg"])
    X0, Y0, K, VH = 147, 98, 1.3, 790
    tag(S, "Mermaid diagram · diagrams/api-request-flow.md", t=S.t("d1", "Request"))
    S.svg_reveal(RP + "mermaid/api-request-flow.svg", X0, Y0, K, "y",
                 [(S.t("d1", "Request"), 92), (S.t("d1", "hits"), 138),
                  (S.t("d3", "If"), 178), (S.t("d3", "authenticates"), 245), (S.t("d3", "routes"), 292),
                  (S.t("d4", "checks"), 332), (S.t("d4", "hit"), 442), (S.t("d4", "miss"), 602),
                  (S.t("d5", "Then"), 652), (S.t("d5", "retraces"), 697), (S.t("d5", "back"), 742), (S.t("d5", "client") + 0.3, 776)],
                 view_h=VH, sticky=92, pan=[(S.t("d4", "miss"), -170), (S.t("d5", "Then") - 0.3, -300)])
    t_cdn = S.t("d2", "C")
    S.ring(*R(X0, Y0, K, 246, 8, 170, 74, pad=6), LIME, t=t_cdn, out=S.t("d3", "If") - 0.05)
    S.chip("cached at the edge: done", 640, 290, LIME, size=34, t=t_cdn, out=S.t("d3", "If") - 0.05)
    S.write()


def beat_write():
    S = sc("write", "svg_diagram", pill="POST /orders", assets=["repo/svg/18-request-flow.svg"])
    X0, Y0, K = 322, 72, 1.45
    tag(S, "from the handbook · Part 18", t=S.t("w1", "Request"))
    S.svg_reveal(RP + "svg/18-request-flow.svg", X0, Y0, K, "y",
                 [(S.t("w1", "Request"), 76), (S.t("w2", "passes"), 210), (S.t("w3", "validates"), 355), (S.t("w3", "message") + 0.2, 410), (S.t("w4", "two"), 480), (S.t("w4", "client") - 0.3, 560)])
    S.ring(*R(X0, Y0, K, 366, 90, 148, 114, pad=6), CYAN, t=S.t("w2", "isn't"), out=S.t("w3", "validates") - 0.05)
    boxes = [("commits", 533, PINK), ("updates", 366, ORG), ("publishes", 199, VIO)]
    for i, (ph, u, col) in enumerate(boxes):
        t0 = S.t("w3", ph)
        t1 = S.t("w3", boxes[i + 1][0]) - 0.05 if i + 1 < len(boxes) else S.t("w4", "two") - 0.05
        S.ring(*R(X0, Y0, K, u, 236, 148, 114, pad=6), col, t=t0, out=t1)
    S.ring(*R(X0, Y0, K, 32, 236, 148, 114, pad=6), VIO, t=S.t("w4", "worker"))
    S.write()


TRACE = [
    ('<span class="n">1.</span> Client → <span class="k">POST</span> <span class="f">/chat</span>  {<span class="s">"message"</span>: <span class="s">"Summarize this doc"</span>}'),
    ('<span class="n">2.</span> <span class="d">Gateway</span> validates JWT, checks rate limit'),
    ('<span class="n">3.</span> <span class="g">App service</span> loads conversation from Postgres, checks Redis cache for recent context'),
    ('<span class="n">4.</span> <span class="g">App service</span> calls <span class="k">AI Gateway</span>'),
    ('<span class="n">5.</span> <span class="k">AI Gateway</span> routes to an available LLM provider (with a fallback if the primary is down)'),
    ('<span class="n">6.</span> Response streams back through App service → Gateway → Client'),
    ('<span class="n">7.</span> App service asynchronously logs the interaction and updates usage/cost tracking via a queue'),
]


def beat_chat():
    S = sc("chat", "code_card", pill="POST /chat: seven steps", assets=["harvest/code/block1.txt"])
    tt = [S.t("t1", "Request"), S.t("t2", "gateway"), S.t("t2", "app"), S.t("t3", "AI"), S.t("t3", "routes"), S.t("t4", "streams"), S.t("t5", "logging")]
    cid, ids, (y0, lh) = S.code(60, 140, 1800, TRACE, "request trace · docs/00-introduction/api-architecture.md", size=30, lh=74, times=tt)
    S.hl(60, y0, lh, 1800, [(tt[0], 0), (tt[1], 1), (tt[2], 2), (tt[3], 3), (tt[4], 4), (tt[5], 5), (tt[6], 6)])
    S.chip("the handbook's own trace", 460, 44, LIME, size=30, t=tt[0])
    S.write()


def beat_sum():
    S = sc("sum", "svg_compare", pill="same map, three different paths")
    rows = [("GET /products/9", 170, [("CDN", LIME)], "read", "u1"),
            ("POST /orders", 350, [("CDN", LIME), ("Gateway", PINK), ("App", ORG), ("Database", CYAN), ("Queue", SLATE)], "write", "u1"),
            ("POST /chat", 530, [("Gateway", PINK), ("App", ORG), ("AI gateway", VIO), ("Provider", VIO), ("Queue", SLATE)], "chat", "u1")]
    for label, y, chain, ph, key in rows:
        t0 = S.t(key, ph)
        S.text(label, 110, y + 22, 420, size=40, color="#fff", weight=900, style="font-family:'JetBrains Mono',monospace", t=t0)
        for i, (name, col) in enumerate(chain):
            x = 560 + i * 250
            S.box(x, y, 210, 96, col, name, None, tsize=32, t=t0 + 0.12 * (i + 1), sfx=None)
            if i:
                S.arrow(x - 38, y + 48, x - 4, y + 48, GREY, t=t0 + 0.12 * (i + 1), width=4)
    S.chip("a read can stop here", 820, 190, LIME, size=34, t=S.t("u1", "stop"))
    S.write()


# ---------------------------------------------------------------- chapter 4: see it run
ROUTE = [
    f'PROVIDER_PRIORITY = [<span class="f">UnreliableTestAdapter</span>(), <span class="f">ProviderAAdapter</span>(), <span class="f">ProviderBAdapter</span>()]',
    f'rate_limiter = <span class="f">TokenBucketRateLimiter</span>(capacity=<span class="n">5</span>, refill_rate=<span class="n">1.0</span>)',
    f'<span class="c"># …</span>',
    f'<span class="k">if</span> <span class="k">not</span> <span class="k">await</span> rate_limiter.<span class="f">allow</span>():',
    f'    <span class="k">raise</span> <span class="f">HTTPException</span>(status_code=<span class="n">429</span>, detail=<span class="s">"rate limit exceeded, try again shortly"</span>)',
    f'<span class="c"># …</span>',
    f'cost_usd = <span class="f">compute_cost_usd</span>(result)',
]


def beat_route():
    S = sc("route", "code_card", pill="examples/llm-gateway", assets=["examples/llm-gateway/main.py"])
    cid, ids, (y0, lh) = S.code(160, 130, 1600, ROUTE, "examples/llm-gateway/main.py  ·  excerpt", size=28, lh=60, times=[S.t("v1", "handbook"), S.t("v1b", "token"), S.t("v1b", "refilling"), S.t("v2", "Over"), S.t("v2", "Over") + 0.25, S.t("v2", "every"), S.t("v2", "cost")])
    S.hl(160, y0, lh, 1600, [(S.t("v1b", "providers"), 0), (S.t("v1b", "token"), 1), (S.t("v2", "Over"), 3), (S.t("v2", "Over") + 0.3, 4), (S.t("v2", "cost"), 6)])
    S.chip("providers, in priority order", 160, 700, CYAN, size=34, t=S.t("v1b", "providers"))
    S.chip("5 requests, refill 1 per second", 700, 700, LIME, size=34, t=S.t("v1b", "token"))
    S.chip("over the limit → 429", 1300, 700, ORG, size=34, t=S.t("v2", "Over"))
    S.chip("a cost on every response", 160, 780, PINK, size=34, t=S.t("v2", "cost"))
    S.write()


def beat_run1():
    S = sc("run1", "terminal_clip", pill="real run · commands trimmed", assets=["demo/real_output.txt"])
    lines = [f'<span class="g">$</span> for i in 1 2 3 4 5; do curl -s -X POST localhost:8000/chat <span class="m">…</span>; done',
             f'<span class="f">flaky_test_provider</span> <span class="n">0.0</span>', f'<span class="f">flaky_test_provider</span> <span class="n">0.0</span>',
             f'<span class="f">flaky_test_provider</span> <span class="n">0.0</span>', f'<span class="f">flaky_test_provider</span> <span class="n">0.0</span>',
             f'<span class="k">provider_a</span> <span class="n">0.000228</span>',
             f'<span class="g">$</span> curl -s localhost:8000/usage',
             f'{{<span class="s">"acme_corp"</span>:{{<span class="s">"requests"</span>:<span class="n">5</span>,<span class="s">"total_cost_usd"</span>:<span class="n">0.000228</span>}}}}']
    t_cmd, t_out, t_fb, t_use = S.t("e1", "Five"), S.t("e1", "Four"), S.t("e2", "fifth"), S.t("e3", "usage")
    times = [t_cmd, t_out, t_out + 0.3, t_out + 0.6, t_out + 0.9, t_fb, t_use, t_use + 0.4]
    cid, ids, (y0, lh) = S.code(110, 130, 1340, lines, "terminal · real output of examples/llm-gateway", size=30, lh=62, times=times, bg="#000000")
    S.hl(110, y0, lh, 1340, [(t_out, 1), (t_out + 0.9, 4), (t_fb, 5), (S.t("e2", "fell"), 5), (t_use + 0.4, 7)])
    S.chip("4 × first provider", 1490, 250, CYAN, size=30, t=t_out)
    S.chip("1 × fell back to A", 1490, 350, PINK, size=30, ink=False, t=t_fb)
    S.chip("only A costs money", 1490, 450, LIME, size=30, t=S.t("e2", "costs"))
    S.write()


def beat_run2():
    S = sc("run2", "terminal_clip", pill="real run · a burst of 8 requests", assets=["demo/real_output.txt"])
    codes = ["200"] * 5 + ["429"] * 3
    lines = [f'<span class="g">$</span> for i in $(seq 1 8); do curl <span class="m">…</span> -w "%{{http_code}}\\n" <span class="m">…</span>; done'] + \
            [f'<span class="{"g" if c == "200" else "o"}">{c}</span>' for c in codes]
    t_cmd, t_ok, t_429 = S.t("f1", "burst"), S.t("f1", "first"), S.t("f1", "next")
    times = [t_cmd] + [t_ok + 0.18 * i for i in range(5)] + [t_429 + 0.22 * i for i in range(3)]
    cid, ids, (y0, lh) = S.code(110, 120, 1340, lines, "terminal · real output of examples/llm-gateway", size=30, lh=62, times=times, bg="#000000")
    S.hl(110, y0, lh, 1340, [(t_429, 6), (t_429 + 0.5, 8)])
    S.chip("5 pass", 1490, 270, LIME, size=34, t=t_ok)
    S.chip("3 rejected: 429", 1490, 370, ORG, size=34, t=t_429)
    S.chip("at the gateway", 1490, 470, RED, size=32, ink=False, t=S.t("f1", "right"))
    S.write()


# ---------------------------------------------------------------- chapter 5: don't over-build
def beat_simple():
    S = sc("simple", "svg_compare", pill="every layer has a price")
    S.text("NOT EVERY API NEEDS EVERY LAYER", 110, 100, 1700, size=74, color=YEL, t=S.t("s1", "Now"))
    out = S.t("s3", "Each") - 0.05
    S.box(150, 290, 420, 190, CYAN, "Client", None, tsize=48, t=S.t("s1", "small"), out=out)
    S.box(740, 290, 440, 190, LIME, "App service", None, tsize=48, t=S.t("s1", "application"), out=out)
    S.box(1350, 290, 420, 190, ORG, "Database", None, tsize=48, t=S.t("s1", "database"), out=out)
    S.arrow(580, 385, 730, 385, GREY, t=S.t("s1", "application") + 0.1, out=out)
    S.arrow(1190, 385, 1340, 385, GREY, t=S.t("s1", "database") + 0.1, out=out)
    S.chip("the right architecture at that scale", 460, 560, LIME, size=40, t=S.t("s1", "right"), out=out)
    rows = [("Cache", "buys latency", CYAN, "Cache"), ("Gateway", "buys central auth + rate limits", LIME, "Gateway"), ("Queue", "buys resilience to slow work", PINK, "Queue")]
    for i, (a, b, col, ph) in enumerate(rows):
        y = 250 + i * 130
        S.chip(a, 150, y, col, w=300, size=48, t=S.t("s3", ph))
        S.text(b, 500, y + 4, 1200, size=54, color="#fff", t=S.t("s3", ph) + 0.1)
    S.chip("the price: more moving parts · more failure modes · more to operate", 150, 660, RED, size=38, ink=False, t=S.t("s3", "price"))
    S.write()


def beat_x1():
    mistake("x1", "x1", 1, "EVERY LAYER, DAY ONE", ['CDN · gateway', 'cache · queue'], "ONE REAL PROBLEM, ONE LAYER", ['slow reads → a cache', 'problem first, layer second'],
            "every layer on day one", "more parts, nothing gained", "Assuming", "Add")


def beat_x2():
    mistake("x2", "x2", 2, "MICROSERVICES = BETTER?", ['split everything', '"more production grade"'], "FIT THE PROBLEM", ['a well built monolith', 'can be the right answer'],
            "it depends on the problem · Part 11", "not automatically better", "Treating", "depends")


def beat_x3():
    mistake("x3", "x3", 3, "AI AS AN AFTERTHOUGHT", ['bolted onto the API', 'no timeouts · no fallback'], "AI AS ITS OWN LAYER", ['timeouts · fallbacks', 'cost tracking'],
            "slow · can fail · costs per call", "outages and bills surprise you", "Bolting", "needs")


def beat_aip():
    S = sc("aip", "svg_compare", pill="the AI layer has different failure and cost")
    out = S.t("y3", "So") - 0.05
    S.box(110, 130, 800, 230, CYAN, "Database query", "usually fast · predictable", tsize=56, t=S.t("y1", "database"), out=out)
    S.box(1010, 130, 800, 230, VIO, "Model call", "slow · non-deterministic · metered by usage", tsize=56, t=S.t("y1", "model"), out=out)
    S.note("same pattern, very different failure and cost", 260, 420, YEL, 66, w=1400, t=S.t("y1", "usage") + 0.2, out=out)
    S.text("PARTS 14–17 ADD", 110, 120, 900, size=70, color=YEL, t=S.t("y3", "So"))
    items = [("LLM gateways", CYAN, "gateways"), ("Token rate limits", LIME, "token"), ("Prompt caching", PINK, "prompt"), ("Semantic caching", ORG, "semantic")]
    for i, (name, col, ph) in enumerate(items):
        S.box(110 + (i % 2) * 900, 280 + (i // 2) * 210, 800, 170, col, name, None, tsize=54, t=S.t("y3", ph))
    S.write()


# ---------------------------------------------------------------- chapter 6: recap
def beat_rec():
    S = sc("rec", "recap_grid", pill="layers earn their place")
    S.text("RECAP", 110, 80, 700, size=96, color=YEL, t=S.t("n1", "recap"), anim="slam")
    items = [("n2", "A layered system", "client → edge → gateway → app → data / AI", CYAN, 150, 220), ("n3", "One narrow job each", "different requests, different paths", LIME, 1010, 220),
             ("n4", "Add a layer for a real problem", "and treat the AI layer like the database", PINK, 150, 500), ("n6", "Bookmark Part 18", "the full production map", ORG, 1010, 500)]
    for i, (k, title, sub, col, x, y) in enumerate(items):
        S.box(x, y, 760, 240, col, title, sub, tsize=52, t=S.t(k), sfx="pop")
    S.write()


def beat_quiz():
    S = sc("quiz", "quiz_card", pill="Check yourself")
    S.chip("CHECK YOURSELF", 460, 44, YEL, size=30, t=S.t("z1", "Quick"))
    S.el(f'<div style="font-size:30px;font-weight:900;color:{CYAN};letter-spacing:.08em">QUESTION 3 · FROM THE CHAPTER</div>'
         f'<div style="font-size:50px;font-weight:700;line-height:1.28;margin-top:14px">A <span style="color:{YEL}">POST /orders</span> request must also send a confirmation email. How do you avoid making the client wait for it?</div>',
         160, 130, 1600, style=f"border:2px solid {CYAN};border-radius:26px;padding:34px 44px;background:{hexa(CYAN, .07)};box-shadow:0 0 30px {hexa(CYAN, .25)};box-sizing:border-box", anim="fade", t=S.t("z1", "Quick"))
    S.note("pause and answer…", 180, 440, YEL, 70, w=700, t=S.t("z2", "Pause"), out=S.t("z2", "Put") - 0.05)
    S.el(f'<div style="font-size:30px;font-weight:900;color:{LIME};letter-spacing:.08em">ANSWER</div>'
         f'<div style="font-size:48px;font-weight:700;line-height:1.28;margin-top:12px">Put the email on a <span style="color:{YEL}">queue</span> as a background job.</div>',
         160, 440, 1600, style=f"border:2px solid {LIME};border-radius:26px;padding:34px 44px;background:{hexa(LIME, .07)};box-shadow:0 0 30px {hexa(LIME, .25)};box-sizing:border-box", anim="fade", t=S.t("z2", "Put"))
    for i, (txt, col, ph) in enumerate([("save the order", CYAN, "Put"), ("respond 201", LIME, "queue"), ("worker sends the email", PINK, "worker")]):
        S.chip(txt, 160 + [0, 500, 960][i], 680, col, size=38, t=S.t("z2", ph) + [0.6, 1.2, 0][i])
    S.write()


def beat_out():
    S = sc("out", "end_screen", pill=None)
    S.el(f'<svg width="170" height="170" viewBox="0 0 300 300"><circle cx="150" cy="150" r="136" fill="none" stroke="{YEL}" stroke-width="10"/>'
         f'<text x="150" y="182" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="92" fill="{YEL}">&lt;/&gt;</text></svg>', 110, 110, anim="fade", t=0.1)
    S.text("API Engineering Handbook", 330, 150, 700, size=48, color="#fff", t=0.2)
    S.box(110, 340, 860, 150, CYAN, "Next: Learning Roadmap", "a guided path through all 20 parts", tsize=46, t=S.t("p1", "Next"))
    S.box(110, 520, 860, 190, LIME, "Try it yourself", "layers for GET /orders/{id} · food delivery app", tsize=44, t=S.t("p2", "exercise"))
    S.chip("Subscribe", 110, 760, PINK, ink=False, size=50, t=S.t("p3", "Subscribe"), sfx="thunk")
    S.write()


def mistake(bid, key, n, bad_title, bad_lines, good_title, good_lines, pill, bad_note, ph_bad, ph_good):
    S = sc(bid, "svg_compare", pill=pill)
    S.text(f"Mistake {n}", 110, 80, 700, size=96, color=YEL, weight=900, t=S.t(key, "Mistake") - 0.05, anim="slam")

    def card(x, color, mark, title, lines, tt):
        h = 130 + 72 * len(lines)
        inner = f'<div style="font-size:32px;font-weight:900;color:{color};letter-spacing:.06em">{mark} {title}</div>' + "".join(f'<div class="mono" style="font-size:40px;margin-top:22px;line-height:1.25">{l}</div>' for l in lines)
        S.el(inner, x, 250, 800, h, style=f"border:4px solid {color};border-radius:26px;padding:28px 36px;background:{hexa(color, .08)};box-shadow:0 0 28px {hexa(color, .28)};box-sizing:border-box", anim="fade", t=tt, sfx="pop")
    card(110, RED, "✗", bad_title, bad_lines, S.t(key, ph_bad))
    card(1010, LIME, "✓", good_title, good_lines, S.t(key, ph_good))
    S.note(bad_note, 130, 640, ORG, 70, w=800, t=S.t(key, ph_bad) + 0.6)
    S.write()


for fn in (beat_hook, beat_road, beat_air, beat_map, beat_lay, beat_org, beat_gw, beat_cache, beat_queue, beat_ai, beat_read, beat_write, beat_chat, beat_sum,
           beat_route, beat_run1, beat_run2, beat_simple, beat_x1, beat_x2, beat_x3, beat_aip, beat_rec, beat_quiz, beat_out):
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
