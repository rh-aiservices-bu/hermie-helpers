#!/usr/bin/env python3
"""Resolve AI501 module/exercise hints to authoritative content paths."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parents[1]
MAP_PATH = SKILL_DIR / "references" / "course-map.yaml"


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def load_map() -> dict:
    with MAP_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def score(needle: str, identifier: str, label: str) -> int:
    wanted = normalize(needle)
    if not wanted:
        return 0
    values = {normalize(identifier), normalize(label)}
    if wanted in values:
        return 100
    if any(wanted in value or value in wanted for value in values):
        return 70
    tokens = set(wanted.split())
    return max((len(tokens & set(value.split())) * 10 for value in values), default=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default="", help="Module id or label")
    parser.add_argument("--exercise", default="", help="Exercise id or label")
    parser.add_argument("--query", default="", help="Free-text hint when ids are absent")
    parser.add_argument("--content-root", default="")
    args = parser.parse_args()

    course = load_map()
    root = Path(
        args.content_root
        or os.getenv(course["content_root_env"])
        or course["default_content_root"]
    )
    hint = args.module or args.query
    ranked_modules = sorted(
        ((score(hint, item["id"], item["label"]), item) for item in course["modules"]),
        key=lambda pair: pair[0],
        reverse=True,
    )
    module_score, module = ranked_modules[0]
    inferred_exercise = None
    inferred_exercise_score = 0
    if not args.module and (args.exercise or args.query):
        exercise_hint = args.exercise or args.query
        candidates = sorted(
            (
                (score(exercise_hint, exercise[0], exercise[1]), candidate_module, exercise)
                for candidate_module in course["modules"]
                for exercise in candidate_module.get("exercises", [])
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        inferred_exercise_score, inferred_module, inferred_exercise = candidates[0]
        if inferred_exercise_score > module_score:
            module_score, module = inferred_exercise_score, inferred_module
    if module_score == 0:
        print(json.dumps({"resolved": False, "reason": "No matching module"}))
        return 2

    if inferred_exercise is not None and inferred_exercise in module.get("exercises", []):
        exercise_score, exercise = inferred_exercise_score, inferred_exercise
    else:
        exercise_hint = args.exercise or args.query
        ranked_exercises = sorted(
            (
                (score(exercise_hint, exercise[0], exercise[1]), exercise)
                for exercise in module.get("exercises", [])
            ),
            key=lambda pair: pair[0],
            reverse=True,
        )
        exercise_score, exercise = ranked_exercises[0] if ranked_exercises else (0, None)
    module_dir = root / course["primary_repository"] / "docs" / module["id"]
    result = {
        "resolved": True,
        "module": {"id": module["id"], "label": module["label"]},
        "module_readme": str(module_dir / "README.md"),
        "module_reference": str(SKILL_DIR / "references" / module["reference"]),
    }
    if exercise and exercise_score:
        result["exercise"] = {"id": exercise[0], "label": exercise[1]}
        result["exercise_file"] = str(module_dir / f"{exercise[0]}.md")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
