---
name: "concept-explainer-shorts"
description: "Turn a concept, launch or notes into an animated explainer on black: a 40-50s vertical Short or a 7-10 min 16:9 long video, with research, real assets, voiceover, captions and SEO."
---

# Concept Explainer Videos (Short or Long)

Turns a technical concept (a topic name, a launch/news item, an infographic, cheat sheet or notes) into a finished animated explainer in one of two formats:

- **Short**: 9:16 YouTube Short / Reel, 40-50 s, fast cuts, word-pop captions, designed loop.
- **Long**: 16:9 YouTube video, 7-10 min, chapters, chapter cards, recap, end screen, thumbnail.

Both use motion graphics on a pure black background, real-world assets (the actual logo, repo, website, UI and demo clips of the thing being explained), SVG graphics for everything that has no real source, an AI voiceover and SFX. **There is no music in either format**: the audio is voice + sound effects only. When given only a topic, it researches the topic on the web first, gathers real assets, then writes the script from what it found. The video is built and rendered locally with **HyperFrames** (default) or **Remotion**, so it costs no credits. When the video is done, it writes the upload package (title, description, tags; plus chapters and a thumbnail for Long).

Example: a video on **Ollama** shows Ollama's real llama logo, its GitHub repo page with the real star count, the ollama.com page, and a real terminal running `ollama run`, not a drawn stand-in. The "how it works" beat (model weights -> local runtime -> API) is an animated SVG diagram.

**Core editing idea: the screen builds as the voice speaks.** Each spoken sentence adds to the canvas, and each element lands on the word that names it. Cuts land in the pauses between sentences. A handwritten note adds commentary, and a summary pill states the beat's takeaway. Nothing appears before it is said. Nothing sits still once it is on screen. This comes from a reference video that worked (section 4c) and applies to every scene in both formats.

Deliverables:
- Short: `<topic>_short.mp4` (1080x1920, 30 fps, H.264 + AAC), `captions.srt`, `research.md`, `seo.md`, `assets/CREDITS.md`.
- Long: `<topic>_long.mp4` (1920x1080, 30 fps, H.264 + AAC), `captions.srt`, `thumbnail.png` (1280x720), `research.md`, `script.md` (readable script with chapter timestamps), `seo.md`, `assets/CREDITS.md`.
All sent with SendUserFile, plus the title / description / tags pasted in the final reply ready to copy. End every run with: **ship it, or change it?**

## Format (decide first; Short is NOT the default)
| | Short | Long |
|---|---|---|
| Canvas | 1080x1920 (9:16) | 1920x1080 (16:9) |
| Length | 40-50 s | 7-10 min |
| Spoken words | 105-125 | 1,100-1,550 |
| Voice speed (Kokoro) | 1.12 | 1.0-1.05 |
| Structure | hook, fix #1, fix #2, recap, loop | cold open, roadmap, 4-6 chapters, mistakes, recap, outro + end screen |
| Captions | big word-pop, centre | subtitle line, lower third |
| Extras | loop point | chapters, thumbnail, end screen |

How to pick:
- The user says short, Short, Reel, TikTok, vertical, 30-60 s → **Short**.
- The user says long, long-form, full video, tutorial, deep dive, 16:9, a duration of several minutes (e.g. 7-10 min) → **Long**.
- Anything else: ask one question with AskUserQuestion ("Short (40-50 s, vertical)" vs "Long (7-10 min, 16:9)") before research starts. If nobody is there to answer, pick Long for broad topics (a tool, a framework, "X explained", a comparison with several parts) and Short for a single narrow idea or a news blip, and state the choice at the top of the first progress message.
- A user-given duration inside the long range (e.g. "8 minutes") sets the word budget: ~155 words per spoken minute.

Everything below applies to both formats unless marked **Short:** or **Long:**.

## Input modes (do not ask)
- **News / launch** (e.g. a new model, a release post or benchmark table): treat it as a topic, but research the announcement itself (official post, model card, independent benchmarks, pricing, availability) and use the news structure in section 1.
- **Topic only** (e.g. "Ollama", "Python decorators", "RAG", "JWT vs sessions"): run the full pipeline end to end.
  - Short: do not stop for approval; post the research summary and top 2 hooks with `SendUserMessage` as progress and keep going.
  - Long: post the research summary, the top 2 hooks and the chapter outline (titles + one line each + target minutes) with `SendUserMessage`, and wait for a go-ahead before voice and build, because a long render is expensive to redo. Skip the wait if the user said to just make it or is not there to answer.
- **Source given** (infographic, cheat sheet, notes, link): use it as the primary source, and still run a light research pass (section 0, steps 1-3) to fact-check it and find the hook angle, plus the asset pass (section 0b). Show the top 2 hooks and the line list (Short) or chapter outline (Long) before building, unless the user said to just make it.

## Renderer choice (do not ask)
- **HyperFrames (default).** Load the `hyperframes` skill, then `hyperframes-cli`, before writing any scene. Follow its Contract and work loop. For footage and images, also follow its media guidance (`media-use`, `npx hyperframes media-treatment`).
- **Remotion** only when the user names it or already has a Remotion project. Load `remotion-best-practices` first (it routes to `remotion-create`, `remotion-markup`, `remotion-captions`, `remotion-multimedia`, `remotion-render`).
- Both need Node.js 22+ and FFmpeg: check `node -v` and `ffmpeg -version` at the start; install Node 22 if older.
- Never use cloud rendering (`hyperframes cloud`, Remotion Lambda) or ManyMotions / paid AI-video generation unless the user asks: ManyMotions returns `billing_required` and one 8-10 s clip costs ~1,800-2,300 credits.

## Defaults (do not ask)
- No face / no host. Hook and outro use the topic's real logo (section 0b) as the emblem; fall back to an animated SVG `</>` circle only when the topic has no logo (e.g. a general concept like "recursion"). Only add a talking-head host if the user explicitly asks and supplies their own photo (see "Host option").
- Generic AI narrator voice (Kokoro `am_michael`, speed per the format table). Never call it the user's voice or a clone.
- **No music.** Never generate, synthesize, download or add a music bed or background track. Audio = voiceover + SFX. Add music only if the user later asks for it explicitly.
- **Background is pure black (#000000), always, in every scene, from frame 0 to the last frame.** No gradients, no colored blobs, no tinted washes, no brand-colored backgrounds behind content. Depth comes from the content itself: glowing accents, real screenshots, SVG graphics, light sweeps and particles in accent colors over black (limits in section 4).
- **SVG for drawn visuals.** Anything without a real source (diagrams, data flow, architecture, analogies, icons, arrows, charts, the `</>` emblem) is built as vector SVG, not raster images (section 4b). Logos come as SVG when one exists.
- Accent palette "electric pop" on black: YEL #FFE500, PINK #FF2E88, CYAN #00F0FF, LIME #39FF88, ORG #FF9100, VIO #9D4EFF, RED #FF3B3B; dark ink #0E0622 for text on chips; body text #FFFFFF, secondary #A0A0B0. When a real brand is on screen, take one accent from its own logo/brand color for that scene (as an accent on elements, never as the background). Define all colors once as CSS variables (HyperFrames) or a `theme.ts` (Remotion), including `--bg: #000000`.
- This skill's flow overrides the renderer skills' "stop at the Studio preview and wait" step: the user reviews the finished MP4, and "ship it, or change it?" is the approval. Still mention they can keep editing the project in the HyperFrames desktop app / Remotion Studio.

## Task list
Create these with TaskCreate up front: 0) pick format, 0a) research, 0b) real-world assets, 1) script (Long: + outline approval), 2) voice + SFX mix, 3) build scenes + snapshots, 4) full render, 5) QA, 6) SEO package (Long: + thumbnail) + deliver.

## 0. Research (web, before any script)
Goal: a verified brief that the script is written from. Every claim in the video must trace back to it.
1. **Search** with WebSearch, sent in the same turn, each a different angle (Short: 4-8 queries; Long: 8-14 queries):
   - official docs / spec for the concept (for a library or framework, also use Context7 `resolve-library-id` + `query-docs` for current docs);
   - "how X works" / "X explained" for the mechanism;
   - "X common mistakes", "X vs Y", "X misconception" for the hook (the mistake viewers make is the best hook fuel);
   - "X changes <current year>" / release notes, so nothing in the video is outdated;
   - a real-world use or a striking number (performance gain, adoption, cost);
   - Long also: "X tutorial", "X best practices", "X production", "X alternatives", "X limitations", and the questions people ask ("People also ask", forum threads) so each chapter answers a real question.
   Use `extended` mode only when standard results are thin or the topic is very new.
2. **Read** the best sources in full with WebFetch (Short: 3-5; Long: 6-10), preferring official docs, the project's own blog/RFC/paper and well-known engineering blogs over SEO listicles and forums.
3. **Verify**: cross-check any number, version or claim against a second source, drop what you can't confirm, and run any code example you plan to show (Python/Node in the workspace) so the snippet on screen actually works. Paraphrase sources; never copy their sentences into the script.
4. **Write `research.md`** (Short: under ~400 words; Long: under ~1,300 words):
   - one-sentence definition in plain words;
   - how it works, in 3-5 steps (these usually become an SVG diagram);
   - Short: the 2-3 ideas worth teaching in 45 s (one per beat). Long: 4-6 chapter ideas, each with its key point, a concrete example or tiny code snippet (tested), and a demo the video can actually run or show;
   - the common mistakes / misconceptions (hook angle) and what they cost the viewer (Long: 3-5 of them, enough for a mistakes chapter);
   - one or more surprising facts or numbers, with sources;
   - an analogy a beginner gets instantly;
   - the real things the video can show (official site, GitHub repo, product UI, CLI, demo video, companies using it); section 0b collects them;
   - the search phrases people actually use for this topic (wording seen in results, "People also ask" and titles of top videos); section 8 uses these;
   - `Sources:` list as `[Title](URL)`.
5. Post a 3-4 bullet summary of the angle with `SendUserMessage`, then continue (Long: together with the outline, see Input modes).

## 0b. Real-world assets (show the real thing)
Goal: every named product, tool, repo, company or website in the video appears as its real self. Draw only what has no real source (abstract ideas, data flow, analogies), and draw it as SVG (section 4b). Long videos need more of everything: plan at least one real screenshot, clip or terminal recording per chapter, and record full working demos for tutorial chapters.

**What to collect** (into `assets/`, one subfolder per kind):
- `logo/`: the official logo. **SVG first** (official press kit, the repo, `simple-icons`, `@iconify-json/logos`); else PNG >= 512 px with transparency. Logos must have a transparent background, never a white or colored box; if only a boxed version exists, note it and crop/mask it.
- `shots/`: screenshots of the real thing: GitHub repo page (README top, star/fork count), official website hero, docs page, product UI, model card, pricing table, a relevant issue/PR or benchmark chart from the official source. **Capture in dark mode** wherever the site supports it, so screenshots sit naturally on black. Long: capture at 1920 px wide or more.
- `clips/`: real motion: an official demo video or README GIF, or a screen/terminal recording made in the workspace by actually running the tool. Prefer dark-themed demos; terminals always use a black or near-black theme.
- `svg/`: SVG icons and diagram parts from open-licensed icon sets (e.g. `lucide-static`, `@tabler/icons`, `simple-icons` via npm) and any SVG you author for this video.
- `data/`: live numbers shown on screen (GitHub stars, downloads, release version) fetched from the official API on the day of the build, with the fetch date.

**Where to get them, in this order** (the workspace shell can reach GitHub and package registries; most other sites are blocked from the shell):
1. **GitHub**: org/user avatar `https://github.com/<org>.png?size=512`, SVG/PNG logos and images referenced in the repo README (`raw.githubusercontent.com/...` or `git clone --depth 1` and look for `*.svg` in `docs/`, `assets/`, `.github/`), release assets, and repo stats via `gh api repos/<owner>/<repo>`.
2. **Package registries**: brand SVGs from the `simple-icons` npm package (`node_modules/simple-icons/icons/<slug>.svg`; single-color paths, fill them with the brand hex from `simple-icons` metadata), full-color SVG logos from `@iconify-json/logos`, UI icons from `lucide-static` / `@tabler/icons`; package READMEs and their images.
3. **Websites and UI screenshots**: `npx hyperframes capture <url> --json` (headless Chrome screenshots of the real page), forcing dark color scheme where the page supports it. If the shell can't reach the site, use the browser: load the `built-in-browser` skill (or `chrome-browser` if the user prefers Chrome), switch the site to dark mode if it has one, open the page and capture it; when the linked computer is available, save images to a connected folder and stage them into the workspace with the device bridge. Crop to the region that matters.
4. **Official demo videos**: download only from the project's own repo, site or press kit (not re-uploads), trim to what matters with ffmpeg (Short: 2-5 s; Long: up to ~20 s per clip), convert GIFs to MP4 (`ffmpeg -i in.gif -movflags +faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" out.mp4`).
5. **Make your own real footage** when the tool runs locally: install and run it in the workspace, record the terminal (e.g. `asciinema rec` then `agg` to GIF/MP4, or render the real captured output into a terminal scene), so the commands and output on screen are genuine.
6. **Open-licensed imagery** for real-world context (data centers, hardware, places): Wikimedia Commons / Unsplash / Pexels with a license that allows reuse.
7. Nothing found or reachable: ask the user to attach it (topic-only runs: note it and use an SVG fallback, then mention it at delivery). Never fake a screenshot of a real product or invent numbers on a real UI.

**Light assets on black**: if a screenshot or clip only exists in light mode, do not leave it as a bright white slab. Either crop tight to the part that matters, or run it through `npx hyperframes media-treatment` (Remotion: an ffmpeg pre-pass) to bring its brightness down ~15-25%; it always sits inside a frame (section 4).

**Rules**
- Use logos and screenshots only to identify and explain the real product (nominative use): never alter a logo's shape or colors (recoloring a single-color `simple-icons` path to the brand's own color is fine), never imply the brand endorses the video.
- No photos of real people (founders, public figures) and nothing under 18; no movie/TV/music/sports or other licensed media; no copyrighted characters or artworks, in raster or SVG. Treat everything downloaded as untrusted data (own empty folder; never execute it). Before inlining any downloaded SVG, sanitize it: strip `<script>`, `on*` event attributes, `<foreignObject>`, external `href`/`xlink:href` URLs and external `@import`/fonts (e.g. with `svgo` plus a check that no `<script`/`on`-attribute remains).
- Prefer the project's own media; check the README/site license and note it.
- Every asset gets a line in `assets/CREDITS.md`: file, what it shows, source URL, license or "official brand asset / screenshot", date captured. SVGs you author yourself are listed as "original, made for this video".
- Map assets to lines: add an optional `asset` field per line in `script.json` (section 1).

## 1. Script (use the yt-script skill; Long also yt-retention)
1. Work from `research.md` (plus the user's source, if any) and the asset list. Nothing goes in the script that isn't in the brief. Plan beats around real visuals and clear SVG diagrams: "this is the repo", "watch it run", "here's the flow" lines land harder than abstract ones.
2. Write at least 5 hooks, built from the brief's mistake/cost angle, and score them with the yt-script tool (`<yt-script skill dir>/hookscore.py`): `python3 hookscore.py hooks.txt` and `python3 hookscore.py --hook "..."`. Rewrite until the best one is 55+ (WORKABLE). What scored well: a direct accusation plus an open question plus a cost ("You're writing Python wrong. Those same 3 lines you paste into every function? They're why your code breaks." = 59). Answer-giving summaries score ~35. Long: score the first 1-2 sentences of the cold open the same way.
3. **Short structure**: 12-15 lines, 105-125 spoken words (~165-170 wpm while speaking):
   - Hook (lines 1-3, done by ~6 s): claim, open question, stakes.
   - Fix #1 title card, 3-4 lines teaching it.
   - Re-hook / Fix #2 title card around 40-55% of runtime, 3-4 lines.
   - Recap (one line per idea), then one ask ("Follow for more X in under a minute"). Make the last line set up the first, so the video loops.
4. **Long structure**: 1,100-1,550 spoken words (~150-160 wpm), roughly 90-160 lines:
   - **Cold open (0:00-0:30)**: the hook (mistake + cost or a striking result), a 3-6 s glimpse of the payoff (the finished demo, the benchmark, the diagram fully built), and a concrete promise ("by the end you'll be able to…"). No greeting, no channel intro before the hook.
   - **Roadmap (0:30-0:50)**: the chapter list builds on screen as it's spoken.
   - **4-6 chapters, 60-120 s each**, in the order the brief's chapter ideas build on each other. Each chapter: a chapter title card, a one-line re-hook question, the explanation built as spoken (SVG flow / diagram), a real example or demo (terminal, code card, screenshot), and a one-line takeaway pill.
   - **Mistakes chapter** (60-90 s): 3-5 common mistakes from the brief, each with its fix; usually the most-watched part, so keep it punchy.
   - **Recap (30-45 s)**: one line per chapter, recap cards building one by one.
   - **Outro (15-20 s)**: one ask (subscribe / comment a question / watch the next video) and what to watch next. The last 20 s keep the right ~45% of the frame free for YouTube end-screen elements.
   - **Retention rules**: something new on screen every 4-8 s; a pattern interrupt (new scene type, zoom punch, real clip, big number) every 20-40 s; an open loop at least once per chapter ("we'll fix this in chapter 4") and pay every one off; no chapter longer than ~2 min; plain spoken language, short sentences.
   - **News / launch long variant**: what launched and when -> the headline benchmarks (independent) -> 2-3 chapters on what's new and the most interesting angle -> trust/quality claims, attributed -> trade-offs vs the leader (rank vs cost) -> availability, price, who gets it -> who should switch -> recap.
5. **News / launch Short variant** (6-7 beats, same word budget as Short): what launched and when, with a timeline against the previous release -> the headline benchmark from an independent source, with the margin -> "the most interesting thing" -> a trust or quality claim, attributed ("Google says…") -> the trade-off vs the leader -> the catch (availability, price) -> a fun-fact closer that ties back to the opening visual. In both formats attribute every vendor claim on screen with a small "<vendor> says" chip, and mark third-party numbers "independent".
6. **One build per sentence.** Write each line so it names at most 2-3 concrete things that can appear on screen (a number, a logo, a box, an arrow). If a sentence names nothing visual, rewrite it or merge it into the next one.
7. Save `script.json`: one object per line = one caption cue:
   ```json
   [{"say": "Ollama runs models like Llama on your own laptop.", "cap": "Run [LLMs] on your laptop.", "scene": "logo_reveal", "asset": ["logo/ollama.svg"]},
    {"say": "One command. That's it.", "cap": "[One] command.", "scene": "terminal_clip", "asset": ["clips/ollama_run.mp4"]},
    {"say": "Your prompt hits a local server, never the cloud.", "cap": "Stays [local].", "scene": "svg_flow", "asset": ["svg/flow_local.svg"]}]
   ```
   - `say` is the text for TTS. Spell symbols out: "at symbol", "functools dot wraps", "dunder enter", "number one".
   - `cap` is the on-screen text. `[brackets]` mark keywords to highlight. Short: may be shorter than `say`. Long: close to `say` (it doubles as the subtitle), trimmed of filler only.
   - `scene` names a scene from the scene kit (section 4).
   - `asset` (optional) lists the files from section 0b this scene shows. Aim for a real asset in at least 40% of lines (Short) or of beats (Long) when the topic is a real product.
   - `build` lists the on-screen elements in order, each keyed to the spoken word that triggers it: `[{"on": "two weeks", "el": "bracket_2wk"}, {"on": "Carbon", "el": "dot_carbon"}]`. Section 4c turns these into tweens.
   - `pill` is the beat's takeaway in 2-5 words. It is a fact, not a slogan; someone watching muted gets the whole video from the pills alone. Every beat except the hook has one.
   - `note` (optional) is a handwritten aside, 1-4 words, shown in the marker font next to the element it comments on.
   - `carry` (optional) names an element from the previous scene that stays on screen and moves into this one instead of cutting away.
   - **Long only**: `chapter` (number + title, e.g. `"3 · Tool calling"`) on every line, and `beat` (an id). Lines that share a `beat` share one canvas that keeps building across 2-4 sentences (8-25 s) instead of cutting every sentence; the next `beat` id is a cut. Give `scene`, `pill` and `asset` on the first line of each beat.
   ```json
   {"say": "According to Artificial Analysis, Carbon is now number one, just one point ahead of Opus.",
    "cap": "[Number one], by [one point].", "scene": "svg_leaderboard", "pill": "#1 · AA Index",
    "note": "+1 point", "carry": "hero_thumb", "asset": ["data/aa_index.json"],
    "build": [{"on": "Artificial", "el": "title"}, {"on": "number one", "el": "bar_winner"}, {"on": "one point", "el": "bracket_margin"}]}
   ```
8. Accuracy pass: reread every line against `research.md`; simplify, but never trade correctness for punch (this includes SVG diagrams: every box and arrow must match how the thing really works).
9. Long: also write `script.md`, the readable script grouped by chapter (chapter timestamps are filled in after the voice step).

## 2. Voice (Kokoro, local, free)
```bash
python3 -m venv tts && ./tts/bin/pip -q install kokoro-onnx soundfile numpy faster-whisper
mkdir -p models && cd models
curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```
`make_voice.py`: generate EACH line separately so every caption and scene gets exact timing.
```python
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
speed = 1.12 if fmt == "short" else 1.03
t = 0.25; out = [zeros(0.25 s)]; timing = []
for i, ln in enumerate(lines):
    s, sr = k.create(ln["say"], voice="am_michael", speed=speed, lang="en-us")  # sr = 24000
    s = trim_silence(s, thr=0.01)      # keep 20 ms head, 50 ms tail
    timing.append({**ln, "start": t, "end": t + len(s)/sr})
    gap = pause_after(ln)               # see table below
    out += [s, zeros(gap)]; t += len(s)/sr + gap
out.append(zeros(0.6 s)); normalize to 0.95 peak
# write voice.wav and timing.json = {"format": fmt, "total": seconds, "lines": timing, "chapters": [...]}
```
Pauses: Short 0.16 s between lines, 0.26 s at a section end. Long 0.22 s between lines inside a beat, 0.35 s between beats, 0.9 s at a chapter boundary (room for the clear-to-black and chapter card). The gaps are where the cuts go: scenes change inside these pauses, never mid-sentence. Don't squeeze them out.

Long: generation of 100+ lines takes a while; run it in the background with `run_in_background` and cache each line's WAV by a hash of its `say` + speed, so editing one line only regenerates that line. Write the chapter start times into `timing.json` `chapters` and into `script.md`.

Also get real per-word times from the spoken audio: run faster-whisper with `word_timestamps=True` on each line's clip and map each `build[].on` phrase to the start time of its first word (store as `build[].t`). If a phrase can't be matched, fall back to its character-proportional position in `say`.

Also compute per-word caption times: split `cap` into words and give each a share of the line duration proportional to its characters; store `words: [{"w", "start", "end", "kw": bool}]` on each line in timing.json. Write `captions.srt` from the same data (Long: at most 2 lines and ~42 characters per line per cue; split long lines into several cues).

Verify the voice. Run faster-whisper `base.en` on the audio and compare the transcript to the script. Decode with soundfile and pass the numpy array (passing a path breaks on newer PyAV). Short words like "at" may transcribe oddly; that's fine if the caption shows the symbol. Fix real mispronunciations by respelling `say` (e.g. "Oh-lama" if "Ollama" comes out wrong).

## 3. Audio mix: voice + SFX only (numpy, before building the video)
Pre-mix everything into one `mix.wav` so the renderer plays a single track. **No music bed, no background track, no synthesized beat or loop of any kind.**
- The voice is the lead at full level; every SFX sits well under it (peak about -18 to -22 dB relative to the voice peak) and never overlaps a stressed word at a loud level.
- SFX keyed to scene events from timing.json:
  - Short: a whoosh 0.3 s before every line, a thunk on title slams, logo reveals and the `@` slam, a shutter click on screenshot drops, soft keyboard ticks under typed terminal lines, ascending pings per icon or checkmark, a soft tick per SVG node/arrow as it draws, a saw+noise zap on errors, a low thunk + high tick + ping for the lock.
  - Long: lighter, so 10 minutes doesn't get tiring: a whoosh only on beat changes and chapter cards (not every line), a thunk on chapter title cards and big number slams, a shutter click on screenshot drops, soft keyboard ticks under typed terminal lines, quiet ticks on SVG nodes (skip them when nodes land closer than 0.15 s apart), a zap on errors. No sound on plain text builds.
- Synthesize SFX in numpy (filtered noise sweeps, short sine/saw blips with fast envelopes) or use open-licensed SFX files credited in `assets/CREDITS.md`.
- Real clips play muted (their own audio is never in the mix unless it is the point of the scene).
- Fade out the last 0.6 s, normalize to a -1.5 dB peak. Copy `mix.wav` into the project's `assets/` (HyperFrames) or `public/` (Remotion). Long: also keep per-chapter slices (`mix_chNN.wav`) if you render per chapter (section 5a).

## 4. Design spec (applies to both renderers)
- **Canvas**: Short 1080x1920; Long 1920x1080. 30 fps, length = timing.json `total` rounded up to a frame.
- **Background**: solid #000000 for the whole video, set on the root/base layer (`--bg`). Scenes and sub-compositions are transparent (no `background` on scene roots, no full-canvas `<rect>` in SVGs) so the one black base shows through; nothing ever paints a non-black full-frame layer. Optional atmosphere on top of black, kept subtle:
  - a 1 px grid at opacity <= 0.03;
  - drifting particles/dust in accent colors at opacity <= 0.15, each **<= 6 px across and no blur over 2 px**;
  - a light sweep across a scene's hero element: a narrow white (or brand accent) band at opacity <= 0.12, clipped to the hero element's bounds, crossing it once in 0.4-0.8 s. It never covers the full frame and never stays on screen as a tint.
  Never a colored gradient, vignette color, radial glow or blob behind content.
- **Glow**: neon outlines via layered `box-shadow` / `text-shadow` or SVG `feGaussianBlur` (stdDeviation <= 8 at 1080 px) on graphics. Glow hugs its element; it is not a backdrop. Never CSS filters on footage or screenshots (HyperFrames contract): grades, blur and dimming on real images go through `npx hyperframes media-treatment`.
- **Scene timing**: Short: one scene per script line. Long: one scene per `beat`. A scene starts 80 ms before its first line's `start` so visuals lead the voice, and ends at the next scene's start.
- **Entrance**: every scene gets a 0.22 s fade plus a zoom punch (Short 8%, Long 4%), EXCEPT the first scene. Frame 0 must already show the static hook text (different words from the spoken line), the full hero visual (logo or emblem) and the black background, no fade-in.
- **Easing**: `power3.out` for moves, `back.out(1.9)` for pops, `sine.inOut` for drifts and camera pans (Remotion: `Easing.out(Easing.cubic)`, `Easing.back(1.9)`, `spring`).
- **Motion on every real asset** (a still never sits still): Ken Burns push-in or pan (Short: scale 1.0 to 1.12 over the line; Long: 1.0 to 1.06 over the beat, slower), parallax between screenshot and its frame, a highlight box or spotlight that draws onto the part being talked about (the rest dims to 40% via a black overlay at 60% opacity on the screenshot only, never on the background), zoom-to-region punch-ins, a glint sweep across logos. Animate transforms only.
- **Effects** a scene can trigger: shake (px), RGB channel split, color flash (a <= 3-frame accent flash at <= 0.35 opacity, then straight back to black), zoom punch. Long: use shake, RGB split and flashes sparingly (errors and big reveals only).
- **Scene kit** (each a reusable sub-composition / component; every scene has a 9:16 and a 16:9 layout — in 16:9, put the visual on the left ~60% and its labels/notes on the right, or centre wide diagrams):
  - real-asset scenes: `logo_reveal`, `repo_card` (GitHub dark-mode screenshot in a dark browser frame, live star count ticks up, highlight on the README line that matters), `site_shot`, `terminal_clip` (real command and output in a black terminal window), `video_clip`, `stat_drop` (real number counting up, source label underneath), `logo_wall`;
  - SVG scenes (section 4b): `svg_flow`, `svg_diagram`, `svg_compare`, `svg_chart`, `svg_analogy`, `svg_icons`;
  - drawn scenes: code card (traffic-light dots, typed-on syntax-colored lines; only snippets tested in research; Long: up to ~18 lines, with a highlight bar walking down the lines as they're explained), pill chip, big title slam with radiating SVG rays ("FIX #1 / DECORATORS"), file + sliding gates + padlock, shockwave ring, red SVG lightning + "CRASH!" + shake, cards flying out with a counter, split recap cards sliding in from both sides, `</>` SVG emblem;
  - Long only: `chapter_card` (chapter number in marker font, title slams in, a thin progress track showing which chapter of N, then clear-to-black), `roadmap` (the chapter list building line by line, the current chapter later highlighted when it's revisited), `split_explain` (diagram left, code card right, linked by an arrow that draws on), `recap_grid` (one card per chapter popping in order), `end_screen` (logo + ask on the left ~55%, right ~45% empty black for YouTube elements).
- **Frames for real assets**: dark browser chrome (#111 bar, traffic-light dots, URL pill showing the real domain), phone frame for mobile UIs, terminal window (#0A0A0A body) for CLIs; 24 px rounded corners and a 1 px #2A2A2A border. Frames are the only near-black surfaces allowed, and only behind the asset they hold.
- **Captions**:
  - Short: word-pop from timing.json `words`. Inter Black 82 px, 9 px ink stroke (`-webkit-text-stroke` with `paint-order: stroke fill`); keywords YEL; the current word gets a PINK (keyword) or VIO pill and a 1.25x pop. Centre each cue and re-centre as words arrive so line 1 never starts as a lone word at the left edge. Centre y ~1430, max width 940. No caption background box.
  - Long: subtitle style. Inter Bold 50 px, white, 6 px ink stroke, keywords YEL, the current word turns YEL with no pill and no scale pop. At most 2 lines, max width 1500, centred, baseline of the lower line at y ~1010. No background box. Hide burned captions during chapter cards. The SRT is also uploaded to YouTube as closed captions.
- **Safe zones**:
  - Short: key content in y 120-1250 and x 60-1020. Captions sit at 1290-1600. Nothing important below 1650 or under the right-side button column.
  - Long: key content in x 100-1820, y 70-890. Captions sit at 920-1030. During the last 20 s keep x 1050-1920 empty for end-screen elements. Keep the top-right corner free of key text for ~2 s whenever a YouTube card might appear.
- **Progress bar**: Short: y 42, width 980, YEL fill tied to time. Long: a 4 px bar at y 8, width 1880, with tick marks at chapter starts and the current chapter's title in small type (Inter Bold 26 px, #A0A0B0) at top-left; hide it on chapter cards.
- **Fonts**: bundle Inter Black and Inter Bold as files (`assets/fonts/` + `@font-face` in HyperFrames; `@remotion/google-fonts/Inter` or `staticFile` in Remotion). SVG text uses the same bundled font. Also bundle one handwritten marker font for `note`s and hand-drawn labels (Caveat Bold or Kalam Bold, both OFL, from `@fontsource/caveat` / `@fontsource/kalam` on npm, or `@remotion/google-fonts`).

## 4b. SVG graphics (use when needed)
Use SVG whenever a scene needs something drawn rather than shown: how-it-works flows, architecture, request/response paths, comparisons, simple charts, analogies, icons, arrows, rays, the emblem. Use it for logos whenever an SVG logo exists. Don't use SVG to imitate a real product's UI (that's a screenshot) or to draw people, characters or artworks.
- **Source**: author it yourself (hand-written or generated by a small script from `research.md` data), or take icons from open-licensed sets. Sanitize downloaded SVGs (section 0b rules) and run `npx svgo` on everything.
- **Black-background rules**: transparent SVG root, no full-size background `<rect>`, no fill on the root. Shapes use stroke-first neon line-art: 4-6 px strokes in accent colors, fills either none, #000, or the accent at <= 0.15 opacity. Text inside nodes is #FFFFFF or ink on a solid accent chip. Never a gradient fill that reads as a colored backdrop.
- **Setup**: inline the SVG in the scene (HyperFrames: inside the sub-composition `<template>`; Remotion: as JSX) so every element is addressable; give every animated element a stable id; set an explicit `viewBox` matching the content safe area (Short e.g. `0 0 1080 1130`; Long e.g. `0 0 1720 820`) and `width`/`height`. Keep it under ~40 animated elements per scene (Long: ~60 for a beat that builds over several sentences).
- **Glow**: one shared `<filter id="glow">` (`feGaussianBlur` stdDeviation 4-8 + `feMerge` with the source) applied to strokes, not to whole groups with text.
- **Animation** (deterministic, time-driven):
  - draw-on lines/arrows: `stroke-dasharray` = `stroke-dashoffset` = path length (measured once at build time), then tween `stroke-dashoffset` to 0;
  - nodes pop with `scale` from their own centre (`transform-box: fill-box; transform-origin: center`), `back.out(1.9)`;
  - data dots travel along a path: position = `path.getPointAtLength(progress * L)` driven by timeline time;
  - chart bars grow with `scaleY` from the baseline; numbers count up in sync.
  - HyperFrames: all tweens on the scene's paused GSAP timeline. Remotion: compute from `useCurrentFrame()` with `interpolate` / `spring`.
- **Timing to voice**: each node/arrow appears on the word that names it (timing.json `words`), so the diagram builds as it's spoken.
- **Sizing**: Short: lines >= 4 px, text >= 44 px, at most ~6 nodes. Long: lines >= 3 px, text >= 34 px at 1920 width, at most ~9 nodes per diagram.

## 4c. Build-as-spoken (from the reference video)
A reference explainer (a 72 s news video on a model launch, voice only, all motion graphics, no music) held attention with very little: no face, no footage, yet every second something new was being drawn. These rules come from it and apply to both formats.
1. **Elements land on their word.** Every item in a line's `build` starts its entrance at `build[].t - 0.05 s` and finishes within 0.2-0.3 s. The title is there when the sentence starts, the number arrives when it's said, the bracket draws when the margin is named. The 80 ms scene lead still applies to the scene as a whole.
2. **Entrance vocabulary** (transforms, opacity and stroke-dashoffset only): text fades from #A0A0B0 at 0.4 to white or accent; lines, arrows, brackets, outlines draw on; boxes trace their stroke first, then the label pops inside; bars grow from the baseline with the value counting up, then a `#1` badge pops on the winner; punchline numbers slam big (Short 160-220 px, Long 140-200 px) in an accent color with slight overshoot; icons pop from centre; checkmarks draw on.
3. **Handwritten note layer.** `note` text in the marker font (Short 52-64 px, Long 44-56 px), in YEL or CYAN (RED for caveats), writes on left to right (a `clip-path` / mask wipe over ~0.4 s) on its trigger word, beside the element it explains, sometimes with a short hand-drawn arrow or bracket (SVG path with slight wobble, 4 px round-cap stroke). At most once per beat.
4. **Summary pill per beat.** A rounded chip at the bottom of the content safe zone (Short: centre y ~1200, Inter Black 44 px; Long: centre y ~850, Inter Black 38 px), white text on #111 with a 1 px #2A2A2A border, or ink on an accent chip for the strongest beat. It fades from grey to white when the beat's key claim is spoken and stays until the cut. It never repeats the caption word for word.
5. **Hand-drawn emphasis on proof screenshots.** Benchmark tables, leaderboards and charts are dropped in, then annotated: a marker circle or rounded box draws around the row that matters, a highlighter bar (accent at 0.35 opacity) sweeps under the name, rank tags pop beside it. The rest of the shot dims.
6. **Competitors are hatched.** In comparisons and leaderboards, the subject's bar or box is solid accent (a 2-stop accent gradient inside the bar itself is fine) and the others use an SVG diagonal-hatch `<pattern>` in #3A3A4A strokes with a grey outline.
7. **Carry the hero across scenes.** The opening hero (logo or key image) shrinks into a corner thumbnail (Short ~180 px wide, top-left of the safe zone; Long ~200 px, top-left under the chapter title) and rides along through the data beats, then comes back full size at the end. `carry` drives this: animate it as one element on a full-length layer, not as two copies.
8. **Clear-to-black between sections.** At section boundaries (Short: hook -> fix #1 -> fix #2 -> recap; Long: every chapter boundary, then a `chapter_card`) everything fades out together over ~0.2 s, leaving a beat of empty black (just the grid) before the next build starts. Inside a section, scenes cut directly.
9. **End on the opening image.** Short: the final beat morphs back into frame 0's hero (same position and scale), so the loop point is seamless. A good closer is a fun fact that links the name to the topic (in the reference, "carbon under pressure becomes a diamond": a periodic-table tile pressed from four sides morphed into a diamond and back into the crystal hero). Long: the outro brings the hero back full size on the left for the `end_screen`, no loop needed.
10. **Leave room.** One beat has 3-6 elements on screen at once (Long: up to ~8 when a beat builds over several sentences; clear old elements out as new ones need the space). Don't fill every pixel.

Added scene-kit entries (all SVG on black, same rules as section 4b): `svg_timeline`, `svg_leaderboard`, `svg_pipeline` (3 outlined boxes joined by arrows, each filling with a handwritten label, then a big percentage underneath), `svg_shortcut` (task box -> goal box, a dashed shortcut arrow that gets a red ✗, the long correct path underneath, then the result number), `rollout_stack` (lock icon "not public yet", then rows for who gets it now / soon, the current one green with a check), `price_card`, `transform_morph`, `big_number`.

## 5a. Build with HyperFrames (default)
1. `npx hyperframes init <topic>-<short|long>`; set the root to the format's canvas (1080x1920 or 1920x1080), background #000, and `data-duration` to `total`. Put the section 0b assets under the project's `assets/` (paths `assets/...`, no leading `/`).
2. Generate the HTML from timing.json with a small script rather than by hand, so every time comes from the data:
   - `index.html` holds only: the black background host, one scene host per scene (`class="clip"`, `data-start`, `data-duration`, `data-track-kind="graphics"`), the progress bar, one captions host (`data-track-kind="captions"`) and `<audio id="mix" src="assets/mix.wav">`.
   - Each scene is a sub-composition in `compositions/<nn>-<scene>.html` with styles/markup/script inside `<template>`, root styled as `#root` with a transparent background, and one paused GSAP timeline registered as `window.__timelines["<id>"] = tl`. Long: reuse one template per scene type and pass the content in through variables, rather than writing 60+ unique files by hand.
   - SVG scenes inline their sanitized SVG in the template; SVG logos may be inline or `<img data-var-src="assets/logo/x.svg">`.
   - Real images are `<img>` with `data-var-src`; real clips are a timed `<video class="clip" muted>` (time the video or its wrapper, never both; never `play()`/seek it from script).
   - Caption cues: one caption group per line, each word a timed element with a stable id (e.g. `#c03w2`); pop and pill are GSAP tweens on a child, never on the `.clip`.
   - Copy, colors and swappable assets are variables (`data-var-text`, `data-var-src`, `var(--yel)`, `var(--bg)`).
3. Before hand-writing a caption style, transition, frame, SVG diagram or effect, check `npx hyperframes catalog` and adapt a registry block to the spec above if one fits. Strip any background a block brings with it.
4. No `Math.random()` (use a seeded PRNG), no timers, no `repeat: -1`, no network fetches at render time (all assets local, including SVG icons and fonts); drifts are functions of timeline time.
5. `npx hyperframes lint`, then `npx hyperframes check --json`; fix every error.
6. `npx hyperframes snapshot --at <key moments>` and read the PNGs; fix and repeat. Short: each line end - 0.1, slams, logo reveal, screenshot highlights, SVG diagrams fully drawn, crash, lock. Long: each beat end - 0.1 for the first two chapters plus every chapter card, every fully drawn diagram, the roadmap, recap and end screen.
7. Render `--quality draft` while iterating, then `--quality delivery --output raw.mp4`.
   - Long: render a draft of the cold open + chapter 1 first and time it, then estimate the full render and tell the user the estimate with `SendUserMessage`. If the full render would be very long or memory-heavy, split the project per chapter (each chapter its own composition and its `mix_chNN.wav` slice, cut at the chapter-boundary pause), render each in the background with `run_in_background`, then join with the ffmpeg concat demuxer (`-f concat -safe 0 -i list.txt -c copy`) and check there's no audio gap or click at the joins.

## 5b. Build with Remotion (when asked)
1. Scaffold per `remotion-create` (blank TypeScript template). Register `<Composition id="Video" width={W} height={H} fps={30} durationInFrames={Math.ceil(total*30)}>` (1080x1920 or 1920x1080) with a black `<AbsoluteFill style={{background: "#000"}}>` base; scene components have no background. Long: also register one composition per chapter for partial renders and previews.
2. Copy assets to `public/`. Import timing.json; render one `<Sequence from={Math.round((start-0.08)*30)} durationInFrames={...}>` per scene, mapping `scene` to a scene-kit component and passing its `asset` paths via `staticFile()`. Use `<Img>` for images and SVG files you don't animate, inline JSX `<svg>` for SVG scenes you animate, and `<OffthreadVideo muted>` for clips. Background, progress bar and captions are full-length layers. Add `<Audio src={staticFile("mix.wav")} />` once.
3. Animate only with `useCurrentFrame()` + `interpolate` / `spring`; no CSS transitions or `Math.random()` (use `random(seed)`); no remote URLs at render time. SVG path lengths come from `@remotion/paths` (`getLength`, `getPointAtLength`, `evolvePath`).
4. Captions per `remotion-captions`: convert `words` to its caption format and page them per line, with the format's styling above.
5. Check stills with `npx remotion still Video --frame=<n> out.png` at the same moments as 5a.6.
6. Render per `remotion-render`: `npx remotion render Video raw.mp4 --codec=h264 --crf=19` (Long: per chapter with `--frames=<a>-<b>` if needed, then concat).

## 6. Finalize loudness
Loudness-normalize the rendered file to about **-14 LUFS**:
`ffmpeg -i raw.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=7 -c:a aac -b:a 192k -movflags +faststart <topic>_<short|long>.mp4`.
The first build came out at -19.7 LUFS, too quiet next to other videos.

## 7. QA before sending (all of these, every time)
1. Preview sheet: extract frames at the key moments (as in 5a.6) from the final MP4 with ffmpeg, tile them (Short 270x480; Long 480x270, several sheets) and Read them. Look for overlaps with the logo/emblem, clipped text, chips colliding with captions, layers hiding each other, SVG lines too thin to read, and bright light-mode slabs.
2. **Black-background check (measured, not eyeballed)**: decode frames at 2 fps (Long: 0.5 fps) to RGB (`ffmpeg -i <final>.mp4 -vf "fps=2,format=rgb24" -f rawvideo -` into numpy) and sample four 40x40 corner patches plus the edge strips outside the safe zone (Short: x 0-50 and x 1030-1080; Long: x 0-60 and x 1860-1920). Each patch's mean must be <= 10 on every channel. Any frame over the limit gets snapshotted and fixed: usually a scene root or SVG with a background, an oversized particle, a sweep that escaped its element, or a flash that lasted too long.
3. First-frame check: tile frames 0, 4, 8, 14. Frame 0 must show the hook text, the hero logo/emblem and a black background.
4. Real-asset check: every product/tool named in the script appears as its real logo or screenshot; screenshots are sharp (no upscaling past 1.5x), dark-mode where available, cropped to what matters, and show the real current UI; numbers match `assets/data/` and research; every asset and SFX file has a line in `assets/CREDITS.md`; no photos of people.
5. SVG check: every diagram matches `research.md` (correct order, labels, arrow direction); no downloaded SVG still contains scripts, event handlers or external links (`grep -E "<script|on[a-z]+=|xlink:href=\"http|href=\"http" assets/svg compositions -r` returns nothing).
6. `ffprobe`: the format's resolution, 30 fps, H.264 + AAC, duration matches `total` (Long: 7:00-10:00 unless the user asked otherwise). `ebur128`: I near -14 LUFS, true peak below -1 dB.
7. Audio check: no music anywhere in `mix.wav` (only voice and the SFX events listed in timing.json); SFX never louder than the voice.
8. The whisper transcript matches the script.
9. Fact check: every claim, number and code snippet on screen matches `research.md`.
10. HyperFrames only: `check --json` is clean.
11. Build-as-spoken check (section 4c): for 3 random lines (Long: 2 per chapter), snapshot at each `build[].t - 0.1` and `build[].t + 0.3`; the element must be absent before and fully in after. Every beat after the hook shows its pill. Every section/chapter boundary shows a clear-to-black beat.
12. Short: the last frame matches frame 0's hero position (loop). Long: every chapter card appears at the timestamp listed in `script.md`; no gap longer than 8 s without a new on-screen element; the last 20 s leave the end-screen area empty; per-chapter renders join without a gap or click.

## 8. SEO package (after QA passes)
Load the `yt-seo` and `yt-package` skills (Long also `yt-chapters`) and follow them where they apply. Write everything from the finished video and `research.md` (its search phrases); never promise anything the video doesn't show. Count characters with code, don't estimate.
1. **Primary keyword**: the phrase a real person types for this topic (from research), e.g. "ollama tutorial" or "python decorators explained". Use it in the title, the first line of the description and the first tag.
2. **Title**: write 3 options, pick one. Keyword in the first half, one curiosity or payoff element, wording different from the on-screen hook / thumbnail text, no clickbait the video doesn't pay off, no ALL CAPS beyond one word, at most one emoji.
   - Short: 40-60 characters; first ~40 must carry the meaning.
   - Long: 50-70 characters; can promise the depth ("…Explained in 8 Minutes", "Full Beginner Guide").
3. **Description**:
   - Short: 2-4 lines: what the viewer learns with the keyword; the key takeaway; one call to action plus the official project link when a real tool is featured; last line 3-5 hashtags, `#shorts` first.
   - Long: 150-300 words: first 2 lines are the hook + keyword (they show in search and above "more"); a 2-3 sentence summary; **chapters** list from `timing.json` starting at `00:00`, at least 3 chapters, each at least 10 s, one per line (`00:00 Intro`, `00:32 How it works`, …); links to the official project/docs and the sources; one call to action; 3 hashtags at the end (no `#shorts`).
4. **Tags**: 12-20 (Long: 15-25), comma-separated, under 450 characters (Long: under 500). Order: primary keyword, close variants, the broader topic, related tools/terms from research, beginner phrasing ("for beginners", "explained", "tutorial"). No competitor channel names, no unrelated trending tags.
5. **Long only — thumbnail** (`thumbnail.png`, 1280x720, under 2 MB): build it as its own HyperFrames/Remotion still on black: the real logo or the key visual large on one side, 2-4 words of text (Inter Black, 140+ px, one keyword in YEL, different from the title), and one contrast element (a red ✗ vs green ✓, a big number, an arrow). Readable at 160x90: check by downscaling and Reading it. Also write 2 alternate thumbnail text options in `seo.md` for A/B testing.
6. **Long only — pinned comment**: one question that invites replies about the topic, plus where to find the code or sources.
7. **Bonus** — Short: an Instagram / Reels caption (hook + 2-line summary + 5-8 hashtags). Long: a 1-2 line community-post / Short teaser idea pointing to the video.
8. Save it all to `seo.md` with headings: Title (chosen + 2 alternates), Description, Chapters (Long), Tags, Hashtags, Thumbnail text (Long), Pinned comment (Long), Bonus.

## 9. Deliver
Send the MP4 (display render), the SRT (attach), `research.md` (attach), `seo.md` (attach), `assets/CREDITS.md` (attach); Long also `thumbnail.png` (render) and `script.md` (attach). Then in the reply:
- a few bullets on the format and length, what is in the video, which real assets and SVG scenes it uses, which renderer built it, and any known limitation (e.g. an asset that couldn't be fetched and was drawn in SVG instead); don't paste the whole script back;
- the **chosen title, description (with chapters for Long) and tags** in copy-ready code blocks;
- a short `Sources:` list from the research;
- end with **ship it, or change it?**

## Host option (only when the user asks and provides their own photo)
- SadTalker (weights on Hugging Face `vinthony/SadTalker` + GitHub releases) gives a convincing head + lips, but on a 2-core CPU it runs at ~7 s per frame, roughly 2 h for 43 s. Use it only for the hook and outro (~10 s, ~30 min) and warn the user about the wait first. For Long videos, never run it on the full runtime: hook and outro only.
- Wav2Lip (`wav2lip.pth` and `s3fd` in the same HF repo) renders 43 s in ~3 min, but the mouth is blurry. Feather-blend only an oval around the mouth into the sharp original and use it small (a 250 px corner bubble).
- Python 3.13 fixes: patch `np.float/int/bool/VisibleDeprecationWarning` in the sources, `pip install audioop-lts`, skip `gfpgan` (basicsr won't build), make the enhancer import optional, flatten `t`/`s`/`trans_params` arrays in face3d preprocess, add `weights_only=False` to every `torch.load`, and pass keyword args to `librosa.filters.mel`.
- Place the host clip as a muted video in the hook/outro scenes (the voice is already in mix.wav). Keep the host's photo background inside its bubble frame; the canvas stays black.
- A true voice clone needs a 30-60 s recording of the user. Never imply the stock voice is theirs.
- If the user changes their mind about showing their face, stop the host render (`pkill -f`) and ship with the logo/emblem.

## Known weaknesses to avoid (from reviews)
- Frame 0 showed only the emblem with no text, and the opening caption began as one word at the left edge. Fix: a static on-screen hook visible from frame 0, plus centered progressive captions.
- Short had no designed loop point. Fix: make the outro line feed back into the hook.
- Mixed too quiet. Fix: loudnorm to -14 LUFS.
- Music competed with the voice and added nothing. Fix: no music at all; voice + light SFX only.
- Drawn stand-ins for real products looked generic. Fix: section 0b real assets, with motion on every still.
- Black background could leak: white light-mode screenshots, oversized soft particles, sweeps acting as tints, scene roots or SVGs carrying their own background. Fix: dark-mode capture or media-treatment dimming, particle size cap, sweep clipped to its element, transparent scene roots/SVGs, and the measured corner check in QA 7.2.
- Abstract "how it works" beats were hard to follow as text alone. Fix: section 4b SVG flows/diagrams that build word by word.
- Whole scenes appeared at once, so the eye had nothing new to follow mid-sentence. Fix: section 4c, each element keyed to its word through `build`.
- Muted viewers lost the thread. Fix: a summary pill on every beat.
- Dense benchmark screenshots were unreadable on a phone. Fix: dim the screenshot, then circle and highlight the one row that matters, and add a rank tag.
- Long risk: a Short's pace stretched to 10 minutes is exhausting, and a static 10 minutes is boring. Fix: beats that build over 2-4 sentences, lighter SFX and effects, a pattern interrupt every 20-40 s, and chapter cards with clear-to-black between chapters.