# Video Series Design — one video per handbook chapter

Status: draft for review · Date: 2026-11-10

## 1. Goal and scope

Produce one educational video per chapter of the handbook (about 190 chapters across Parts 00–19; Part 20 is capstone specs and is handled separately). Each video teaches exactly one topic in depth and runs **5–10 minutes**. Topics are never combined: "DNS" and "URLs" are two videos.

Audience: backend and AI engineers, beginner to intermediate.

Success criteria:

- Every video follows the beat structure in section 3 and lands between 5:00 and 10:00.
- Every technical claim in a script traces to its source chapter (section 5).
- A new video can be produced from a chapter with no new tooling work after the pilot phase.
- Nothing under `video/` can break the existing CI checks (links, SVGs, chapter template, MkDocs strict).

Non-goals: on-camera footage, a custom video editor, hosting or publishing automation, translations. Each can be a later spec.

## 2. Approach: pilot first, then scale

- **Phase 0 — Pipeline.** Build the shared script template, Remotion visual kit and render scripts once.
- **Phase 1 — Pilots.** Produce 3 videos from different parts and review the style with the maintainer. Pilot topics: **DNS** (Part 1, concept with a strong diagram), then one from Part 5 (authentication) and one from Part 16 or 17 (AI), chosen after DNS is reviewed. Only DNS is committed to now.
- **Phase 2 — Rollout.** Part by part, one batch per part, in handbook order. Each part also gets a short part-intro video. Style changes after the pilots are applied to the kit, and affected videos are re-rendered.

## 3. Video structure (every video)

Beats map onto chapter sections. Target about 150 spoken words per minute, so a 7-minute video is about 1,050 words.

| Time | Beat | Chapter source |
|---|---|---|
| 0:00–0:30 | Hook and one-line promise | TL;DR "In one line" |
| 0:30–1:30 | Why this matters (a concrete problem) | Why This Matters |
| 1:30–3:00 | Core concept and mental model | Core Concept, Mental Model |
| 3:00–5:00 | How it works, step by step, animated | How It Works, Architecture |
| 5:00–6:30 | Demo (real request/response, terminal or code) | Request/Response Example, Code Example |
| 6:30–7:30 | Common mistakes and production tips | Common Mistakes, Production Considerations |
| 7:30–8:30 | Recap plus 3-question quiz card | Key Takeaways, Check Yourself |
| 8:30–9:00 | Next-video teaser | Part README order |

Simple topics compress beats 3–4; dense topics (HTTP Methods, Status Codes) extend them. The script word count, not the clock, decides length. A script outside 750–1,500 words fails validation.

## 4. Repository layout

```
video/
  specs/                     this document and later specs
  templates/script.md        script template (frontmatter + beats)
  scripts/<NN-slug>/<chapter>.md   one reviewed script per video
  kit/                       Remotion project (React components, theme)
    src/scenes/              Title, Concept, DiagramWalk, Terminal, CodeReveal, Mistakes, Recap, Quiz
    src/theme.ts             palette copied from docs/assets/diagrams visual system
  tools/
    draft_script.py          chapter -> draft script (section-by-section skeleton)
    check_script.py          validates script (section 5)
    render.sh                script -> narration -> Remotion render -> mp4
  out/                       rendered files (gitignored)
```

`video/` is a sibling of `docs/`, so MkDocs and `scripts/check_chapters.py` never see it. Script files contain no relative Markdown links, so `scripts/check_links.py` is unaffected; `check_script.py` resolves chapter references itself.

## 5. Script format and quality gates

Each script is Markdown with frontmatter:

```
---
chapter: docs/01-api-foundations/dns.md
part: 1
index: 5
title: DNS
target_seconds: 420
---
```

Followed by one `## Beat` section per row of section 3. Each beat contains narration paragraphs and `[scene: ...]` cues naming a kit scene and its data (for example `[scene: DiagramWalk svg=01-dns-resolution.svg steps=1-6]`).

`check_script.py` enforces:

1. Frontmatter present and `chapter` file exists.
2. All eight beats present, in order.
3. Total narration words between 750 and 1,500; estimated duration within 5:00–10:00.
4. Every `[scene: ...]` names a scene that exists in the kit and, for diagrams, an SVG that exists.
5. Code and commands shown in a demo beat appear in the chapter or in the matching `examples/` project, so no invented output.
6. No secrets, no placeholder text (`TODO`, `coming soon`).

A human fact-check pass against the chapter is required before a script is marked reviewed. The reviewed flag lives in the frontmatter (`reviewed: true`) and `render.sh` refuses unreviewed scripts.

## 6. Production pipeline

1. `draft_script.py` pulls the TL;DR, headings and code blocks from the chapter into a skeleton script. A model-assisted rewrite turns the skeleton into spoken prose (short sentences, no "as shown above").
2. Human review sets `reviewed: true`.
3. `render.sh`: narration audio is generated per beat through a TTS adapter; Remotion renders scenes with each scene's duration taken from its audio length; captions are burned in from the same script text; `ffmpeg` muxes the final mp4 into `video/out/`.

Narration: a single `tts` adapter selected by `VIDEO_TTS_PROVIDER`, with credentials only from environment variables and never committed. If no provider is configured, `render.sh` produces a captioned silent render plus the narration text, so the maintainer can record the voiceover themselves. Same voice and settings across the whole series.

Visuals: SVG diagrams from `docs/assets/diagrams/` are reused as animated scenes (highlight step N, dim the rest). Where a chapter has only a Mermaid diagram, the kit gets a native scene for it as part of that video's work. Colors follow the handbook palette (green main path, blue client, amber data, red failure, purple AI, slate infra), and text is never under 12px at 1080p.

Output: 1920×1080, 30 fps, H.264 mp4, burned-in captions plus a separate `.srt`.

## 7. Pilot: DNS

- Source: `docs/01-api-foundations/dns.md` (about 1,950 words) and `docs/assets/diagrams/01-dns-resolution.svg`.
- Target length about 7:30.
- Demo beat: a real `dig` resolution trace and a short Python lookup, both taken from or consistent with the chapter's examples.
- Pilot done when: `check_script.py` passes, the video renders end to end, and the maintainer approves style, pacing and voice. Their feedback then updates the kit before Phase 1 continues.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Quality drift across ~190 videos | Pilots first; shared kit; `check_script.py` gates; part-by-part review |
| Technical errors in generated scripts | Facts traced to chapters; demo code checked against chapter or examples; human review flag |
| TTS cost, quota or availability | Adapter plus silent-render fallback; per-part batches |
| Render time and disk use | Rendered files gitignored; render one part at a time |
| Chapters edited after video is made | Script frontmatter records the chapter path; a later check can flag scripts older than their chapter |

## 9. Open items for the implementation plan (not design questions)

- Exact Remotion and Node versions to pin.
- Which TTS providers the adapter ships with first.
- Where finished videos are published and how they are linked from part READMEs. This is a later spec.
