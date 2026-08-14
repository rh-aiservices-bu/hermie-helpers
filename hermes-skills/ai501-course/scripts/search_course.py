#!/usr/bin/env python3
"""Search the local AI501 content mirror with ripgrep or a Python fallback."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

DEFAULT_ROOT = "/app/.hermes/ai501-content"


def rg_search(query: str, roots: list[Path], limit: int) -> list[dict]:
    command = ["rg", "-n", "-i", "-F", "--glob", "*.md", query, *map(str, roots)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    matches = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3:
            matches.append({"path": parts[0], "line": int(parts[1]), "text": parts[2].strip()})
        if len(matches) >= limit:
            break
    return matches


def python_search(query: str, roots: list[Path], limit: int) -> list[dict]:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = []
    for root in roots:
        for path in sorted(root.rglob("*.md")):
            try:
                for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                    if pattern.search(line):
                        matches.append({"path": str(path), "line": number, "text": line.strip()})
                        if len(matches) >= limit:
                            return matches
            except OSError:
                continue
    return matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--module", default="", help="Limit lab instructions to a module id")
    parser.add_argument("--repository", action="append", default=[], help="Repository name; repeatable")
    parser.add_argument("--content-root", default="")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    content_root = Path(args.content_root or os.getenv("AI501_CONTENT_DIR") or DEFAULT_ROOT)
    repositories = args.repository or ["lab-instructions"]
    roots = []
    for repository in repositories:
        root = content_root / repository
        if repository == "lab-instructions" and args.module:
            root = root / "docs" / args.module
        if root.exists():
            roots.append(root)
    if not roots:
        print(json.dumps({"matches": [], "error": "AI501 content mirror is unavailable"}))
        return 2

    limit = max(1, min(args.limit, 100))
    matches = rg_search(args.query, roots, limit) if shutil.which("rg") else python_search(args.query, roots, limit)
    print(json.dumps({"query": args.query, "matches": matches}, indent=2, ensure_ascii=False))
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())

