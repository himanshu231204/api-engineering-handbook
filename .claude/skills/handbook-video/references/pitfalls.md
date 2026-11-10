# Pitfalls hit while building "What Is an API?"

1. **Whisper wants 16 kHz.** Kokoro writes 24 kHz. Feeding it to faster-whisper unresampled stretches every word time 1.5x (elements appear late) and makes the ASR mishear ("four" -> "fear"). Always `ffmpeg -ar 16000 -ac 1` first, then check no word falls outside its line window.
2. **TTS respellings**: `API` -> `A P I`, `MDN` -> `M D N`, `PostgreSQL` -> `Post gress Q L`, `MongoDB` -> `Mongo D B`, `404` -> `four zero four`. Captions use the clean text (`cap`), the SRT is cleaned in `post.py`.
3. **Chapter gap 2.0 s** between chapters so the chapter card is on screen >= 1.5 s (check's `line_unread` warning).
4. **Render must stay a child of the tool call.** `nohup npx hyperframes render ... &` is killed with the shell (`render_cancelled_parent_exited`). Use `run_in_background` on the render command itself with `HYPERFRAMES_RENDER_DETACHED=1`.
5. **Repo SVGs**: class names must not start with a digit (prefix `r<stem>-`); text with no explicit fill defaults to black (set `fill="#FFFFFF"` on the root); several inlined SVGs share class names like `.note`, `.title` - prefix them or they restyle your scenes.
6. **Mermaid SVG**: its `<style>` is scoped by id and contains `&gt;`; inlined in a scene the CSS is ignored (grey boxes, invisible arrows) and the linter reports `css_parse_error`. `mermaid_to_svg.py` decodes the entities and bakes computed styles inline (`bake_svg_styles.js`), then it renders correctly. Unique root id per diagram.
7. **GSAP**: use `fromTo`; every exit tween needs `immediateRender:false`; never put a CSS `transform` on an animated element; lint's `overlapping_gsap_tweens` / `gsap_repeated_fromto_without_baseline` warnings on the helper functions are false positives (the helper branches are mutually exclusive).
8. **Layout check** flags text overlapping boxes: titles inside flex boxes sit at the centre - put separate labels on top-aligned boxes; chips that fade out must finish before the next element fades in (compute `out` from the previous line's end).
9. **HUD collision**: chips at the top-left collide with the HUD chapter title; start them at x >= 460.
10. **Black background check**: top corner patches contain the yellow progress bar by design; judge the bottom corners and side strips.
11. **`check_links.py`** scans every `.md` under the repo, including local venvs; ignore hits under untracked `tts/` and `fa/`.
12. Faster-whisper `base.en` is enough for alignment; do not trust it for pronunciation checks of unusual words - listen-proof with `small.en` if a respelling is in doubt.
