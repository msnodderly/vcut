# vcut

Text-based video editor — edit video by editing a transcript. This is a sort of trivial, mostly vibe-coded project. I made it for clipping out just the interesting sections of podcasts, long screen shares, etc. -Matt

## Overview

`vcut` turns video editing into text editing. Transcribe a video, edit the transcript in your favorite text editor, and render the result.

```bash
vcut transcribe video.mp4       # Step 1: Generate video.txt
vim video.txt                       # Step 2: Edit the transcript
vcut render video.mp4           # Step 3: Render video_edited.mp4
```

Delete or comment lines with `#` to cut content. 

## Installation

### Prerequisites

- **FFmpeg** on your `$PATH`:
  ```bash
  brew install ffmpeg        # macOS
  sudo apt install ffmpeg    # Ubuntu/Debian
  ```
- **Python 3.10+**

### Install

```bash
pip install -e .
```

### Whisper Models

The `faster-whisper` package installs via pip automatically. On first run, the selected Whisper model downloads (~150MB-1.5GB) and caches to `~/.cache/huggingface/`.

## Usage

### `vcut transcribe` — Generate transcript

```bash
vcut transcribe video.mp4                # → video.txt
vcut transcribe video.mp4 -o out.txt     # custom output path
vcut transcribe video.mp4 --model large-v3 --language en
vcut transcribe video.mp4 --force        # overwrite existing
```

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output` | `-o` | `{input}.txt` | Output transcript path |
| `--model` | `-m` | `distil-large-v3` | Whisper model |
| `--language` | `-l` | auto-detect | Force language |
| `--force` | | `false` | Overwrite existing transcript |

### `vcut render` — Render from edited transcript

```bash
vcut render video.mp4                     # reads video.txt → video_edited.mp4
vcut render video.mp4 -o final.mp4        # custom output
vcut render video.mp4 -t edited.txt       # custom transcript
vcut render video.mp4 --reencode          # frame-perfect cuts
```

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--transcript` | `-t` | `{input}.txt` | Transcript file |
| `--output` | `-o` | `{input}_edited.mp4` | Output video path |
| `--reencode` | `-r` | `false` | Re-encode for precise cuts |

### `vcut edit` — Convenience: edit + render

Opens the transcript in `$EDITOR` then renders on save. Requires a transcript to already exist.

```bash
vcut edit video.mp4
vcut edit video.mp4 --reencode
```

## Transcript Format

Each line is a segment with timestamps:

```
[00:00:00.000 -> 00:00:03.200] | Welcome to this tutorial.
[00:00:03.200 -> 00:00:06.500] | First, we'll discuss the basics.
[00:00:06.500 -> 00:00:09.800] | This part is boring filler content.
[00:00:09.800 -> 00:00:12.100] | Now for the interesting stuff.
```

Edit it:

```
[00:00:00.000 -> 00:00:03.200] | Welcome to this tutorial.
# [00:00:03.200 -> 00:00:06.500] | First, we'll discuss the basics.
[00:00:09.800 -> 00:00:12.100] | Now for the interesting stuff.
```

- Commented line (`#`) or deleted lines are removed from the output

## Stream Copy vs Re-encode

**Stream copy** (default): Fast. Cuts at keyframes, so there may be slight imprecision at segment boundaries.

**Re-encode** (`--reencode`): Slower. Frame-perfect cuts. Use for final output.

## Typical Workflow

```bash
# Transcribe once
vcut transcribe interview.mp4

# Edit as many times as you want
vim interview.txt
vcut render interview.mp4 -o take1.mp4

vim interview.txt
vcut render interview.mp4 -o take2.mp4

# Final render with precise cuts
vcut render interview.mp4 -o final.mp4 --reencode
```

## Advanced: Supercuts (videogrep-style)

Create a supercut of every time someone says a specific word or phrase:

```bash
# 1. Transcribe with small chunks for fine-grained control
vcut transcribe video.mp4 -c 2

# 2. Use grep to find matching segments
grep -i "amazing" video.txt > supercut.txt

# 3. Render just those clips
vcut render video.mp4 -t supercut.txt -o amazing-supercut.mp4
```

Or use sed/awk for pattern-based editing:

```bash
# Keep only lines containing "data" or "analysis"
grep -E "(data|analysis)" video.txt > technical-terms.txt
vcut render video.mp4 -t technical-terms.txt -o technical-supercut.mp4

# Remove all lines with filler words (only works if they're included in the transcript)
sed '/\b(um|uh|like|you know)\b/d' video.txt > clean.txt
vcut render video.mp4 -t clean.txt -o clean-version.mp4
```

## Troubleshooting

**ffmpeg not found** — Install it: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Ubuntu).

**Model download is slow** — First run downloads the Whisper model (~1.5GB). Set `HF_TOKEN` for faster downloads.

**Transcript already exists** — Use `--force` to overwrite, or just edit the existing file.

**Transcript not found (render/edit)** — Run `vcut transcribe` first.

## License

MIT
