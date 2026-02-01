import os
import re
import subprocess
import sys
from pathlib import Path

TIMESTAMP_RE = re.compile(
    r"^\[(\d{2}:\d{2}:\d{2}\.\d{3})\s*->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\]"
)


def get_editor() -> str:
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vim"


def open_editor(filepath: Path) -> int:
    editor = get_editor()
    result = subprocess.run([editor, str(filepath)])
    return result.returncode


def parse_timestamp(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_edited_file(filepath: Path) -> list[tuple[float, float]]:
    segments = []
    for line in filepath.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = TIMESTAMP_RE.match(line)
        if match:
            start = parse_timestamp(match.group(1))
            end = parse_timestamp(match.group(2))
            if segments and start <= segments[-1][1]:
                # Merge overlapping/adjacent segments
                segments[-1] = (segments[-1][0], max(segments[-1][1], end))
            else:
                segments.append((start, end))
    return segments
