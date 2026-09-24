import os
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


def _hf_hub_cache_dir() -> Path:
    """Return the Hugging Face Hub cache directory using HF's env precedence."""
    if cache := os.environ.get("HF_HUB_CACHE"):
        return Path(cache).expanduser()
    if cache := os.environ.get("HUGGINGFACE_HUB_CACHE"):
        return Path(cache).expanduser()
    if hf_home := os.environ.get("HF_HOME"):
        return Path(hf_home).expanduser() / "hub"
    if xdg_cache_home := os.environ.get("XDG_CACHE_HOME"):
        return Path(xdg_cache_home).expanduser() / "huggingface" / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def _model_repo_id(model_name: str) -> str | None:
    """Map a faster-whisper size/name to its Hugging Face repo ID."""
    model_path = Path(model_name).expanduser()
    if model_path.exists():
        return None
    if "/" in model_name:
        return model_name

    try:
        from faster_whisper import utils as faster_whisper_utils
    except Exception:
        return None

    return getattr(faster_whisper_utils, "_MODELS", {}).get(model_name)


def _looks_like_complete_model_snapshot(snapshot_path: Path) -> bool:
    """Check for files needed to load faster-whisper without extra HF lookups."""
    return (
        (snapshot_path / "config.json").is_file()
        and (snapshot_path / "model.bin").is_file()
        and (snapshot_path / "tokenizer.json").is_file()
    )


def _cached_model_snapshot(repo_id: str) -> Path | None:
    """Return a complete cached snapshot path for repo_id, if one is available."""
    repo_cache = _hf_hub_cache_dir() / f"models--{repo_id.replace('/', '--')}"
    snapshots_dir = repo_cache / "snapshots"
    if not snapshots_dir.is_dir():
        return None

    candidates: list[Path] = []
    main_ref = repo_cache / "refs" / "main"
    try:
        if main_ref.is_file():
            candidates.append(snapshots_dir / main_ref.read_text().strip())
        candidates.extend(sorted(p for p in snapshots_dir.iterdir() if p.is_dir()))
    except OSError:
        return None

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if _looks_like_complete_model_snapshot(candidate):
            return candidate
    return None


def _resolve_cached_model_path(model_name: str) -> str:
    """
    Prefer an already-cached HF snapshot path over a model name.

    Passing a model name to faster-whisper can make huggingface_hub resolve the
    repo online even when files are already cached. Passing the snapshot path
    loads locally and avoids unnecessary HF requests.
    """
    model_path = Path(model_name).expanduser()
    if model_path.exists():
        return str(model_path)

    repo_id = _model_repo_id(model_name)
    if repo_id:
        cached_snapshot = _cached_model_snapshot(repo_id)
        if cached_snapshot:
            return str(cached_snapshot)

    return model_name


def transcribe(
    audio_path: Path,
    model_name: str,
    language: str | None,
    chunk_size: float,
    local_files_only: bool = False,
) -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel(
        _resolve_cached_model_path(model_name),
        compute_type="int8",
        local_files_only=local_files_only,
    )

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
