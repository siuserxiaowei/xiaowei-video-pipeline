#!/usr/bin/env python3
"""Validate the portable edit-plan contract used by the video pipeline."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


MODES = {"conservative", "balanced", "aggressive"}
ACTIONS = {"keep", "cut"}


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate(plan: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if plan.get("schema") != 1:
        errors.append("schema must be 1")
    if plan.get("mode") not in MODES:
        errors.append("mode must be conservative, balanced, or aggressive")

    source = plan.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
        source = {}
    duration = source.get("durationSeconds")
    if duration is not None and (not _number(duration) or duration <= 0):
        errors.append("source.durationSeconds must be a positive number")
        duration = None

    segments = plan.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty array")
        segments = []

    previous_end = 0.0
    keep_count = 0
    for index, segment in enumerate(segments):
        prefix = f"segments[{index}]"
        if not isinstance(segment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        action = segment.get("action")
        if action not in ACTIONS:
            errors.append(f"{prefix}.action must be keep or cut")
        elif action == "keep":
            keep_count += 1
        start = segment.get("startSeconds")
        end = segment.get("endSeconds")
        if not _number(start) or not _number(end):
            errors.append(f"{prefix} needs numeric startSeconds/endSeconds")
            continue
        confidence = segment.get("confidence")
        if not _number(confidence) or not 0 <= confidence <= 1:
            errors.append(f"{prefix}.confidence must be a number between 0 and 1")
        if start < 0 or end <= start:
            errors.append(f"{prefix} must satisfy 0 <= startSeconds < endSeconds")
        if start < previous_end:
            errors.append(f"{prefix} overlaps or is out of order")
        previous_end = max(previous_end, end)
        if duration is not None and end > duration + 0.05:
            errors.append(f"{prefix} ends after source duration")
        reason_codes = segment.get("reasonCodes", [])
        if not isinstance(reason_codes, list) or not all(isinstance(item, str) and item for item in reason_codes):
            errors.append(f"{prefix}.reasonCodes must be an array of non-empty strings")
        evidence = segment.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{prefix}.evidence must be an array")
        elif not evidence:
            warnings.append(f"{prefix} has no evidence references")

    if keep_count == 0:
        errors.append("segments must contain at least one keep segment")
    if not plan.get("qa"):
        warnings.append("qa is missing; add predicted risks and required manual checks")

    return {"valid": not errors, "errors": errors, "warnings": warnings, "keepSegments": keep_count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", help="Path to edit-plan.json")
    args = parser.parse_args()
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [f"cannot read plan: {exc}"], "warnings": []}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(plan, dict):
        result = {"valid": False, "errors": ["plan root must be an object"], "warnings": []}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    result = validate(plan)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
