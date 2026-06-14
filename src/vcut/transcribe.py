from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from vcut.ffmpeg import run_ffmpeg


def extract_audio(video_path: Path, tmp_dir: Path) -> Path:
    audio_path = tmp_dir / "audio.wav"
    run_ffmpeg([
        "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_path),
    ])
    return audio_path


def merge_words_into_chunks(segments: list, chunk_size: float) -> list[dict]:
    """Merge word-level timestamps into segments of approximately chunk_size seconds."""
    # Collect all words from all segments
    words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                words.append({"start": w.start, "end": w.end, "word": w.word})

    if not words:
        return []

    results = []
    chunk_start = words[0]["start"]
    chunk_words = []

    for w in words:
        if chunk_start is None:
            chunk_start = w["start"]
        chunk_words.append(w["word"])

        if w["end"] - chunk_start >= chunk_size:
            results.append({
                "start": chunk_start,
                "end": w["end"],
                "text": " ".join(word.strip() for word in chunk_words),
            })
            chunk_words = []
            chunk_start = None

    if chunk_words:
        results.append({
            "start": chunk_start,
            "end": words[-1]["end"],
            "text": " ".join(word.strip() for word in chunk_words),
        })

    return results


def transcribe(
    audio_path: Path,
    model_name: str,
    language: str | None,
    chunk_size: float,
) -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, compute_type="int8")

    kwargs: dict = {"word_timestamps": True}
    if language:
        kwargs["language"] = language

    segments_iter, info = model.transcribe(str(audio_path), **kwargs)

    raw_segments = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Transcribing..."),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("transcribe", total=info.duration)
        for seg in segments_iter:
            raw_segments.append(seg)
            progress.update(task, completed=seg.end)
        progress.update(task, completed=info.duration)

    return merge_words_into_chunks(raw_segments, chunk_size)


def format_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    h = total_ms // 3_600_000
    total_ms %= 3_600_000
    m = total_ms // 60_000
    total_ms %= 60_000
    s = total_ms // 1000
    ms = total_ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def segments_to_text(segments: list[dict]) -> str:
    lines = []
    for seg in segments:
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        lines.append(f"[{start} -> {end}] | {seg['text']}")
    return "\n".join(lines) + "\n"
