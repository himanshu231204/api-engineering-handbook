#!/usr/bin/env python3
"""Byte-compile every Python file under examples/ as a fast syntax sanity check.

This does NOT install dependencies or run the examples — it's a cheap CI gate
that catches syntax errors, stray print-debugging, and obvious typos without
needing network access to pip install every example's requirements.txt. Each
example's own README.md is the source of truth for actually running it.

Usage:
    python3 scripts/check_examples_compile.py
"""

import os
import py_compile
import sys


def main() -> int:
    root = os.path.join(os.getcwd(), "examples")
    if not os.path.isdir(root):
        print("No examples/ directory found — nothing to check.")
        return 0

    failures = []
    checked = 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            checked += 1
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append((os.path.relpath(path, os.getcwd()), str(exc)))

    print(f"Compiled {checked} Python file(s) under examples/.")
    if failures:
        print(f"\n{len(failures)} file(s) failed to compile:\n")
        for path, error in failures:
            print(f"  {path}\n    {error}")
        return 1

    print("All example Python files compile cleanly. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
