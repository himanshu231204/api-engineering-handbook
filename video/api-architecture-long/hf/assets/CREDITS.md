# Asset credits — "API Architecture at a Glance" (long)

| File / item | What it shows | Source | License / status | Captured |
|---|---|---|---|---|
| `repo/mermaid/api-architecture-layers-td.svg`, `api-architecture-layers-lr.svg` | The chapter's two Mermaid flowcharts, rendered by `video/tools/mermaid_to_svg.py` (mermaid-cli) | `docs/00-introduction/api-architecture.md` in this repo | MIT (this repository); Mermaid is MIT | 2026-11-10 |
| `repo/mermaid/api-request-flow.svg` | The Mermaid sequence diagram of one request, compact layout (`--extra-config mermaid-sequence-compact.json`) | `diagrams/api-request-flow.md` in this repo | MIT (this repository) | 2026-11-10 |
| `repo/svg/11-api-gateway.svg`, `07-cache-aside.svg`, `08-message-queue.svg`, `15-llm-gateway.svg`, `18-request-flow.svg` | The handbook's concept diagrams, converted to a dark neon palette by `video/tools/repo_svg_to_dark.py` | `docs/assets/diagrams/` in this repo | MIT (this repository) | 2026-11-10 |
| On-screen request trace (7 steps) | The chapter's "send a chat message" example, verbatim | `docs/00-introduction/api-architecture.md` | MIT (this repository) | 2026-11-10 |
| Code excerpt and terminal output | `examples/llm-gateway/main.py` lines and a real run (`demo/real_output.txt`, `demo/run_demo.sh`); long commands trimmed with `…` | Run locally with FastAPI + uvicorn | MIT (this repository) / original recording | 2026-11-10 |
| Quiz question and answer | Check Yourself question 3 | `docs/00-introduction/api-architecture.md` | MIT (this repository) | 2026-11-10 |
| `</>` emblem, boxes, arrows, chips | Diagrams and logo mark | Original SVG/HTML, made for this video | Original | — |
| Voice | AI narration, Kokoro `am_michael` (not a human voice, not a clone) | https://github.com/thewh1teagle/kokoro-onnx (model files v1.0) | Apache-2.0 | 2026-11-10 |
| Sound effects | Whoosh, thunk, pop, tick, shutter | Synthesized in numpy (`build/mix.py`) | Original | — |
| `fonts/caveat-700.woff2` | Handwritten notes | `@fontsource/caveat` 5.3.0 | SIL OFL 1.1 | 2026-11-10 |
| Inter, JetBrains Mono | Text and code | Bundled with HyperFrames | SIL OFL 1.1 | — |
| `vendor/gsap.min.js` | Animation runtime, GSAP 3.15.0 | https://gsap.com | GreenSock standard license (free) | 2026-11-10 |
| `thumbnail.png` | Thumbnail | `thumb/index.html` (original) | Original | 2026-11-10 |
| No music, no third-party screenshots, no photos of people | — | — | — | — |
