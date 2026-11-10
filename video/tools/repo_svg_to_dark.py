#!/usr/bin/env python3
"""Convert a handbook concept SVG (docs/assets/diagrams/*.svg, white card) to a transparent neon-on-black SVG.

usage: repo_svg_to_dark.py in.svg out.svg [prefix]
- removes the white canvas rect, darkens pastel fills (hue kept), brightens strokes, text -> white/grey
- prefixes class names and ids (default: file stem + '-') so several SVGs can be inlined in one page
  without their <style> rules leaking into the scene CSS
"""
import colorsys, os, re, sys
import argparse
ap = argparse.ArgumentParser(description="Convert a handbook concept SVG to a transparent neon-on-black SVG.")
ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("prefix", nargs="?")
a = ap.parse_args()
src, dst = a.src, a.dst
pre = "r" + (a.prefix or re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(src))[0].lower())) + "-"   # CSS class names must not start with a digit
s = open(src).read()

def rgb(h):
    h = h.lstrip("#"); h = "".join(c * 2 for c in h) if len(h) == 3 else h
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def hexs(r, g, b): return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))
def conv(col, role):
    if not re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}", col): return col
    r, g, b = rgb(col); h, l, sat = colorsys.rgb_to_hls(r, g, b)
    if role == "text":
        if l < 0.22: return "#FFFFFF"                                  # near-black headings -> white
        if sat < 0.5 and l < 0.7: return "#A0A0B0"                     # greys -> secondary text
        if sat < 0.25: return "#FFFFFF"
        return hexs(*colorsys.hls_to_rgb(h, 0.64, min(max(sat, .6), .95)))
    if role == "fill":
        if l > 0.88 and sat < 0.25: return "#0B0B0F"
        if l > 0.6: return hexs(*colorsys.hls_to_rgb(h, 0.11, min(sat, .7)))
        return hexs(*colorsys.hls_to_rgb(h, max(l, .62), max(sat, .3)))          # marker / dark shape -> brighter
    if role == "stroke":
        if l > 0.85 and sat < 0.25: return "#2A2A2A"
        return hexs(*colorsys.hls_to_rgb(h, max(l, .58), max(sat, .45)))
    return col

# 1. drop the white canvas card
s = re.sub(r'<rect[^>]*fill="#(?:fff|ffffff)"[^>]*stroke="#e5e7eb"[^>]*/>\s*', "", s, count=1, flags=re.I)
# 2. colours (text elements first: a <text fill="..."> is text, not a shape fill)
s = re.sub(r'(<text\b[^>]*?)fill="(#[0-9a-fA-F]{3,6})"', lambda m: f'{m.group(1)}fill="{conv(m.group(2), "text")}"', s)
s = re.sub(r'(<(?!text\b)[a-zA-Z]+\b[^>]*?)fill="(#[0-9a-fA-F]{3,6})"', lambda m: f'{m.group(1)}fill="{conv(m.group(2), "fill")}"', s)
s = re.sub(r'stroke="(#[0-9a-fA-F]{3,6})"', lambda m: f'stroke="{conv(m.group(1), "stroke")}"', s)
s = re.sub(r'style="([^"]*)"', lambda m: 'style="' + re.sub(r"fill:\s*(#[0-9a-fA-F]{3,6})", lambda k: f"fill:{conv(k.group(1), 'text')}", m.group(1)) + '"', s)
def style_block(m):
    css = re.sub(r"fill:\s*(#[0-9a-fA-F]{3,6})", lambda k: f"fill: {conv(k.group(1), 'text')}", m.group(0))
    return css
s = re.sub(r"<style>.*?</style>", style_block, s, flags=re.S)
# 3. prefix classes and ids
def pref_css(m):
    return re.sub(r"\.([A-Za-z_][\w-]*)", lambda k: "." + pre + k.group(1), m.group(0))
s = re.sub(r"<style>.*?</style>", pref_css, s, flags=re.S)
s = re.sub(r'class="([^"]+)"', lambda m: 'class="' + " ".join(pre + c for c in m.group(1).split()) + '"', s)
s = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{pre}{m.group(1)}"', s)
s = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{pre}{m.group(1)})", s)
s = re.sub(r'aria-labelledby="([^"]+)"', lambda m: 'aria-labelledby="' + " ".join(pre + c for c in m.group(1).split()) + '"', s)
# step badges: the dark circle is brightened above, so its 1-2 digit numeral needs dark ink (white on mint is ~1.7:1)
s = re.sub(r'(<text\b[^>]*?)fill="#FFFFFF"([^>]*>\s*\d{1,2}\s*</text>)', lambda m: m.group(1) + 'fill="#0E0622"' + m.group(2) if 'font-size="12"' in m.group(0) or 'font-size="13"' in m.group(0) else m.group(0), s)
s = re.sub(r'(<text\b[^>]*?style="font:\s*700 1[23]px[^"]*?)fill:\s*#FFFFFF;("[^>]*>\s*\d{1,2}\s*</text>)', r'\1fill:#0E0622;\2', s)
s = re.sub(r"<svg ", '<svg fill="#FFFFFF" ', s, count=1)              # text without an explicit fill defaulted to black
open(dst, "w").write(s)
vb = re.search(r'viewBox="[\-\d\.]+ [\-\d\.]+ ([\d\.]+) ([\d\.]+)"', s)
print(f"{dst}: {vb.group(1) + 'x' + vb.group(2) if vb else 'unknown size'}, prefix={pre}")
