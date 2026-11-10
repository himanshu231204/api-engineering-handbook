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
