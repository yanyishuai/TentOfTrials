#!/usr/bin/env python3
"""Audit that files referencing "legacy" also contain an uppercase LEGACY marker.

Scans all repository files (excluding .git, build artifacts, etc.) for
case-insensitive mentions of "legacy", and verifies each file also contains
an uppercase "LEGACY" comment marker.  Files that reference legacy concepts
without a LEGACY marker are flagged as violations.

Returns exit code 0 when all files pass.

Usage:
    python tools/legacy_caps_audit.py        # audit only (exit code 0 = pass)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", "target", "build", "dist",
    "diagnostic", ".pytest_cache", "encryptly", "TODO_AUDIT.md",
    "tsconfig.tsbuildinfo",
}


def is_legacy_reference(line: str) -> bool:
    """True if the line contains a lower/mixed-case legacy reference
    that is NOT already an uppercase LEGACY marker."""
    stripped = line.strip()
    # A proper LEGACY comment line — counts as the marker, not a violation
    if "LEGACY" in stripped:
        return False
    return "legacy" in stripped.lower()


def has_legacy_marker(content: str) -> bool:
    """True if the file contains at least one uppercase LEGACY line."""
    for line in content.splitlines():
        if "LEGACY" in line:
            return True
    return False


def audit() -> tuple[list[str], list[str]]:
    """Return (violations, skipped) file paths."""
    violations: list[str] = []
    skipped: list[str] = []

    for file_path in sorted(ROOT.rglob("*")):
        if file_path.is_dir():
            continue
        if any(excluded in file_path.parts for excluded in EXCLUDED_DIRS):
            continue
        rel = file_path.relative_to(ROOT).as_posix()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            skipped.append(rel)
            continue

        # Check if file has any legacy reference
        has_ref = any(is_legacy_reference(line) for line in content.splitlines())
        if not has_ref:
            continue

        # It references legacy, so it must have a LEGACY marker
        if not has_legacy_marker(content):
            violations.append(rel)

    return violations, skipped


def main() -> int:
    violations, skipped = audit()
    if skipped:
        print(f"Skipped {len(skipped)} binary/unreadable files", file=sys.stderr)
    if violations:
        print(f"LEGACY caps violations ({len(violations)}):", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1
    print("All files with legacy references include LEGACY marker.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
