#!/usr/bin/env python3
"""Verify every Python file has a module-level docstring."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", "node_modules", "target", "encryptly", "diagnostic"}


def missing_docstrings(root: Path) -> list[str]:
    bad: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        if not ast.get_docstring(tree):
            bad.append(path.relative_to(root).as_posix())
    return bad


def main() -> int:
    missing = missing_docstrings(ROOT)
    if missing:
        print("Missing module docstrings:", file=sys.stderr)
        for rel in missing:
            print(f"  {rel}", file=sys.stderr)
        return 1
    print(f"All Python modules under {ROOT.name} have docstrings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
