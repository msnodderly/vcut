from types import SimpleNamespace

from vcut.transcribe import (
    _cached_model_snapshot,
    _resolve_cached_model_path,
    format_timestamp,
    segments_to_text,
    merge_words_into_chunks,
)


class TestFormatTimestamp:
    def test_zero(self):
        assert format_timestamp(0.0) == "00:00:00.000"

    def test_hours_minutes_seconds_ms(self):
        assert format_timestamp(3661.5) == "01:01:01.500"

    def test_boundary(self):
        assert format_timestamp(3599.999) == "00:59:59.999"

    def test_large_hours(self):
        assert format_timestamp(36000.0) == "10:00:00.000"

    def test_sub_millisecond_rounding(self):
        assert format_timestamp(1.9999) == "00:00:02.000"
        assert format_timestamp(59.9999) == "00:01:00.000"


class TestSegmentsToText:
    def test_basic_format(self):
        segs = [{"start": 0.0, "end": 2.5, "text": "Hello world."}]
        result = segments_to_text(segs)
        assert result == "[00:00:00.000 -> 00:00:02.500] | Hello world.\n"

    def test_multiple_segments(self):
        segs = [
            {"start": 0.0, "end": 2.5, "text": "First."},
            {"start": 2.5, "end": 5.0, "text": "Second."},
        ]
        lines = segments_to_text(segs).strip().split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("[00:00:00.000 -> 00:00:02.500]")
        assert lines[1].startswith("[00:00:02.500 -> 00:00:05.000]")


class TestCachedModelResolution:
    def _make_cached_snapshot(self, cache_dir, repo_id="Systran/faster-whisper-tiny.en"):
        repo_cache = cache_dir / f"models--{repo_id.replace('/', '--')}"
        snapshot = repo_cache / "snapshots" / "abc123"
        snapshot.mkdir(parents=True)
        (repo_cache / "refs").mkdir()
        (repo_cache / "refs" / "main").write_text("abc123")
        for filename in ("config.json", "model.bin", "tokenizer.json"):
            (snapshot / filename).write_text("x")
        return snapshot

    def test_resolves_faster_whisper_alias_to_cached_snapshot(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "hub"
        snapshot = self._make_cached_snapshot(cache_dir)
        monkeypatch.setenv("HF_HUB_CACHE", str(cache_dir))

        assert _resolve_cached_model_path("tiny.en") == str(snapshot)

    def test_resolves_hf_repo_id_to_cached_snapshot(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "hub"
        snapshot = self._make_cached_snapshot(cache_dir)
        monkeypatch.setenv("HF_HUB_CACHE", str(cache_dir))

        assert _resolve_cached_model_path("Systran/faster-whisper-tiny.en") == str(snapshot)

    def test_keeps_model_name_when_cache_is_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "empty"))

        assert _resolve_cached_model_path("tiny.en") == "tiny.en"

    def test_incomplete_snapshot_is_ignored(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "hub"
        snapshot = self._make_cached_snapshot(cache_dir)
        (snapshot / "tokenizer.json").unlink()
        monkeypatch.setenv("HF_HUB_CACHE", str(cache_dir))

        assert _cached_model_snapshot("Systran/faster-whisper-tiny.en") is None
        assert _resolve_cached_model_path("tiny.en") == "tiny.en"


class TestMergeWordsIntoChunks:
    def _make_word(self, start, end, word):
        return SimpleNamespace(start=start, end=end, word=word)

    def _make_segment(self, words):
        return SimpleNamespace(words=[self._make_word(*w) for w in words])

    def test_basic_chunking(self):
        seg = self._make_segment([
            (0.0, 1.0, " Hello"),
            (1.0, 2.0, " world"),
            (2.0, 3.0, " this"),
            (3.0, 4.0, " is"),
            (4.0, 5.0, " a"),
            (5.0, 6.0, " test"),
        ])
        result = merge_words_into_chunks([seg], chunk_size=3.0)
        assert len(result) == 2
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 3.0
        assert result[1]["start"] == 3.0
        assert result[1]["end"] == 6.0

    def test_empty_words(self):
        seg = SimpleNamespace(words=[])
        assert merge_words_into_chunks([seg], chunk_size=3.0) == []

    def test_no_words_attr(self):
        seg = SimpleNamespace(words=None)
        assert merge_words_into_chunks([seg], chunk_size=3.0) == []

    def test_trailing_chunk(self):
        seg = self._make_segment([
            (0.0, 1.0, " Hello"),
            (1.0, 2.0, " world"),
        ])
        result = merge_words_into_chunks([seg], chunk_size=5.0)
        assert len(result) == 1
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 2.0
