"""Validate video scripts against the series spec (video/specs/...-design.md, section 5)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from script_model import BEAT_NAMES, estimated_seconds, narration_words, parse_script  # noqa: E402

REQUIRED_META = ["chapter", "part", "index", "title", "target_seconds"]
MIN_WORDS, MAX_WORDS = 750, 1500
_PLACEHOLDER = re.compile(r"\bTODO\b|coming soon|lorem ipsum", re.IGNORECASE)
_SECRET = re.compile(r"sk-[A-Za-z0-9]{20,}|Bearer\s+\S{20,}")
_STEPS = re.compile(r"^(\d+)(?:-(\d+))?$")


def _read_texts(directory: Path) -> str:
    chunks = []
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            try:
                chunks.append(p.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, OSError):
                pass
    return "\n".join(chunks)


def check_script(path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []

    def err(msg: str, line: int | None = None) -> None:
        errors.append(f"{path}:{line}: {msg}" if line else f"{path}: {msg}")

    text = path.read_text(encoding="utf-8")
    try:
        script = parse_script(text)
    except ValueError as exc:
        return [f"{path}: {exc}"]

    for key in REQUIRED_META:
        if key not in script.meta:
            err(f"frontmatter missing '{key}'")
    chapter_rel = script.meta.get("chapter")
    chapter_text = ""
    if chapter_rel:
        chapter_file = repo_root / chapter_rel
        if chapter_file.is_file():
            chapter_text = chapter_file.read_text(encoding="utf-8")
        else:
            err(f"chapter file '{chapter_rel}' does not exist")

    names = [b.name for b in script.beats]
    if names != BEAT_NAMES:
        for n in names:
            if n not in BEAT_NAMES:
                err(f"unknown beat heading '{n}' (expected one of {BEAT_NAMES})")
        for n in sorted({n for n in names if names.count(n) > 1}):
            err(f"duplicate beat '{n}'")
        for n in BEAT_NAMES:
            if n not in names:
                err(f"missing beat '{n}'")
        if sorted(names) == sorted(BEAT_NAMES):
            err(f"beats out of order: {names}")
    for beat in script.beats:
        if not beat.narration.strip():
            err(f"beat '{beat.name}' has empty narration", beat.line)

    words = narration_words(script)
    if not MIN_WORDS <= words <= MAX_WORDS:
        err(f"narration has {words} words; must be between {MIN_WORDS} and {MAX_WORDS}")
    seconds = estimated_seconds(script)
    if not 300 <= seconds <= 600:
        err(f"estimated length {seconds:.0f}s is outside 300-600s")

    kit = repo_root / "video" / "kit"
    scene_names = set(json.loads((kit / "scene_names.json").read_text(encoding="utf-8")))
    diagrams = repo_root / "docs" / "assets" / "diagrams"
    for beat in script.beats:
        for cue in beat.cues:
            if cue.scene not in scene_names:
                err(f"unknown scene '{cue.scene}'", cue.line)
                continue
            if cue.scene != "DiagramWalk":
                continue
            svg = cue.args.get("svg")
            steps = cue.args.get("steps")
            if not svg or not steps:
                err("DiagramWalk needs svg= and steps=", cue.line)
                continue
            if not (diagrams / svg).is_file():
                err(f"svg '{svg}' not found in docs/assets/diagrams", cue.line)
                continue
            match = _STEPS.match(steps)
            if not match:
                err(f"steps '{steps}' must look like 3 or 1-6", cue.line)
                continue
            hi = int(match.group(2) or match.group(1))
            sidecar = kit / "diagram_steps" / f"{Path(svg).stem}.json"
            if not sidecar.is_file():
                err(f"no step sidecar for '{svg}' at video/kit/diagram_steps", cue.line)
                continue
            count = len(json.loads(sidecar.read_text(encoding="utf-8"))["steps"])
            if hi > count or int(match.group(1)) < 1:
                err(f"steps {steps} exceed the {count} steps defined for '{svg}'", cue.line)

    corpus = chapter_text + "\n" + _read_texts(repo_root / "examples")
    for beat in script.beats:
        if beat.name != "Demo":
            continue
        for block in beat.code_blocks:
            for raw in block.split("\n"):
                code = raw.strip()
                if code and code not in corpus:
                    err(f"demo line not found in chapter or examples: '{code}'", beat.line)

    for match in _PLACEHOLDER.finditer(text):
        err(f"placeholder text '{match.group(0)}'")
    if _SECRET.search(text):
        err("secret-like string found")
    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: check_script.py <script.md>...", file=sys.stderr)
        return 2
    repo_root = Path(__file__).resolve().parents[2]
    failed = False
    for arg in argv:
        for message in check_script(Path(arg), repo_root):
            print(message)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
