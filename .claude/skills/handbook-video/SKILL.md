---
name: handbook-video
description: Make (or re-cut) the YouTube explainer video for a chapter of the API Engineering Handbook using the repo's own content, not stand-ins - the chapter's Mermaid diagrams, the concept SVGs in docs/assets/diagrams, its code, the glossary, cheatsheets and a real run of the example - on top of the concept-explainer pipeline (Kokoro voice, HyperFrames render). Use when asked for a video for a handbook topic or a video/ROADMAP.md row, or to add the repo's real images, diagrams or Mermaid to a video.
---

# Handbook video (repo-specific)

One topic of this handbook becomes one 5-10 minute video. This skill is the **concept-explainer-shorts pipeline specialised for this repo**: same voice, design system, scene kit and QA, but the **source of truth is the repo**, and every diagram or code block the chapter already has must appear on screen as the real thing.

- Pipeline mechanics, design spec, QA: `references/base-concept-explainer.md` (a copy of `anthropic-skills:concept-explainer-shorts`; if that skill is installed, load it too). Also load `hyperframes` and `hyperframes-cli` before writing scenes.
- Scene recipes for repo content (Mermaid, concept SVGs, code, real runs): `references/scene-recipes.md`.
- Traps already hit once, with fixes: `references/pitfalls.md`.
- A complete worked example you can copy: `video/what-is-an-api-long/` (Part 0, "What Is an API?").

## What differs from the base skill

| Base skill | Handbook video |
|---|---|
| Research the web first, then script | **Harvest the chapter first** (`harvest_chapter.py`). Web only to fact-check, to cite third parties (MDN, vendor reports) and to screenshot them |
| Draw diagrams as SVG yourself | **Never redraw what the repo has.** Use the chapter's Mermaid block and the concept SVGs from `docs/assets/diagrams/`, converted to the dark neon look by `video/tools/` |
| Code card "tested in research" | Show the chapter's code **exactly as written**, and **run the example** (`examples/*` or the chapter snippet) so terminal output is real |
| Default format asked each time | **Long (7-10 min, 16:9)** unless the user says Short. Chapter = 4-6 beats groups; one beat per diagram |
| Output anywhere | `video/<slug>-long/` (project), MP4 **not committed**, ROADMAP row updated |

## Source order (stop when the video has enough real material)

1. **The chapter** `docs/<NN-slug>/<chapter>.md`: TL;DR callout (hook + promise), Core Concept/Mental Model (analogy), How It Works, Architecture (Mermaid), Request/Response Example, Code Example, Common Mistakes (mistakes chapter), AI Engineering Perspective, Exercises (outro), Key Takeaways (recap), Check Yourself (end quiz or pinned comment).
2. **Concept SVGs** `docs/assets/diagrams/<NN>-*.svg` for that part (`ls docs/assets/diagrams | grep '^<NN>-'`) plus any the chapter embeds.
3. **Standalone Mermaid** in `diagrams/*.md` when the chapter links to one (`api-request-flow`, `webhook-flow`, `authentication-flow`, `rag-architecture`, `agent-architecture`, `production-ai-architecture`).
4. **Examples** `examples/<name>/` - run it, record the real output. **Resources**: `resources/glossary.md` (definition quote card), `resources/cheatsheets/*` (status codes, methods...), `resources/interview-questions/*`, `resources/exercises/*`.
5. **Web** only for facts and third-party proof screenshots (dark mode, cropped to dark regions, credited).

## Procedure

1. **Pick the row** in `video/ROADMAP.md`; the slug is `<chapter-file-stem>-long`. Set `PROJ=video/<slug>-long`.
2. **Harvest**:
   ```bash
   python3 video/tools/harvest_chapter.py docs/<NN-slug>/<chapter>.md $PROJ/harvest
   ```
   Writes `harvest.json` (title, TL;DR, sections, takeaways, quiz, related files) plus `mermaid/*.svg` (neon, transparent, styles baked inline), `svg/*.svg` (dark versions of every embedded concept SVG) and `code/*`. Convert extra repo SVGs one by one with `video/tools/repo_svg_to_dark.py in.svg out.svg`. Copy what you will use into `$PROJ/hf/assets/repo/{svg,mermaid}/`.
3. **Asset map** (write it down before scripting): every Mermaid block, every concept SVG and every code block gets **its own beat** with 1-3 narration lines that name what is being revealed. If the repo has it, it is on screen.
4. **Script** with the base skill's rules (hook scored 55+ with the yt-script `hookscore.py`, one build per sentence, pills, no music). Respell for TTS (`A P I`, `M D N`, `Post gress Q L`, `four zero four`). `build/script_lines.py` in the worked example is the format.
5. **Build project**: copy `video/what-is-an-api-long/build/` and `hf/` skeleton (`cp -r`), keep `script_lines.py`, `make_voice.py`, `align.py`, `mix.py`, `build.py`, `post.py`; rewrite `script_lines.py` and the `beat_*` functions. Reuse `Scene.svg_reveal`, `code`, `hl`, `box`, `arrow`, `chip`, `note`, `stat`, `img`, `ring`.
6. **Voice, align, mix** (order matters): `make_voice.py` -> `ffmpeg -i voice.wav -ar 16000 -ac 1 voice16.wav` -> `align.py` -> `build.py` -> `mix.py` -> `post.py` (SRT, script.json, script.md, chapters).
7. **Check and look**: `cd hf && npx hyperframes check --json` must show 0 errors in lint/runtime/layout/contrast/audio; `npx hyperframes snapshot --at <end of every beat>` and Read the contact sheets. Fix, repeat.
8. **Render** `HYPERFRAMES_RENDER_DETACHED=1 npx hyperframes render --quality delivery --output ../renders/raw.mp4` as a *foreground command with `run_in_background`* (not `nohup ... &`: that gets cancelled). About 1.5x runtime on 4 cores. Then `loudnorm=I=-14:TP=-1.5:LRA=7`.
9. **QA** (base skill section 7) plus the repo checks below. **Deliver** with SendUserFile: MP4, thumbnail, SRT, seo.md, research.md (or harvest summary), script.md, CREDITS.md. End with: **ship it, or change it?**

## Repo rules to respect

- Update `video/ROADMAP.md`: row status -> `🎬 Rendered`, part table counts. Published only after the user adds the YouTube link.
- **Do not commit** MP4/WAV (`$PROJ/.gitignore` has them) or venvs (`tts/`, `fa/`, `models/`). Commit scripts, scenes, assets, SRT, script, SEO, thumbnail, CREDITS.
- `python3 scripts/check_links.py` must pass for tracked files (local venv folders can show false hits; they are untracked). Markdown inside `video/` must not link to files that do not exist.
- Credit every asset in `hf/assets/CREDITS.md`: repo content is MIT (this repo); third-party screenshots are cited, nominative use; no photos of people; no music.
- Commit on the session's feature branch, push, keep one draft PR (see CLAUDE.md house rules: focused commits).
- Facts on screen must match the chapter or a cited source; vendor statistics are labelled "<vendor> survey".

## Final answer format

Bullets: format and length, which repo diagrams/Mermaid/code were shown (file paths), which real runs, what was cited from the web, QA results, title + description (chapters) + tags in code blocks, `Sources:` list, then **ship it, or change it?**
