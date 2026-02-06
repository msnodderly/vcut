import os
from unittest.mock import patch

import pytest

from vcut.editor import parse_edited_file, parse_timestamp, get_editor


class TestParseTimestamp:
    def test_basic(self):
        assert parse_timestamp("00:00:00.000") == 0.0

    def test_hours_minutes_seconds(self):
        assert parse_timestamp("01:23:45.678") == 5025.678

    def test_boundary(self):
        assert parse_timestamp("00:59:59.999") == 3599.999

    def test_rejects_invalid_minutes(self):
        with pytest.raises(ValueError, match="minutes must be < 60"):
            parse_timestamp("00:61:00.000")

    def test_rejects_invalid_seconds(self):
        with pytest.raises(ValueError, match="seconds must be < 60"):
            parse_timestamp("00:00:61.000")

    def test_rejects_invalid_milliseconds(self):
        with pytest.raises(ValueError, match="milliseconds must be < 1000"):
            parse_timestamp("00:00:00.1000")


class TestParseEditedFile:
    def test_parse_basic(self, fixtures_dir):
        segments = parse_edited_file(fixtures_dir / "transcripts" / "basic.txt")
        assert len(segments) == 4
        assert segments[0] == (0.0, 2.5)
        assert segments[1] == (2.5, 5.0)
        assert segments[2] == (5.0, 7.5)
        assert segments[3] == (7.5, 10.0)

    def test_ignores_comments_and_blanks(self, fixtures_dir):
        segments = parse_edited_file(fixtures_dir / "transcripts" / "with-comments.txt")
        assert len(segments) == 3
        assert segments[0] == (0.0, 2.5)
        assert segments[1] == (5.0, 7.5)
        assert segments[2] == (7.5, 10.0)

    def test_merges_overlapping_segments(self, fixtures_dir):
        segments = parse_edited_file(fixtures_dir / "transcripts" / "overlapping.txt")
        assert len(segments) == 2
        assert segments[0] == (0.0, 5.0)
        assert segments[1] == (5.0, 7.5)

    def test_rejects_out_of_order(self, fixtures_dir):
        with pytest.raises(ValueError, match="Out-of-order segment"):
            parse_edited_file(fixtures_dir / "transcripts" / "reordered.txt")

    def test_rejects_start_after_end(self, tmp_path):
        f = tmp_path / "bad.txt"
        f.write_text("[00:00:05.000 -> 00:00:02.000] | Bad segment.\n")
        with pytest.raises(ValueError, match="start time .* must be before end time"):
            parse_edited_file(f)

    def test_empty_file_returns_empty(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert parse_edited_file(f) == []

    def test_all_commented_returns_empty(self, tmp_path):
        f = tmp_path / "commented.txt"
        f.write_text("# [00:00:00.000 -> 00:00:02.000] | Commented out.\n")
        assert parse_edited_file(f) == []


class TestGetEditor:
    def test_visual_takes_precedence(self):
        with patch.dict(os.environ, {"VISUAL": "nano", "EDITOR": "emacs"}):
            assert get_editor() == "nano"

    def test_editor_fallback(self):
        env = os.environ.copy()
        env.pop("VISUAL", None)
        env["EDITOR"] = "emacs"
        with patch.dict(os.environ, env, clear=True):
            assert get_editor() == "emacs"

    def test_vim_default(self):
        env = os.environ.copy()
        env.pop("VISUAL", None)
        env.pop("EDITOR", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_editor() == "vim"
