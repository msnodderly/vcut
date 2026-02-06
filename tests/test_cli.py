from pathlib import Path

from vcut.cli import transcript_path_for, MODEL_PRESETS


class TestTranscriptPathFor:
    def test_mp4(self):
        assert transcript_path_for(Path("video.mp4")) == Path("video.txt")

    def test_mkv(self):
        assert transcript_path_for(Path("test.mkv")) == Path("test.txt")

    def test_preserves_directory(self):
        assert transcript_path_for(Path("/tmp/video.mp4")) == Path("/tmp/video.txt")


class TestModelPresets:
    def test_presets_exist(self):
        assert "fast" in MODEL_PRESETS
        assert "balanced" in MODEL_PRESETS
        assert "quality" in MODEL_PRESETS

    def test_quality_is_default(self):
        assert MODEL_PRESETS["quality"] == "distil-large-v3"
