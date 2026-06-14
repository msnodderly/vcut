from pathlib import Path

from vcut.cli import transcript_path_for, MODEL_PRESETS, build_parser


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


class TestHelpText:
    def test_top_level_help_includes_agent_workflows(self):
        help_text = build_parser().format_help()

        assert "Agent guide" in help_text
        assert "vcut edits video by editing timestamped transcript lines" in help_text
        assert "vcut transcribe \"input.mp4\" -o /tmp/input.vcut.txt" in help_text
        assert "Contiguous clip" in help_text
        assert "Supercut" in help_text
        assert "Remove or clean up parts" in help_text
        assert "ffprobe" in help_text
        assert "vcut render \"input.mp4\"" in help_text
