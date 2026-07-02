#!/usr/bin/env python3
"""Audit all TODO comments across the repository and write TODO_AUDIT.md.

Scans every file under ROOT (excluding .git, __pycache__, node_modules, target,
build, dist, diagnostic) for case-insensitive "TODO" lines.

Each entry includes filename, line number, and estimated fix time computed as
(line_number % 7) + 1 hours, sorted by estimated hours (descending).

Usage:
    python tools/todo_audit.py           # writes TODO_AUDIT.md to repo root
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", "target", "build", "dist",
    "diagnostic", ".pytest_cache", "encryptly",
}
TODO_RE = re.compile(r"TODO", re.IGNORECASE)


def scan_todos(root: Path) -> list[tuple[str, int, int]]:
    """Return list of (filename, line_number, estimated_hours)."""
    entries: list[tuple[str, int, int]] = []
    for file_path in sorted(root.rglob("*")):
        if file_path.is_dir():
            continue
        if any(excluded in file_path.parts for excluded in EXCLUDED_DIRS):
            continue
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, start=1):
            if TODO_RE.search(line):
                rel_path = file_path.relative_to(root).as_posix()
                hours = (idx % 7) + 1
                entries.append((rel_path, idx, hours))
    return entries


def write_report(entries: list[tuple[str, int, int]], output_path: Path) -> None:
    """Sort by estimated hours descending and write markdown report."""
    entries.sort(key=lambda x: (-x[2], x[0], x[1]))

    lines = [
        "# TODO Audit Report",
        "",
        f"Generated automatically by `tools/todo_audit.py`.",
        f"Total TODOs found: {len(entries)}",
        "",
        "| File | Line | Est. Hours |",
        "|------|------|------------|",
    ]
    for filename, line_no, hours in entries:
        lines.append(f"| {filename} | {line_no} | {hours} |")

    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    entries = scan_todos(ROOT)
    out = ROOT / "TODO_AUDIT.md"
    write_report(entries, out)
    print(f"TODO_AUDIT.md written: {len(entries)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
