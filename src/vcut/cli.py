import argparse
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

from rich.console import Console

from vcut.transcribe import extract_audio, transcribe, segments_to_text
from vcut.editor import open_editor, parse_edited_file
from vcut.render import render

console = Console()


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        console.print(
            "[bold red]Error:[/] ffmpeg not found on $PATH.\n"
            "Install it: https://ffmpeg.org/download.html",
        )
        sys.exit(1)


def transcript_path_for(video_path: Path) -> Path:
    return video_path.with_suffix(".txt")


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_edited{input_path.suffix}")


def confirm_overwrite(output_path: Path, force: bool) -> None:
    """Prompt before clobbering an existing output; exit if the user declines."""
    if output_path.is_file() and not force:
        answer = console.input(
            f"[bold yellow]Output already exists:[/] {output_path}\nOverwrite? [y/N] "
        )
        if not answer.strip().lower().startswith("y"):
            console.print("Aborted.")
            sys.exit(1)


def run_render(input_path: Path, segments, output_path: Path, reencode: bool) -> None:
    """Render segments to output_path, managing the temp dir and ffmpeg errors."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="vcut_"))
    try:
        mode = "re-encode" if reencode else "stream copy"
        console.print(f"[bold]Rendering {len(segments)} segments ({mode})...[/]")
        render(input_path, segments, output_path, tmp_dir, reencode)
        console.print(f"[bold green]Done![/] Output: {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print(f"Temp files preserved at: {tmp_dir}")
        sys.exit(1)
    else:
        shutil.rmtree(tmp_dir, ignore_errors=True)


MODEL_PRESETS = {
    "fast": "tiny.en",
    "balanced": "base.en",
    "quality": "distil-large-v3",
}


AGENT_HELP = """\
Agent guide:

  vcut edits video by editing timestamped transcript lines. The render command
  keeps every uncommented transcript line and removes deleted or # commented
  lines. Each line has this format:

       [HH:MM:SS.mmm -> HH:MM:SS.mmm] | spoken text

  Start every unfamiliar vcut task by reading this help:
       vcut --help

Agent investigation workflow:

  1. Transcribe to a scratch file. Use smaller chunks when you need searchable
     boundaries around phrases, topics, or repeated words:
       vcut transcribe "input.mp4" -o /tmp/input.vcut.txt -m balanced -l en -c 2 --force

     If the model is not cached, this may download a faster-whisper model.
     The "balanced" preset is usually enough for locating a clip; use "quality"
     for a more accurate transcript when time is less important.

  2. Search the transcript for requested text, likely transcription variants,
     and nearby wording:
       rg -n -i 'phrase|alternate spelling|related term' /tmp/input.vcut.txt
       sed -n 'START,ENDp' /tmp/input.vcut.txt

  3. Choose the editing pattern that matches the request:

     Contiguous clip:
       Use this for "create a snippet of the section where..." or any request
       for one continuous excerpt. Create one synthetic transcript line spanning
       the chosen start/end timestamps:
         printf '%s\\n' '[00:32:18.400 -> 00:37:42.840] | requested section' > /tmp/clip.vcut.txt
         vcut render "input.mp4" -t /tmp/clip.vcut.txt -o "requested-section.mp4" --reencode --force

     Supercut:
       Use this for "every time they say..." or other jump-cut compilations.
       Keep multiple matching transcript lines:
         rg -i 'amazing|incredible' /tmp/input.vcut.txt > /tmp/supercut.vcut.txt
         vcut render "input.mp4" -t /tmp/supercut.vcut.txt -o "supercut.mp4" --reencode --force

     Remove or clean up parts:
       Copy the full transcript, then delete or # comment lines to remove.
       This preserves the rest of the video:
         cp /tmp/input.vcut.txt /tmp/clean.vcut.txt
         # edit /tmp/clean.vcut.txt, or generate it with rg/sed/awk
         vcut render "input.mp4" -t /tmp/clean.vcut.txt -o "clean.mp4" --reencode --force

     Manual edit:
       If the user wants to hand-edit, transcribe next to the video or pass
       --transcript, then run:
         vcut edit "input.mp4" --reencode

     Use --reencode for accurate user-visible outputs. Omit it only when speed is
     more important than precise boundaries.

  4. Verify the output:
       ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "output.mp4"

Important constraints:
  - vcut writes the output path you pass to -o. If the source video is outside
    the writable workspace, write the snippet inside the current project or /tmp.
  - If the user asks for a concept name that is not found, search likely
    transcription variants and report the term actually found.
  - Do not render every transcript line separately for one continuous section;
    that is slower and creates jump cuts. Use one synthetic transcript line.
  - If you created a user-visible output that needs manual testing, include a
    basic smoke test with the current branch/worktree in your final response.
"""


def cmd_transcribe(args):
    if args.model == "__list__":
        console.print("[bold]Available model presets:[/]")
        for preset, model in MODEL_PRESETS.items():
            default = " [dim](default)[/]" if preset == "quality" else ""
            console.print(f"  {preset:10s} → {model}{default}")
        console.print("\nAny faster-whisper model name is also accepted (e.g. large-v3, small.en).")
        sys.exit(0)
    args.model = MODEL_PRESETS.get(args.model, args.model)
    input_path = Path(args.input)
    if not input_path.is_file():
        console.print(f"[bold red]Error:[/] File not found: {input_path}")
        sys.exit(1)

    check_ffmpeg()

    out_path = Path(args.output) if args.output else transcript_path_for(input_path)

    if out_path.is_file() and not args.force:
        console.print(f"[bold yellow]Transcript already exists:[/] {out_path}")
        console.print("Use --force to overwrite.")
        sys.exit(1)

    tmp_dir = Path(tempfile.mkdtemp(prefix="vcut_"))
    try:
        console.print("[bold]Extracting audio...[/]")
        audio_path = extract_audio(input_path, tmp_dir)

        segments = transcribe(audio_path, args.model, args.language, args.chunk_size)
        if not segments:
            console.print("[bold red]Error:[/] No speech detected in the video.")
            sys.exit(1)

        out_path.write_text(segments_to_text(segments))
        console.print(f"[bold green]Transcript saved:[/] {out_path}")
        console.print(f"[dim]Next: vcut edit {args.input}  (or: vcut render {args.input})[/]")
    except RuntimeError as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def cmd_render(args):
    input_path = Path(args.input)
    if not input_path.is_file():
        console.print(f"[bold red]Error:[/] File not found: {input_path}")
        sys.exit(1)

    check_ffmpeg()

    transcript_src = Path(args.transcript) if args.transcript else transcript_path_for(input_path)
    if not transcript_src.is_file():
        console.print(f"[bold red]Error:[/] Transcript not found: {transcript_src}")
        if not args.transcript:
            console.print(f"[dim]Run first: vcut transcribe {args.input}[/]")
        sys.exit(1)

    output_path = Path(args.output) if args.output else default_output_path(input_path)
    confirm_overwrite(output_path, args.force)

    try:
        segments = parse_edited_file(transcript_src)
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print("\n[dim]Please fix the transcript file and try again.[/]")
        sys.exit(1)

    if not segments:
        console.print("[yellow]No segments in transcript. Nothing to render.[/]")
        sys.exit(0)

    run_render(input_path, segments, output_path, args.reencode)


def cmd_edit(args):
    """Convenience: open the transcript in $EDITOR, then render."""
    input_path = Path(args.input)
    if not input_path.is_file():
        console.print(f"[bold red]Error:[/] File not found: {input_path}")
        sys.exit(1)

    check_ffmpeg()

    transcript_src = Path(args.transcript) if args.transcript else transcript_path_for(input_path)
    if not transcript_src.is_file():
        console.print(f"[bold red]Error:[/] Transcript not found: {transcript_src}")
        console.print(f"[dim]Run first: vcut transcribe {args.input}[/]")
        sys.exit(1)

    # Copy to a working file so the original is preserved
    tmp_dir = Path(tempfile.mkdtemp(prefix="vcut_"))
    working_copy = tmp_dir / "transcript.txt"
    shutil.copy(transcript_src, working_copy)

    console.print(f"[bold]Opening editor...[/] ({transcript_src})")
    rc = open_editor(working_copy)
    if rc != 0:
        console.print(f"[bold red]Editor exited with code {rc}. Aborting.[/]")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        sys.exit(1)

    try:
        segments = parse_edited_file(working_copy)
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        # Keep the edited file (don't remove tmp_dir) so edits aren't lost.
        console.print(f"\n[dim]The edited file is preserved at: {working_copy}[/]")
        console.print(f"[dim]Please fix the issues and copy it back to: {transcript_src}[/]")
        sys.exit(1)

    if not segments:
        console.print("[yellow]No segments remaining after edit. Nothing to render.[/]")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        sys.exit(0)

    output_path = Path(args.output) if args.output else default_output_path(input_path)
    confirm_overwrite(output_path, args.force)
    run_render(input_path, segments, output_path, args.reencode)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vcut",
        description="Edit video by editing its transcript.",
        epilog=textwrap.dedent(AGENT_HELP),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # -- transcribe --
    p_transcribe = sub.add_parser("transcribe", aliases=["t"], help="Generate transcript from video")
    p_transcribe.add_argument("input", help="Input video file")
    p_transcribe.add_argument("-o", "--output", help="Output transcript path (default: {input}.txt)")
    p_transcribe.add_argument(
        "-m", "--model", default="distil-large-v3",
        nargs="?", const="__list__",
        metavar="MODEL",
        help="Whisper model preset or name. "
             "Presets: fast (tiny.en), balanced (base.en), quality (distil-large-v3). "
             "Default: quality. Any faster-whisper model name also accepted. "
             "Pass -m alone to list presets.",
    )
    p_transcribe.add_argument("-l", "--language", default=None, help="Force transcription language")
    p_transcribe.add_argument("-c", "--chunk-size", type=float, default=3.0, help="Target segment duration in seconds (default: 3)")
    p_transcribe.add_argument("--force", action="store_true", help="Overwrite existing transcript")
    p_transcribe.set_defaults(func=cmd_transcribe)

    # -- render --
    p_render = sub.add_parser("render", aliases=["r"], help="Render video from edited transcript")
    p_render.add_argument("input", help="Input video file")
    p_render.add_argument("-t", "--transcript", help="Transcript file (default: {input}.txt)")
    p_render.add_argument("-o", "--output", help="Output video path (default: {input}_edited.mp4)")
    p_render.add_argument("-r", "--reencode", action="store_true", help="Re-encode for precise cuts")
    p_render.add_argument("--force", action="store_true", help="Overwrite output without prompting")
    p_render.set_defaults(func=cmd_render)

    # -- edit --
    p_edit = sub.add_parser("edit", aliases=["e"], help="Open transcript in $EDITOR, then render (convenience)")
    p_edit.add_argument("input", help="Input video file")
    p_edit.add_argument("-t", "--transcript", help="Transcript file (default: {input}.txt)")
    p_edit.add_argument("-o", "--output", help="Output video path (default: {input}_edited.mp4)")
    p_edit.add_argument("-r", "--reencode", action="store_true", help="Re-encode for precise cuts")
    p_edit.add_argument("--force", action="store_true", help="Overwrite output without prompting")
    p_edit.set_defaults(func=cmd_edit)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not getattr(args, "func", None):
        parser.print_help()
        sys.exit(1)

    args.func(args)
