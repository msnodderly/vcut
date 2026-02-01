import subprocess
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

console = Console()


def render(
    input_video: Path,
    segments: list[tuple[float, float]],
    output_path: Path,
    tmp_dir: Path,
    reencode: bool,
) -> None:
    seg_files = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Extracting segments..."),
        BarColumn(),
        MofNCompleteColumn(),
    ) as progress:
        task = progress.add_task("segments", total=len(segments))
        for i, (start, end) in enumerate(segments):
            seg_path = tmp_dir / f"seg_{i:04d}.mp4"
            if reencode:
                # -ss after -i for precise decode, then re-encode
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-i", str(input_video),
                        "-ss", str(start),
                        "-to", str(end),
                        "-avoid_negative_ts", "make_zero",
                        str(seg_path),
                    ],
                    capture_output=True,
                    check=True,
                )
            else:
                # -ss before -i for fast keyframe seek, -c copy
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-ss", str(start),
                        "-i", str(input_video),
                        "-t", str(end - start),
                        "-c", "copy",
                        "-avoid_negative_ts", "make_zero",
                        str(seg_path),
                    ],
                    capture_output=True,
                    check=True,
                )
            seg_files.append(seg_path)
            progress.update(task, advance=1)

    # Concat via demuxer
    concat_list = tmp_dir / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{f}'" for f in seg_files) + "\n"
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(output_path),
        ],
        capture_output=True,
        check=True,
    )
