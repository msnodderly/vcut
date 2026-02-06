import argparse
import shutil
import sys
import tempfile
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


MODEL_PRESETS = {
    "fast": "tiny.en",
    "balanced": "base.en",
    "quality": "distil-large-v3",
}


def cmd_transcribe(args):
    if args.model == "__list__":
        console.print("[bold]Available model presets:[/]")
        for preset, model in MODEL_PRESETS.items():
            default = " [dim](default)[/]" if preset == "quality" else ""
            console.print(f"  {preset:10s} → {model}{default}")
        console.print("\nAny faster-whisper model name is also accepted (e.g. large-v3, small.en).")
        sys.exit(0)
    args.model = MODEL_PRESETS.get(args.model, args.model)
    if args.chunk_size is None:
        args.chunk_size = 3.0
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

    output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_edited{input_path.suffix}")

    if output_path.is_file() and not args.force:
        if not console.input(f"[bold yellow]Output already exists:[/] {output_path}\nOverwrite? [y/N] ").strip().lower().startswith("y"):
            console.print("Aborted.")
            sys.exit(1)

    try:
        segments = parse_edited_file(transcript_src)
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print("\n[dim]Please fix the transcript file and try again.[/]")
        sys.exit(1)

    if not segments:
        console.print("[yellow]No segments in transcript. Nothing to render.[/]")
        sys.exit(0)

    tmp_dir = Path(tempfile.mkdtemp(prefix="vcut_"))
    try:
        mode = "re-encode" if args.reencode else "stream copy"
        console.print(f"[bold]Rendering {len(segments)} segments ({mode})...[/]")
        render(input_path, segments, output_path, tmp_dir, args.reencode)
        console.print(f"[bold green]Done![/] Output: {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print(f"Temp files preserved at: {tmp_dir}")
        sys.exit(1)
    else:
        shutil.rmtree(tmp_dir, ignore_errors=True)


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

    try:
        console.print(f"[bold]Opening editor...[/] ({transcript_src})")
        rc = open_editor(working_copy)
        if rc != 0:
            console.print(f"[bold red]Editor exited with code {rc}. Aborting.[/]")
            sys.exit(1)

        try:
            segments = parse_edited_file(working_copy)
        except ValueError as e:
            console.print(f"[bold red]Error:[/] {e}")
            console.print(f"\n[dim]The edited file is preserved at: {working_copy}[/]")
            console.print(f"[dim]Please fix the issues and copy it back to: {transcript_src}[/]")
            sys.exit(1)

        if not segments:
            console.print("[yellow]No segments remaining after edit. Nothing to render.[/]")
            sys.exit(0)

        output_path = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_edited{input_path.suffix}")

        if output_path.is_file() and not args.force:
            if not console.input(f"[bold yellow]Output already exists:[/] {output_path}\nOverwrite? [y/N] ").strip().lower().startswith("y"):
                console.print("Aborted.")
                sys.exit(1)

        mode = "re-encode" if args.reencode else "stream copy"
        console.print(f"[bold]Rendering {len(segments)} segments ({mode})...[/]")
        render(input_path, segments, output_path, tmp_dir, args.reencode)
        console.print(f"[bold green]Done![/] Output: {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print(f"Temp files preserved at: {tmp_dir}")
        sys.exit(1)
    else:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        prog="vcut",
        description="Edit video by editing its transcript.",
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
    p_transcribe.add_argument("-c", "--chunk-size", type=float, default=None, help="Target segment duration in seconds (default: 3)")
    p_transcribe.add_argument("--force", action="store_true", help="Overwrite existing transcript")

    # -- render --
    p_render = sub.add_parser("render", aliases=["r"], help="Render video from edited transcript")
    p_render.add_argument("input", help="Input video file")
    p_render.add_argument("-t", "--transcript", help="Transcript file (default: {input}.txt)")
    p_render.add_argument("-o", "--output", help="Output video path (default: {input}_edited.mp4)")
    p_render.add_argument("-r", "--reencode", action="store_true", help="Re-encode for precise cuts")
    p_render.add_argument("--force", action="store_true", help="Overwrite output without prompting")

    # -- edit --
    p_edit = sub.add_parser("edit", aliases=["e"], help="Open transcript in $EDITOR, then render (convenience)")
    p_edit.add_argument("input", help="Input video file")
    p_edit.add_argument("-t", "--transcript", help="Transcript file (default: {input}.txt)")
    p_edit.add_argument("-o", "--output", help="Output video path (default: {input}_edited.mp4)")
    p_edit.add_argument("-r", "--reencode", action="store_true", help="Re-encode for precise cuts")
    p_edit.add_argument("--force", action="store_true", help="Overwrite output without prompting")

    args = parser.parse_args()

    if args.command in ("transcribe", "t"):
        cmd_transcribe(args)
    elif args.command in ("render", "r"):
        cmd_render(args)
    elif args.command in ("edit", "e"):
        cmd_edit(args)
    else:
        parser.print_help()
        sys.exit(1)
