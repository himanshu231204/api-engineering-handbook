# Scene recipes for repo content

All helpers live in `video/what-is-an-api-long/build/build.py` (class `Scene`). Times are local seconds inside the scene; `S.t(line_key, "word")` returns the time a word is spoken (from `timing.json`).

## 1. Mermaid block from the chapter  ->  `svg_reveal`

```bash
python3 video/tools/mermaid_to_svg.py chapter.mmd out.svg mm-chapter-1   # neon theme, transparent, styles baked inline
```
```python
S.svg_reveal("assets/repo/mermaid/<name>.svg", x, y, scale, "y", steps)
# steps = [(S.t("q1","Now"), 92), (S.t("q2","request"), 145), ...]   # svg units revealed from the top
```
- Sequence diagrams: reveal row by row (participants first, then each message on the word that names it, bottom participants last). Find row y by rendering the SVG once and reading the picture; `viewBox` height is the total.
- Flowcharts: reveal left to right (`"x"`), or per node group.
- Explain the point with `S.ring(x, y, w, h, color, t=...)` around the part the client depends on vs the part free to change, plus two `S.chip` labels. Scale 1.4 fits 1166x489 in the safe area.
- Mermaid text is 16-20 px in the SVG; at scale 1.4 it reads at 28 px.

## 2. Concept SVG from `docs/assets/diagrams/`  ->  `svg_reveal`

```bash
python3 video/tools/repo_svg_to_dark.py docs/assets/diagrams/01-status-code-families.svg out.svg
```
Removes the white card, darkens pastel fills (hue kept), brightens strokes, text -> white/grey, prefixes classes/ids (`r<stem>-`). Reveal top-to-bottom with one step per band/box named in the narration (`"y"`), e.g. status families: title 80, 1xx 150, 2xx 222, 4xx 366, 5xx 440. Scale 1.45-1.5. Always add `S.chip("from the handbook", 460, 44, LIME, size=30, ...)` (x >= 460 to stay clear of the chapter title in the HUD).

## 3. Code from the chapter  ->  `code` + `hl`

Paste the chapter snippet **verbatim** (drop only blank/docstring lines if space is short, and say nothing that contradicts it). `S.code(x, y, w, lines, title, size, lh, times)` types one line per time; `S.hl(...)` moves a yellow highlight bar to the line being explained; annotate with chips in a right-hand column (width <= 290). 12 lines at lh 50 fits.

## 4. Real run  ->  terminal `code(bg="#000000")`

Run the example (`examples/<name>` or `video/<slug>/demo/`), save the real `curl -i` output to `demo/real_output.txt`, show those lines (trim headers only if you say "some headers trimmed"). Use the default port shown on screen (8000).

## 5. Glossary quote card

Real text from `resources/glossary.md` in a lime-bordered card labelled `FROM THE HANDBOOK GLOSSARY`, key phrases in yellow (`beat_c1a` in the example).

## 6. Third-party proof screenshot  ->  `img`

Playwright dark-mode capture (`colorScheme: 'dark'`), crop with ffmpeg to the dark/relevant region, `S.img(..., title="domain/path")`, a `S.ring` around the quoted line, chip `"<source> says"`; vendor numbers via `S.stat`. Credit in CREDITS.md.

## Layout constants (1920x1080)

Safe area x 100-1820, y 70-890. HUD chapter title at x 24-300, y 26-54. Pill centre y 850. Captions y 918-1030. Last 20 s keep x >= 1050 empty (end screen).
