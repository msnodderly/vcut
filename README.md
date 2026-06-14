# vcut

`vcut` is a text-based video editor: Edit video by editing a transcript. This is a sort of trivial, mostly vibe-coded project. It is essentially a thin wrapper around ffmpeg and fastet-whisper. I made yhis for clipping out just the interesting sections of podcasts, long screen shares, etc. -Matt

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
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -e .
```

### Whisper Models

The `faster-whisper` package installs via pip automatically. On first run, the selected Whisper model downloads (~150MB-1.5GB) and caches to `~/.cache/huggingface/`.

## Usage

### Agent workflow: choose the right transcript edit

`vcut --help` is intended to be useful as an ad-hoc agent instruction document.
When an agent is asked to use `vcut`, start there and then choose the edit
pattern that matches the user's request.

```bash
# 1. Read the tool instructions.
vcut --help

# 2. Transcribe to a scratch file with short chunks for searchable boundaries.
vcut transcribe "input.mp4" -o /tmp/input.vcut.txt -m balanced -l en -c 2 --force

# 3. Search for the requested phrase, likely transcript variants, and nearby terms.
rg -n -i 'requested phrase|alternate spelling|related term' /tmp/input.vcut.txt
sed -n 'START,ENDp' /tmp/input.vcut.txt
```

For a contiguous snippet, such as "the section where they discuss X", create one
synthetic transcript line spanning the selected start/end time. Do not render
every transcript line separately unless the user wants jump cuts.

```bash
printf '%s\n' '[00:32:18.400 -> 00:37:42.840] | requested section' > /tmp/clip.vcut.txt
vcut render "input.mp4" -t /tmp/clip.vcut.txt -o "requested-section.mp4" --reencode --force
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "requested-section.mp4"
```

For a supercut, such as "every time they say X", keep multiple matching
transcript lines and render those lines as separate clips.

```bash
rg -i 'amazing|incredible' /tmp/input.vcut.txt > /tmp/supercut.vcut.txt
vcut render "input.mp4" -t /tmp/supercut.vcut.txt -o "supercut.mp4" --reencode --force
```

For cleanup/removal edits, copy the full transcript, delete or `#` comment the
lines to remove, then render the edited transcript. This preserves everything
else.

```bash
cp /tmp/input.vcut.txt /tmp/clean.vcut.txt
# edit /tmp/clean.vcut.txt, or generate it with rg/sed/awk
vcut render "input.mp4" -t /tmp/clean.vcut.txt -o "clean.mp4" --reencode --force
```

Notes for agents:

- Use `/tmp` for scratch transcripts.
- Write the final output somewhere writable; if the source video is outside the
  workspace, do not assume its directory is writable.
- If the exact requested phrase is not found, search plausible transcription
  variants and tell the user what term was actually found.
- Use `--reencode` for user-visible snippets that need accurate boundaries.

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
