import os
import re
import subprocess
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


def parse_timestamp(ts: str, line_context: str = "") -> float:
    """Parse HH:MM:SS.mmm timestamp to seconds.

    Raises ValueError if the timestamp is invalid.
    """
    h, m, rest = ts.split(":")
    s, ms = rest.split(".")

    hours = int(h)
    minutes = int(m)
    seconds = int(s)
    milliseconds = int(ms)

    # Validate timestamp components
    if minutes >= 60:
        raise ValueError(f"Invalid timestamp '{ts}': minutes must be < 60 (got {minutes}){line_context}")
    if seconds >= 60:
        raise ValueError(f"Invalid timestamp '{ts}': seconds must be < 60 (got {seconds}){line_context}")
    if milliseconds >= 1000:
        raise ValueError(f"Invalid timestamp '{ts}': milliseconds must be < 1000 (got {milliseconds}){line_context}")

    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def parse_edited_file(filepath: Path) -> list[tuple[float, float]]:
    segments = []
    for line_num, line in enumerate(filepath.read_text().splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = TIMESTAMP_RE.match(line)
        if match:
            line_context = f" (line {line_num})"
            try:
                start = parse_timestamp(match.group(1), line_context)
                end = parse_timestamp(match.group(2), line_context)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp in {filepath.name}{line_context}: {e}") from e

            # Validate that start comes before end
            if start >= end:
                raise ValueError(
                    f"Invalid segment in {filepath.name}{line_context}: "
                    f"start time ({match.group(1)}) must be before end time ({match.group(2)})"
                )

            if segments and start < segments[-1][1]:
                prev_end = segments[-1][1]
                if start < segments[-1][0]:
                    raise ValueError(
                        f"Out-of-order segment in {filepath.name}{line_context}: "
                        f"segment starts at {match.group(1)} which is before the previous segment. "
                        f"Reordering segments is not supported."
                    )
                # Merge overlapping/adjacent segments to prevent jitter
                segments[-1] = (segments[-1][0], max(prev_end, end))
            else:
                segments.append((start, end))
    return segments
