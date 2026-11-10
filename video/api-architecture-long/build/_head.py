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


