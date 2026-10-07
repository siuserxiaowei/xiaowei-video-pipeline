#!/usr/bin/env python3
"""Create a portable, machine-readable media capability snapshot.

The doctor only inspects local binaries and filesystem capacity.  It never
downloads media, reads credentials, or overwrites a user file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(argv: list[str], timeout: float = 8.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"status": "missing", "command": argv}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": argv}
    except OSError as exc:
        return {"status": "error", "command": argv, "error": str(exc)}

    output = proc.stdout or ""
    return {
        "status": "available" if proc.returncode == 0 else "error",
        "returncode": proc.returncode,
        "command": argv,
        "output": output,
    }


def _binary(name: str, version_args: list[str] | None = None) -> dict[str, Any]:
    path = shutil.which(name)
    result: dict[str, Any] = {"status": "available" if path else "missing", "path": path}
    if not path:
        return result
    if version_args:
        probe = _run([path, *version_args])
        first_line = (probe.get("output") or "").splitlines()[0:1]
        if first_line:
            result["version"] = first_line[0].strip()
    return result


def _names_from_listing(output: str, kind: str) -> set[str]:
    names: set[str] = set()
    for line in output.splitlines():
        # Filter listings use three flags; encoder listings use six. Ignore
        # headings and comments in both formats.
        flags = r"[A-Z\.]{2,6}" if kind == "filters" else r"[A-Z\.]{6}"
        match = re.match(rf"^\s*{flags}\s+([A-Za-z0-9_-]+)", line)
        if match:
            names.add(match.group(1))
    return names


def _ffmpeg_capabilities(ffmpeg: str | None) -> dict[str, Any]:
    if not ffmpeg:
        return {"status": "missing"}

    filters = _run([ffmpeg, "-hide_banner", "-filters"])
    encoders = _run([ffmpeg, "-hide_banner", "-encoders"])
    filter_names = _names_from_listing(filters.get("output", ""), "filters")
    encoder_names = _names_from_listing(encoders.get("output", ""), "encoders")

    important_filters = ["drawtext", "subtitles", "ass", "loudnorm", "silencedetect", "select"]
    important_encoders = [
        "libx264",
        "libx265",
        "h264_videotoolbox",
        "h264_nvenc",
        "h264_qsv",
        "h264_vaapi",
        "libvpx-vp9",
    ]
    return {
        "status": "available" if filters["status"] == "available" else filters["status"],
        "filters": {name: name in filter_names for name in important_filters},
        "encoders": {name: name in encoder_names for name in important_encoders},
        "encoderSelectionRule": "Use only a listed encoder; smoke-test it before a long render; fall back to libx264.",
    }


def _storage(path: Path) -> dict[str, Any]:
    try:
        usage = shutil.disk_usage(path)
        return {"path": str(path), "freeBytes": usage.free, "totalBytes": usage.total}
    except OSError as exc:
        return {"path": str(path), "status": "error", "error": str(exc)}


def build_snapshot(root: Path) -> dict[str, Any]:
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    binaries = {
        "ffmpeg": _binary("ffmpeg", ["-version"]),
        "ffprobe": _binary("ffprobe", ["-version"]),
        "yt-dlp": _binary("yt-dlp", ["--version"]),
        "whisper": _binary("whisper", ["--help"]),
        "whisper.cpp": _binary("whisper-cli", ["--help"]),
        "python": _binary(Path(sys.executable).name, ["--version"]),
        "node": _binary("node", ["--version"]),
    }
    return {
        "schema": 1,
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "root": str(root.resolve()),
        "binaries": binaries,
        "ffmpeg": _ffmpeg_capabilities(ffmpeg_path),
        "storage": _storage(root),
        "notes": [
            "A listed hardware encoder is not proof that a render will work; use a short smoke test.",
            "Missing drawtext/subtitles/ass filters require a different FFmpeg build or an overlay fallback.",
            "This report records capability evidence; it does not silently install dependencies.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Directory whose filesystem should be measured")
    parser.add_argument("--output", help="Write JSON to this path instead of stdout")
    args = parser.parse_args()

    snapshot = build_snapshot(Path(args.root))
    rendered = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
