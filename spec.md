# Specification: vcut (CLI Video Editor)

## 1. Project Overview
`vcut` is a minimalist CLI tool that allows users to edit video files by manipulating a generated text transcript. It follows the Unix philosophy: "Text is the universal interface." By editing the transcript in a system editor like Vim, users can cut and sequence video segments with standard text-editing commands.

## 2. Technical Stack
- **Transcription:** `faster-whisper` (default model: `distil-large-v3`, configurable via `--model`).
- **Processing:** `FFmpeg` (system-level installation required).
- **Environment:** Python 3.10+ (using `subprocess` for system calls).
- **Editor (optional):** `$VISUAL` → `$EDITOR` → `vim` (standard precedence, only used by `edit` subcommand).
- **Progress:** `rich` for transcription progress and status output.

## 3. CLI Interface

Three explicit subcommands for a phased workflow:

```
# Phase 1: Generate transcript
vcut transcribe video.mp4                   # → video.txt

# Phase 2: User edits the transcript manually
vim video.txt                                   # delete lines, comment out lines

# Phase 3: Render edited video
vcut render video.mp4                        # reads video.txt → video_edited.mp4
```

Optional convenience command that combines editing and rendering:
```
vcut edit video.mp4                          # opens video.txt in $EDITOR, then renders
```

### Subcommands

#### `vcut transcribe <input>`
Generate a transcript from a video file.

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output` | `-o` | `{input}.txt` | Output transcript path |
| `--model` | `-m` | `distil-large-v3` | Whisper model name |
| `--language` | `-l` | auto-detect | Force transcription language |
| `--force` | | `false` | Overwrite existing transcript |

#### `vcut render <input>`
Render video from an edited transcript.

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--transcript` | `-t` | `{input}.txt` | Transcript file to use |
| `--output` | `-o` | `{input}_edited.mp4` | Output video path |
| `--reencode` | `-r` | `false` | Re-encode for frame-perfect cuts |

#### `vcut edit <input>`
Convenience: open transcript in `$EDITOR`, then render on save. Requires transcript to already exist.

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--transcript` | `-t` | `{input}.txt` | Transcript file to edit |
| `--output` | `-o` | `{input}_edited.mp4` | Output video path |
| `--reencode` | `-r` | `false` | Re-encode for frame-perfect cuts |

## 4. Workflow

### Phase 1: Transcribe (`vcut transcribe`)
- Validate input file exists.
- Check that `ffmpeg` is available on `$PATH`.
- Refuse to overwrite existing transcript unless `--force` is passed.
- Extract audio from video via FFmpeg (WAV, 16kHz mono).
- Run `faster-whisper` to produce timestamped segments.
- Save transcript as `{input}.txt`. Format per line:
  ```
  [00:00:01.200 -> 00:00:04.500] | This is the spoken text.
  ```
- Display progress via `rich`.

### Phase 2: Manual Edit (user's responsibility)
- User opens the `.txt` file in any editor they prefer.
- Delete lines to cut content.
- Comment lines with `#` to exclude them.
- Blank lines are ignored.
- User can re-edit and re-render as many times as they want.

### Phase 3: Render (`vcut render`)
- Parse the transcript file via regex to extract timestamps.
- Lines starting with `#` and blank lines are ignored.
- Segments are rendered in their original chronological order.
- **Stream copy mode** (default): Use `-ss` before `-i` with `-c copy` for fast keyframe-based extraction, then concat demuxer. Near-instant but cuts on keyframes.
- **Re-encode mode** (`--reencode`): Decode and re-encode each segment for frame-perfect cuts, then concat.

### Convenience: Edit + Render (`vcut edit`)
- Requires transcript to already exist (run `transcribe` first).
- Copies transcript to a temp working file.
- Opens in `$VISUAL` / `$EDITOR` / `vim`.
- On save and exit, parses edits and renders.
- Original transcript file is preserved.

## 5. Error Handling
- **FFmpeg not found:** Exit with clear message and install instructions.
- **Invalid input file:** Exit with message.
- **Transcript already exists (`transcribe`):** Exit with message, suggest `--force`.
- **Transcript not found (`render`/`edit`):** Exit with message, suggest `vcut transcribe`.
- **Editor exits non-zero (`edit`):** Abort without rendering.
- **Empty transcript (all lines deleted/commented):** Abort with message, no output produced.
- **FFmpeg render failure:** Preserve temp files, print error and temp path.

## 6. Package Structure
```
vcut/
├── pyproject.toml
├── src/
│   └── vcut/
│       ├── __init__.py
│       ├── cli.py          # subcommand parsing, main entry point
│       ├── transcribe.py   # audio extraction + whisper
│       ├── editor.py       # editor launch + transcript parsing
│       └── render.py       # ffmpeg segment extraction + concat
├── spec.md
└── README.md
```

Installed as `vcut` command via pyproject.toml `[project.scripts]`.
