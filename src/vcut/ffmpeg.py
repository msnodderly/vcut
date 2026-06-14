import subprocess


def run_ffmpeg(args: list[str]) -> None:
    """Run `ffmpeg -y <args>`.

    On failure, raise a RuntimeError containing the tail of ffmpeg's stderr so
    the caller can show *why* it failed instead of a bare exit code.
    """
    try:
        subprocess.run(
            ["ffmpeg", "-y", *args],
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        tail = "\n".join(stderr.splitlines()[-15:])
        detail = f":\n{tail}" if tail else "."
        raise RuntimeError(f"ffmpeg exited with status {e.returncode}{detail}") from e
