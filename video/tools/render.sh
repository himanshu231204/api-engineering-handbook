#!/usr/bin/env bash
# Render one reviewed video script to video/out/<slug>.mp4 (+ .srt).
# Usage: bash video/tools/render.sh video/scripts/<NN-slug>/<chapter>.md
set -euo pipefail

SCRIPT="${1:?usage: render.sh <script.md>}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VIDEO="$ROOT/video"
KIT="$VIDEO/kit"
SLUG="$(basename "$SCRIPT" .md)"
WORK="$VIDEO/.cache/$SLUG"
TMP_MP4="$WORK/$SLUG.tmp.mp4"

[ -f "$SCRIPT" ] || { echo "render.sh: script not found: $SCRIPT" >&2; exit 1; }

if ! grep -qiE '^reviewed:[[:space:]]*true[[:space:]]*$' "$SCRIPT"; then
  echo "render.sh: refusing to render, $SCRIPT is not reviewed (fact-check it, then set 'reviewed: true')." >&2
  exit 1
fi

python3 "$VIDEO/tools/check_script.py" "$SCRIPT" || { echo "render.sh: script failed validation" >&2; exit 1; }

# A failed render must never leave a partial mp4 in video/out.
trap 'rm -f "$TMP_MP4"' EXIT

rm -rf "$WORK"
mkdir -p "$WORK" "$VIDEO/out" "$KIT/public/diagrams"

# Diagram assets referenced by DiagramWalk cues (SVG + its step sidecar).
for svg in $(grep -oE 'svg=[^] ]+' "$SCRIPT" | cut -d= -f2 | sort -u); do
  cp "$ROOT/docs/assets/diagrams/$svg" "$KIT/public/diagrams/$svg"
  cp "$KIT/diagram_steps/${svg%.svg}.json" "$KIT/public/diagrams/${svg%.svg}.json"
done

python3 "$VIDEO/tools/build_timeline_cli.py" "$SCRIPT" --out-dir "$WORK"

rm -rf "$KIT/public/audio"
if [ -d "$WORK/audio" ] && ls "$WORK/audio"/*.mp3 >/dev/null 2>&1; then
  mkdir -p "$KIT/public/audio"
  cp "$WORK/audio"/*.mp3 "$KIT/public/audio/"
fi

BROWSER_FLAG=()
BROWSER="${REMOTION_BROWSER:-/opt/pw-browsers/chromium}"
[ -x "$BROWSER" ] && BROWSER_FLAG=(--browser-executable="$BROWSER")

(
  cd "$KIT"
  npx remotion render src/index.ts Episode "$TMP_MP4" \
    --props="$WORK/timeline.json" --codec=h264 --log=warn "${BROWSER_FLAG[@]}"
)

mv "$TMP_MP4" "$VIDEO/out/$SLUG.mp4"
cp "$WORK/captions.srt" "$VIDEO/out/$SLUG.srt"
echo "rendered $VIDEO/out/$SLUG.mp4"
