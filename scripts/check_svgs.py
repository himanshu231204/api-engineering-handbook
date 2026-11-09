#!/usr/bin/env python3
"""Check every SVG diagram under docs/assets/ is well-formed XML with a <title>.

Browsers forgive malformed SVG when it's inlined in HTML, but render a broken
image when it's loaded via <img> (how Markdown embeds it). An unescaped "&" is
the classic cause. Stdlib only; used by CI.

Usage:
    python3 scripts/check_svgs.py
"""

import sys
import xml.dom.minidom
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"


def main() -> int:
    svgs = sorted(Path("docs/assets").rglob("*.svg"))
    problems = []
    for svg in svgs:
        try:
            doc = xml.dom.minidom.parse(str(svg))
        except Exception as exc:  # expat raises ExpatError; report any parse failure
            problems.append(f"{svg}: not well-formed XML ({exc})")
            continue
        root = doc.documentElement
        if root.tagName != "svg" or root.getAttribute("xmlns") != SVG_NS:
            problems.append(f"{svg}: root must be <svg xmlns=\"{SVG_NS}\">")
        if svg.parent.name == "diagrams" and not root.getElementsByTagName("title"):
            problems.append(f"{svg}: diagram has no <title> (needed for accessibility)")
    print(f"Checked {len(svgs)} SVG files.")
    if problems:
        print("\n".join(problems))
        return 1
    print("All SVGs are well-formed. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
