# Handbook videos

One 5–10 minute faceless video per handbook chapter, generated from a reviewed
script. Design: `specs/2026-11-10-video-series-design.md`. Build plan:
`plans/2026-11-10-video-pipeline-and-dns-pilot.md`.

## Workflow

1. **Draft** a script skeleton from a chapter:

   ```bash
   python3 video/tools/draft_script.py docs/01-api-foundations/dns.md --part 1 --index 5 \
     > video/scripts/01-api-foundations/dns.md
   ```

2. **Rewrite** it as spoken prose (about 750–1,500 words in total). Each beat has a
   comment with the chapter text to draw from. Add scene cues such as
   `[scene: DiagramWalk svg=01-dns-resolution.svg steps=1-6]`.
3. **Validate**:

   ```bash
   python3 video/tools/check_script.py video/scripts/01-api-foundations/dns.md
   ```

4. **Review**: fact-check every claim against the chapter, then set `reviewed: true`
   in the script's frontmatter. `render.sh` refuses unreviewed scripts.
5. **Render**:

   ```bash
   bash video/tools/render.sh video/scripts/01-api-foundations/dns.md
   ```

   Output: `video/out/<name>.mp4` and `video/out/<name>.srt` (gitignored).

First run in a fresh checkout: `cd video/kit && npm ci`.

## Narration

With no provider configured the render is captioned and silent, and the narration
text is the script itself, so you can record your own voiceover. To generate
speech, set these environment variables (never commit them):

| Variable | Meaning |
|---|---|
| `VIDEO_TTS_PROVIDER` | `openai-compatible` (or unset/`none` for silent) |
| `VIDEO_TTS_BASE_URL` | API base URL, for example `https://api.example.com/v1` |
| `VIDEO_TTS_API_KEY` | API key |
| `VIDEO_TTS_MODEL` | speech model name |
| `VIDEO_TTS_VOICE` | voice name (keep it the same across the series) |

## Checks

```bash
python3 -m unittest discover -s video/tools/tests   # Python tools
cd video/kit && npm run typecheck && npm run check-registry
```

## Layout

- `scripts/<NN-slug>/<chapter>.md`: one reviewed script per video
- `templates/script.md`: blank script with all eight beats
- `tools/`: validator, drafting, captions, narration, timeline, `render.sh`
- `kit/`: the Remotion project; scene names live in `kit/scene_names.json`,
  diagram step boxes in `kit/diagram_steps/<svg-name>.json`
