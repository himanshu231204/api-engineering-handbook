# Video Pipeline and DNS Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared script-to-video pipeline under `video/` and use it to produce one reviewed, rendered pilot video for the DNS chapter.

**Architecture:** Python stdlib tools (`video/tools/`) parse and validate a Markdown script, produce narration audio (or a silent fallback), captions and a frame-accurate timeline JSON. A Remotion project (`video/kit/`) renders that timeline from a fixed set of scenes. `render.sh` chains them and `ffmpeg` muxes the mp4.

**Tech Stack:** Python 3 stdlib (`unittest`), Node 22, Remotion 4.x (version pinned exactly in `package.json`), React + TypeScript, `ffmpeg`.

**Spec:** `video/specs/2026-11-10-video-series-design.md`

## Global Constraints

- Videos are 1920×1080, 30 fps, H.264 mp4, with burned-in captions and a separate `.srt`.
- Length 5:00–10:00; narration 750–1,500 words at 150 words per minute.
- Beat names, in order: `Hook`, `Why It Matters`, `Concept`, `How It Works`, `Demo`, `Mistakes`, `Recap`, `Next`.
- Scene names (single source of truth `video/kit/scene_names.json`): `Title`, `Concept`, `DiagramWalk`, `Terminal`, `CodeReveal`, `Mistakes`, `Recap`, `Quiz`.
- Palette: green main path, blue client, amber data, red failure, purple AI, slate infra; no text under 12px at 1080p.
- Python tools are stdlib-only. Node tooling lives only in `video/kit/`.
- Credentials come only from environment variables (`VIDEO_TTS_PROVIDER`, `VIDEO_TTS_BASE_URL`, `VIDEO_TTS_API_KEY`, `VIDEO_TTS_MODEL`, `VIDEO_TTS_VOICE`); nothing is committed. With no provider the render is captioned and silent.
- `render.sh` refuses a script without `reviewed: true` in its frontmatter.
- Nothing under `video/` may break `scripts/check_links.py`, `scripts/check_chapters.py`, `scripts/check_svgs.py` or `mkdocs build --strict`: no relative Markdown links in `video/**/*.md` and nothing added under `docs/`.
- No placeholder text (`TODO`, `coming soon`) in any committed script.
- Gitignored: `video/out/`, `video/.cache/`, `video/kit/node_modules/`, `video/kit/public/diagrams/`.

## Review Focus

1. A script saved with Windows line endings (`\r\n`) must parse the same as `\n`.
2. Narration containing non-ASCII text, backticks, or inline code must count words, wrap captions and build SRT correctly.
3. A `[scene: ...]` cue naming a missing scene, missing SVG, or a step range beyond the diagram's step count must be rejected with a message naming the line.
4. A beat with no narration, or a duplicated or misspelled beat heading, must be rejected rather than rendering a zero-length scene.
5. A failure partway through narration synthesis or rendering must not leave a partial mp4 in `video/out/` (write to a temp path, move on success).

## File Structure

```
video/
  .gitignore
  README.md                       how to run; env vars; review rule
  templates/script.md             blank script with all 8 beats
  scripts/01-api-foundations/dns.md   the pilot script
  tools/
    script_model.py               parse_script and dataclasses
    check_script.py               validation + CLI
    captions.py                   caption chunking and SRT
    tts.py                        provider adapter, durations
    timeline.py                   build_timeline
    draft_script.py               chapter -> skeleton
    render.sh                     pipeline driver
    tests/                        unittest files, one per module
  kit/
    package.json, tsconfig.json, remotion.config.ts
    scene_names.json
    diagram_steps/01-dns-resolution.json
    src/{index.ts, Root.tsx, Episode.tsx, theme.ts, types.ts}
    src/scenes/{registry.ts, Title.tsx, Concept.tsx, DiagramWalk.tsx,
                Terminal.tsx, CodeReveal.tsx, Mistakes.tsx, Recap.tsx, Quiz.tsx}
```

---

### Task 1: Script model and validator

**Files:**
- Create: `video/tools/script_model.py`, `video/tools/check_script.py`, `video/tools/tests/test_script_model.py`, `video/tools/tests/test_check_script.py`, `video/templates/script.md`, `video/kit/scene_names.json`, `video/.gitignore`

**Interfaces:**
- Produces (`script_model.py`):
  - `BEAT_NAMES: list[str]` (the eight names above, in order)
  - `@dataclass Cue: scene: str; args: dict[str, str]; line: int`
  - `@dataclass Beat: name: str; narration: str; cues: list[Cue]; code_blocks: list[str]`
  - `@dataclass Script: meta: dict[str, str]; beats: list[Beat]`
  - `parse_script(text: str) -> Script` (normalizes `\r\n`; frontmatter is `key: value` lines between `---` fences; a cue is a line `[scene: Name key=value ...]`, removed from narration; fenced code blocks inside a beat go to `code_blocks`, not narration; raises `ValueError` with the line number on malformed input)
  - `narration_words(script: Script) -> int`
  - `estimated_seconds(script: Script) -> float` (words / 150 × 60)
- Produces (`check_script.py`): `check_script(path: Path, repo_root: Path) -> list[str]` (empty list means valid) and a CLI `python3 video/tools/check_script.py <script.md>...` exiting 1 on any error. `scene_names.json` is a JSON list of the eight scene names.

- [ ] **Step 1: Write failing tests** in `test_script_model.py`: `test_parse_basic_script_has_eight_beats_in_order`; `test_crlf_input_parses_identically`; `test_cue_removed_from_narration_and_args_parsed` (`[scene: DiagramWalk svg=01-dns-resolution.svg steps=1-6]` → `Cue("DiagramWalk", {"svg": "01-dns-resolution.svg", "steps": "1-6"}, line)`); `test_code_block_not_counted_as_narration`; `test_unicode_and_backticks_counted_as_words` (`"résumé `dig` 日本語 ok"` → 4 words); `test_estimated_seconds_is_words_over_150_times_60`.
- [ ] **Step 2: Write failing tests** in `test_check_script.py`, each building a temp repo with a tiny chapter, `examples/` file and SVG: `test_valid_script_passes`; `test_missing_chapter_file_fails`; `test_misspelled_beat_heading_fails`; `test_duplicate_beat_fails`; `test_empty_beat_narration_fails`; `test_word_count_below_750_fails` and `test_above_1500_fails`; `test_unknown_scene_fails_with_line_number`; `test_missing_svg_fails`; `test_steps_beyond_sidecar_count_fails`; `test_demo_code_line_not_in_chapter_or_examples_fails`; `test_demo_code_line_present_in_chapter_passes`; `test_todo_placeholder_fails`; `test_secret_like_string_fails` (`sk-` followed by 20+ alphanumerics, or `Bearer ` followed by 20+ characters).
- [ ] **Step 3: Run and confirm failure.** `python3 -m unittest discover -s video/tools/tests -v` → ImportError or FAIL.
- [ ] **Step 4: Implement `script_model.py`** per the Interfaces block (line-by-line state machine; no regex-only parsing of fences).
- [ ] **Step 5: Implement `check_script.py`.** Rules as spec section 5: frontmatter keys `chapter`, `part`, `index`, `title`, `target_seconds` present and `chapter` exists under `repo_root`; beats exactly `BEAT_NAMES` in order; non-empty narration; 750–1,500 words; scene names from `kit/scene_names.json`; `svg` args exist under `docs/assets/diagrams/`; `steps=a-b` within `kit/diagram_steps/<svg-stem>.json` step count; every non-blank line of every Demo code block appears, after stripping, in the chapter text or any file under `examples/`; no `TODO`/`coming soon`/`lorem ipsum`; no secret-like strings. Every error string starts with the script path and line number where known.
- [ ] **Step 6: Create `video/templates/script.md`** (frontmatter with `reviewed: false` plus the eight empty beat headings with one-line prompts in HTML comments), `scene_names.json`, and `video/.gitignore` with the ignored paths from Global Constraints.
- [ ] **Step 7: Run tests.** `python3 -m unittest discover -s video/tools/tests -v` → all PASS.
- [ ] **Step 8: Commit.** `git add video && git commit -m "feat(video): script model and validator"`

---

### Task 2: Captions, narration and timeline

**Files:**
- Create: `video/tools/captions.py`, `video/tools/tts.py`, `video/tools/timeline.py`, tests `test_captions.py`, `test_tts.py`, `test_timeline.py` in `video/tools/tests/`

**Interfaces:**
- Consumes: `Script`, `Beat`, `Cue`, `parse_script` from Task 1.
- Produces:
  - `captions.py`: `@dataclass Caption: start: float; end: float; text: str`; `chunk_narration(text: str, start: float, end: float, max_chars: int = 42) -> list[Caption]` (split on whole words, no chunk longer than `max_chars` unless one word exceeds it, time distributed by character count, chunks contiguous and covering `[start, end]` exactly); `build_srt(captions: list[Caption]) -> str` (1-based index, `HH:MM:SS,mmm --> HH:MM:SS,mmm`, blank line between entries).
  - `tts.py`: `class TTSProvider(Protocol): def synthesize(self, text: str, out: Path) -> float` (returns seconds); `get_provider(env: Mapping[str, str]) -> TTSProvider | None` (`None` when `VIDEO_TTS_PROVIDER` is unset or `none`; `"openai-compatible"` posts to `{VIDEO_TTS_BASE_URL}/audio/speech` with the key from `VIDEO_TTS_API_KEY` using `urllib`, writes the returned audio, reads its duration with `ffprobe`; unknown names raise `ValueError`); `estimate_seconds(text: str) -> float` (words / 150 × 60); `beat_durations(script: Script, provider: TTSProvider | None, out_dir: Path) -> dict[str, float]` (provider durations plus 0.4 s trailing pause, or `estimate_seconds` plus 0.4 s when `provider` is `None`; synthesizes into `out_dir/<beat-slug>.mp3`; if any beat fails, removes files it created in this call and re-raises).
  - `timeline.py`: `build_timeline(script: Script, durations: dict[str, float], fps: int = 30) -> dict` returning `{"fps", "width": 1920, "height": 1080, "title", "part", "index", "beats": [{"name", "startFrame", "frames", "audio": str | None, "cues": [{"scene", "args", "startFrame", "frames"}], "captions": [{"startFrame", "endFrame", "text"}]}], "totalFrames"}`; cues share their beat's frames equally; a beat with no cues gets a default scene (`Concept` for Hook/Why It Matters/Concept/Next, `Recap` for Recap, `Mistakes` for Mistakes, `Terminal` for Demo with the beat's first code block as `args.lines`, `DiagramWalk` is never defaulted); beats are contiguous from frame 0.

- [ ] **Step 1: Write failing tests.** `test_captions`: `test_chunks_respect_max_chars`; `test_chunks_cover_range_contiguously`; `test_unicode_text_chunks_and_srt_roundtrip` (non-ASCII words, one 60-character word); `test_srt_timestamp_format` (`3725.5` s → `01:02:05,500`). `test_tts`: `test_get_provider_none_when_unset`; `test_unknown_provider_raises`; `test_estimate_seconds_matches_150wpm`; `test_beat_durations_without_provider_uses_estimate_plus_pause`; `test_failure_midway_removes_partial_audio` (fake provider raises on the third beat; assert `out_dir` has no `.mp3` left and exception propagates). `test_timeline`: `test_beats_contiguous_and_total_frames_sum`; `test_cues_split_beat_frames_equally`; `test_default_scene_for_beat_without_cues`; `test_demo_default_terminal_uses_first_code_block`; `test_audio_none_when_no_provider`.
- [ ] **Step 2: Run and confirm failure.** `python3 -m unittest discover -s video/tools/tests -v` → the new tests FAIL.
- [ ] **Step 3: Implement `captions.py`, `tts.py`, `timeline.py`** per Interfaces. For `openai-compatible`, JSON body `{"model": VIDEO_TTS_MODEL, "voice": VIDEO_TTS_VOICE, "input": text}`; no request is made in tests.
- [ ] **Step 4: Run tests.** → all PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(video): captions, narration adapter and timeline builder"`

---

### Task 3: Remotion kit scaffold and text scenes

**Files:**
- Create: `video/kit/package.json`, `tsconfig.json`, `remotion.config.ts`, `src/index.ts`, `src/Root.tsx`, `src/Episode.tsx`, `src/theme.ts`, `src/types.ts`, `src/scenes/registry.ts`, `src/scenes/{Title,Concept,Mistakes,Recap,Quiz}.tsx`, `src/scenes/registry.test-check.mjs`

**Interfaces:**
- Consumes: the timeline JSON shape from Task 2; `scene_names.json` from Task 1.
- Produces:
  - `types.ts`: `Timeline`, `BeatTL`, `CueTL`, `CaptionTL` exactly mirroring the Task 2 JSON keys.
  - `theme.ts`: `colors = { green, blue, amber, red, purple, slate, bg, text }` taken from the hex values in `docs/assets/diagrams/01-http-request-anatomy.svg`, `fonts`, and `minFontPx = 12`.
  - Scene component signature, identical for all eight: `(props: { args: Record<string, string>; beat: string; title: string }) => JSX.Element`.
  - `registry.ts`: `export const scenes: Record<string, React.FC<SceneProps>>` with the eight keys from `scene_names.json`.
  - `Episode.tsx`: composition `Episode` taking `{ timeline: Timeline }`, laying out each beat's cues in `<Sequence>`s, burned-in captions from `captions` at the bottom, and `<Audio>` when `audio` is set.
  - `Root.tsx` registers `Episode` with `durationInFrames` computed from `timeline.totalFrames` via `calculateMetadata`, 1920×1080, 30 fps.

- [ ] **Step 1: Initialize.** Run `npm init -y` in `video/kit`, then `npm install --save-exact remotion @remotion/cli @remotion/captions react react-dom typescript @types/react` choosing a Remotion 4.x release at least two weeks old; commit the exact versions in `package.json` and the lockfile. Add scripts `typecheck` (`tsc --noEmit`) and `check-registry` (`node src/scenes/registry.test-check.mjs`).
- [ ] **Step 2: Write the failing registry check** `registry.test-check.mjs`: reads `scene_names.json` and the keys of `registry.ts` (via a regex on the exported object literal) and exits 1 on any mismatch.
- [ ] **Step 3: Run it.** `cd video/kit && npm run check-registry` → FAIL (no registry yet).
- [ ] **Step 4: Implement** `types.ts`, `theme.ts`, `registry.ts`, `Episode.tsx`, `Root.tsx`, `index.ts`, and the five text scenes. `Title` shows part/index/title; `Concept` shows `args.heading` and `args.body`; `Mistakes` shows `args.items` split on `|`; `Recap` shows `args.items` split on `|`; `Quiz` shows `args.q1..q3` one at a time (answers revealed in the last third of the cue). `DiagramWalk`, `Terminal`, `CodeReveal` are registered as the Task 4 components (import them from files created in Task 4; create temporary stubs returning `null` only inside this task's commit and replace them in Task 4).
- [ ] **Step 5: Verify.** `npm run typecheck` → exit 0; `npm run check-registry` → exit 0.
- [ ] **Step 6: Smoke render.** Write `video/kit/fixtures/smoke.json` (a two-beat timeline using `Title` and `Concept`), then `npx remotion still src/index.ts Episode out/smoke.png --props=fixtures/smoke.json --frame=10 --browser-executable=/opt/pw-browsers/chromium` (path from `/opt/pw-browsers/` as installed here; omit the flag where Remotion can download its own browser). Expected: a 1920×1080 PNG exists; look at it and confirm title text is legible.
- [ ] **Step 7: Commit.** `git commit -m "feat(video): Remotion kit scaffold and text scenes"`

---

### Task 4: Media scenes (DiagramWalk, Terminal, CodeReveal)

**Files:**
- Create: `video/kit/src/scenes/DiagramWalk.tsx`, `Terminal.tsx`, `CodeReveal.tsx`, `video/kit/diagram_steps/01-dns-resolution.json`, `video/kit/fixtures/media.json`
- Modify: `video/kit/src/scenes/registry.ts` (replace the stubs)

**Interfaces:**
- Consumes: the scene prop signature and registry from Task 3.
- Produces:
  - `diagram_steps/<svg-stem>.json`: `{ "width": 880, "height": 500, "steps": [{ "n": 1, "label": string, "x": number, "y": number, "w": number, "h": number }] }`, one entry per numbered circle in the SVG, coordinates in the SVG's own coordinate space.
  - `DiagramWalk` args: `svg` (file name), `steps` (`a-b`). Renders the SVG from `public/diagrams/<svg>` full width, dims everything, and for each step in the range highlights its box (rounded outline in `colors.green`) with its `label` below; each step gets an equal share of the cue's frames.
  - `Terminal` args: `lines` (lines separated by `|`) or a `file` is not supported; types each line character by character over the first 70% of the cue, then holds.
  - `CodeReveal` args: `lines` (separated by `|`), `lang`. Reveals one line at a time, monospace, `minFontPx` respected.

- [ ] **Step 1: Write the failing check.** Extend `registry.test-check.mjs` to also assert every `diagram_steps/*.json` has `steps` with consecutive `n` from 1 and positive `w`/`h` inside the declared `width`×`height`. Run `npm run check-registry` → FAIL (sidecar missing).
- [ ] **Step 2: Create `01-dns-resolution.json`.** Read the element positions of the six numbered circles and their adjacent boxes in `docs/assets/diagrams/01-dns-resolution.svg`; one step each: 1 device cache, 2 resolver, 3 root, 4 TLD, 5 authoritative, 6 IP returned, with a box covering that step's shape and label text.
- [ ] **Step 3: Implement the three scenes** and register them in place of the stubs.
- [ ] **Step 4: Verify.** `npm run typecheck`, `npm run check-registry` → exit 0.
- [ ] **Step 5: Visual check.** Copy the SVG into `video/kit/public/diagrams/`, write `fixtures/media.json` (one `DiagramWalk svg=01-dns-resolution.svg steps=1-6`, one `Terminal`, one `CodeReveal`), render a still at the middle of each cue with `npx remotion still ... --frame=<n>`, and confirm each highlight box sits on the intended shape for all six steps (render a still per step). Adjust the sidecar coordinates until they do.
- [ ] **Step 6: Commit.** `git commit -m "feat(video): diagram walk, terminal and code scenes"`

---

### Task 5: Render driver and script drafting

**Files:**
- Create: `video/tools/render.sh`, `video/tools/draft_script.py`, `video/tools/build_timeline_cli.py`, `video/tools/tests/test_draft_script.py`, `video/README.md`

**Interfaces:**
- Consumes: `parse_script`, `check_script`, `get_provider`, `beat_durations`, `build_timeline`, `build_srt`, `chunk_narration`.
- Produces:
  - `draft_script.py`: `draft_script(chapter_path: Path, part: int, index: int) -> str` returning a template-shaped script with `reviewed: false`: frontmatter filled; Hook from the chapter's "In one line"; Why It Matters / Concept / How It Works / Mistakes / Recap seeded with the corresponding chapter section text as comment-quoted source material for rewriting; Demo seeded with the chapter's first non-Python fenced block; CLI `python3 video/tools/draft_script.py <chapter.md> --part N --index N`.
  - `build_timeline_cli.py`: `python3 video/tools/build_timeline_cli.py <script.md> --out-dir <dir>` writes `timeline.json`, `captions.srt` and any `.mp3` files into `out-dir`, using `get_provider(os.environ)`.
  - `render.sh <script.md>`: runs `check_script.py`; exits 1 with a clear message unless frontmatter has `reviewed: true`; copies referenced SVGs into `kit/public/diagrams/`; runs `build_timeline_cli.py` into `video/.cache/<slug>/`; renders with `npx remotion render` to `video/.cache/<slug>/video.mp4.tmp`; on success moves it to `video/out/<slug>.mp4` and copies the `.srt`; on any failure removes the temp file and exits non-zero.

- [ ] **Step 1: Write failing tests** in `test_draft_script.py`: `test_draft_uses_tldr_one_line_as_hook_source`; `test_draft_has_all_eight_beats_in_order`; `test_draft_demo_uses_first_non_python_code_block`; `test_draft_marks_reviewed_false`; `test_draft_for_every_part1_chapter_parses` (loop over `docs/01-api-foundations/*.md` except `README.md`; each draft must pass `parse_script`).
- [ ] **Step 2: Run and confirm failure.** → FAIL.
- [ ] **Step 3: Implement `draft_script.py` and `build_timeline_cli.py`.**
- [ ] **Step 4: Run tests.** → all PASS.
- [ ] **Step 5: Implement `render.sh`** (`set -euo pipefail`, trap to delete the temp file) and test it by hand: `bash video/tools/render.sh video/templates/script.md` must exit 1 with the "not reviewed" or validation message and leave `video/out/` empty.
- [ ] **Step 6: Write `video/README.md`**: the workflow (draft → rewrite → review → render), env vars, the review rule, where outputs go.
- [ ] **Step 7: Commit.** `git commit -m "feat(video): render driver and script drafting"`

---

### Task 6: DNS pilot script

**Files:**
- Create: `video/scripts/01-api-foundations/dns.md`

**Interfaces:**
- Consumes: `draft_script.py`, `check_script.py`, the DNS chapter `docs/01-api-foundations/dns.md`, `01-dns-resolution.svg` and its sidecar.

- [ ] **Step 1: Draft.** `python3 video/tools/draft_script.py docs/01-api-foundations/dns.md --part 1 --index 5 > video/scripts/01-api-foundations/dns.md`.
- [ ] **Step 2: Rewrite as spoken prose** for about 1,100 spoken words (about 7:20): short sentences, no "as shown above", every claim taken from the chapter. Beats: Hook (TL;DR line); Why It Matters (DNS failures look like "API down"); Concept (name → IP, hierarchy, the contacts-app analogy); How It Works (`[scene: DiagramWalk svg=01-dns-resolution.svg steps=1-6]` narrating each numbered step, then caching and TTL); Demo (the chapter's `text` blocks and Python lookup as `Terminal` and `CodeReveal` cues, using only lines present in the chapter); Mistakes and Production (from "Common Mistakes" and "Production Considerations": lower the TTL before a migration, stale answers); Recap (Key Takeaways) with the three Check Yourself questions in a `Quiz` cue; Next (teaser for URLs, the next row in the Part 1 table).
- [ ] **Step 3: Validate.** `python3 video/tools/check_script.py video/scripts/01-api-foundations/dns.md` → exit 0, no output. Fix until clean.
- [ ] **Step 4: Fact-check pass.** Read the script beside the chapter and confirm every factual sentence, number (for example TTL values), record type and order of servers matches the chapter. Record any correction made in the commit message. Then set `reviewed: true`.
- [ ] **Step 5: Repo checks.** `python3 scripts/check_links.py` → "All relative links resolve."
- [ ] **Step 6: Commit.** `git commit -m "docs(video): add DNS pilot script"`

---

### Task 7: Render the DNS pilot

**Files:**
- Create (gitignored, not committed): `video/out/dns.mp4`, `video/out/dns.srt`
- Modify: `video/README.md` (add the pilot's measured render time and size)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Render.** `VIDEO_TTS_PROVIDER` unset unless the maintainer has supplied a provider: `bash video/tools/render.sh video/scripts/01-api-foundations/dns.md`. Expected: `video/out/dns.mp4` and `video/out/dns.srt` exist; no `.tmp` file remains.
- [ ] **Step 2: Verify length and format.** `ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of default=nw=1 video/out/dns.mp4` → duration between 300 and 600 s, 1920×1080, 30/1.
- [ ] **Step 3: Visual review.** Extract frames at each beat start with `ffmpeg -ss <t> -i video/out/dns.mp4 -frames:v 1 <png>` (into `video/.cache/`), look at each, and confirm: title card correct, diagram highlights land on the right shape for steps 1–6, terminal and code text legible and at least 12px equivalent, captions inside the frame and not overlapping scene text, recap and quiz readable. Fix scene or sidecar problems in the kit and re-render; list what was fixed.
- [ ] **Step 4: Check SRT.** The `.srt` last timestamp is within 0.5 s of the video duration and every caption line is at most 42 characters.
- [ ] **Step 5: Run all repo checks.** `python3 -m unittest discover -s video/tools/tests`, `cd video/kit && npm run typecheck && npm run check-registry`, then from the repo root `python3 scripts/check_links.py`, `python3 scripts/check_examples_compile.py`, `python3 scripts/check_svgs.py`, `python3 scripts/check_chapters.py` → all pass.
- [ ] **Step 6: Commit and push.** `git add video && git commit -m "docs(video): DNS pilot render notes"` then `git push`, and update PR 6's description with the pilot result and how to render it.
- [ ] **Step 7: Hand the mp4 to the maintainer** for the style, pacing and voice review that the spec requires before Phase 1 continues.
