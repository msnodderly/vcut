from unittest.mock import patch

from vcut.render import render


class TestRender:
    def test_stream_copy_ffmpeg_args(self, tmp_path):
        input_video = tmp_path / "video.mp4"
        input_video.touch()
        output = tmp_path / "out.mp4"
        segments = [(1.0, 5.0)]

        with patch("vcut.render.subprocess.run") as mock_run:
            render(input_video, segments, output, tmp_path, reencode=False)

        extract_call = mock_run.call_args_list[0]
        cmd = extract_call[0][0]
        assert "-c" in cmd and "copy" in cmd
        ss_idx = cmd.index("-ss")
        i_idx = cmd.index("-i")
        assert ss_idx < i_idx

    def test_reencode_ffmpeg_args(self, tmp_path):
        input_video = tmp_path / "video.mp4"
        input_video.touch()
        output = tmp_path / "out.mp4"
        segments = [(1.0, 5.0)]

        with patch("vcut.render.subprocess.run") as mock_run:
            render(input_video, segments, output, tmp_path, reencode=True)

        extract_call = mock_run.call_args_list[0]
        cmd = extract_call[0][0]
        assert "-c" not in cmd or "copy" not in cmd
        i_idx = cmd.index("-i")
        ss_idx = cmd.index("-ss")
        assert i_idx < ss_idx

    def test_concat_file_written(self, tmp_path):
        input_video = tmp_path / "video.mp4"
        input_video.touch()
        output = tmp_path / "out.mp4"
        segments = [(0.0, 2.0), (3.0, 5.0)]

        with patch("vcut.render.subprocess.run"):
            render(input_video, segments, output, tmp_path, reencode=False)

        concat = tmp_path / "concat.txt"
        assert concat.exists()
        lines = concat.read_text().strip().split("\n")
        assert len(lines) == 2
        assert all(line.startswith("file '") for line in lines)
