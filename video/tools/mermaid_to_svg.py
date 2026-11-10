#!/usr/bin/env python3
"""Render a Mermaid block to a transparent, neon-on-black SVG for the handbook videos.

usage: mermaid_to_svg.py in.mmd out.svg [unique_id]   (run with -h for details)
Needs Node (npx downloads @mermaid-js/mermaid-cli) and a Chromium: uses the pre-installed
Playwright one (/opt/pw-browsers/chromium-*/chrome-linux*/chrome) or $CHROME_PATH.
The output has explicit width/height from its viewBox and a unique root id (default: file stem),
so several diagrams can be inlined in one HyperFrames page without CSS collisions.
"""
import argparse, glob, json, os, re, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
MERMAID_CLI = "@mermaid-js/mermaid-cli@12.2.0"   # pinned: the post-processing below depends on its SVG output
ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("uid", nargs="?")
a = ap.parse_args()
src, dst = a.src, a.dst
uid = a.uid or "mm-" + re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(dst))[0].lower())
chrome = os.environ.get("CHROME_PATH") or next(iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))), None)
pp = {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
if chrome:
    pp["executablePath"] = chrome
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(pp, f)
    ppath = f.name
try:
    subprocess.run(["npx", "-y", MERMAID_CLI, "-i", src, "-o", dst, "-p", ppath, "-c", here + "/mermaid-neon-theme.json", "-b", "transparent"], check=True)
finally:
    os.unlink(ppath)
svg = open(dst).read()
svg = svg.replace("my-svg", uid)
vb = re.search(r'viewBox="([\-\d\.]+) ([\-\d\.]+) ([\d\.]+) ([\d\.]+)"', svg)
if not vb:
    sys.exit(f"{dst}: Mermaid output has no usable viewBox")
w, h = float(vb.group(3)), float(vb.group(4))
svg = re.sub(r'width="100%"', f'width="{w:g}" height="{h:g}"', svg, count=1)
svg = re.sub(r'style="max-width:[^;"]*;?\s*background-color:\s*transparent;?"', "", svg, count=1)
# mermaid writes "&gt;" inside <style>; HTML does not decode entities there, so inlined CSS fails to parse
svg = re.sub(r"<style>.*?</style>", lambda m: m.group(0).replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&"), svg, flags=re.S)
open(dst, "w").write(svg)
# bake computed styles inline (Mermaid's id-scoped <style> does not survive being mounted in a HyperFrames scene)
subprocess.run(["node", here + "/bake_svg_styles.js", dst, dst], check=True)
svg = open(dst).read()
print(f"{dst}: {w:g}x{h:g}, id={uid}")
