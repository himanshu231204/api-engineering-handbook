#!/usr/bin/env python3
"""Harvest a handbook chapter into video-ready assets.

usage: harvest_chapter.py docs/<part>/<chapter>.md OUT_DIR

Writes OUT_DIR/harvest.json plus:
  mermaid/*.mmd + *.svg   every ```mermaid block, rendered neon-on-black (mermaid_to_svg.py)
  svg/*.svg               every concept SVG the chapter embeds, converted to dark (repo_svg_to_dark.py)
  code/*                  every fenced code block (python/http/json/bash), exactly as written
and prints a short report: title, TL;DR, quiz, related glossary / cheatsheet / example / exercise hits.
"""
import json, os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.abspath(os.path.join(here, "..", ".."))
chap, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
text = open(chap).read()
rel = os.path.relpath(chap, repo)
for d in ("mermaid", "svg", "code"): os.makedirs(f"{out}/{d}", exist_ok=True)
H = {"chapter": rel, "title": re.search(r"^# (.+)$", text, re.M).group(1)}
tldr = re.search(r"> \[!TIP\]\n((?:>.*\n?)+)", text)
if tldr:
    t = re.sub(r"^> ?", "", tldr.group(1), flags=re.M)
    for k in ("In one line", "In plain English", "You'll be able to"):
        m = re.search(rf"\*\*{k}:\*\*\s*(.+?)(?:\n\n|\Z)", t, re.S)
        if m: H.setdefault("tldr", {})[k] = " ".join(m.group(1).split())
# sections
secs = re.split(r"^## ", text, flags=re.M)[1:]
H["sections"] = [s.split("\n", 1)[0].strip() for s in secs]
# mermaid + code fences
H["mermaid"], H["code"] = [], []
for i, m in enumerate(re.finditer(r"```(\w+)?\n(.*?)```", text, re.S)):
    lang, body = (m.group(1) or "text"), m.group(2)
    sec = re.findall(r"^## (.+)$", text[: m.start()], re.M)
    sec = sec[-1] if sec else ""
    if lang == "mermaid":
        n = len(H["mermaid"]) + 1; p = f"{out}/mermaid/diagram{n}.mmd"; open(p, "w").write(body)
        subprocess.run([sys.executable, here + "/mermaid_to_svg.py", p, p[:-4] + ".svg", f"mm-{os.path.basename(chap)[:-3]}-{n}"], check=True)
        H["mermaid"].append({"mmd": os.path.relpath(p, out), "svg": os.path.relpath(p[:-4] + ".svg", out), "section": sec, "first_line": body.strip().splitlines()[0]})
    else:
        ext = {"python": "py", "http": "http", "json": "json", "bash": "sh", "text": "txt"}.get(lang, lang)
        p = f"{out}/code/block{i + 1}.{ext}"; open(p, "w").write(body)
        H["code"].append({"file": os.path.relpath(p, out), "lang": lang, "section": sec, "lines": len(body.splitlines())})
# concept SVGs
H["svgs"] = []
for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+\.svg)\)", text):
    path = os.path.normpath(os.path.join(os.path.dirname(chap), m.group(2)))
    if os.path.exists(path):
        name = os.path.splitext(os.path.basename(path))[0]; dst = f"{out}/svg/{name}.svg"
        subprocess.run([sys.executable, here + "/repo_svg_to_dark.py", path, dst], check=True)
        H["svgs"].append({"src": os.path.relpath(path, repo), "dark": os.path.relpath(dst, out), "alt": m.group(1)})
# takeaways + quiz
kt = re.search(r"## Key Takeaways\n(.*?)(?:\n### Check Yourself|\Z)", text, re.S)
H["takeaways"] = [l[2:].strip() for l in (kt.group(1).splitlines() if kt else []) if l.startswith("- ")]
H["quiz"] = re.findall(r"<summary>(.+?)</summary>", text)
# related repo content
stem = os.path.basename(chap)[:-3]; related = {}
for d in ("resources", "examples", "diagrams", "projects"):
    hits = subprocess.run(["grep", "-rl", "--include=*.md", stem, os.path.join(repo, d)], capture_output=True, text=True).stdout.split()
    related[d] = sorted(os.path.relpath(h, repo) for h in hits)
H["related"] = related
json.dump(H, open(f"{out}/harvest.json", "w"), indent=1, ensure_ascii=False)
print(f"{H['title']}: {len(H['mermaid'])} mermaid, {len(H['svgs'])} svg, {len(H['code'])} code blocks, {len(H['quiz'])} quiz Qs")
for k, v in related.items(): print(f"  related {k}: {len(v)}", *v[:4])
