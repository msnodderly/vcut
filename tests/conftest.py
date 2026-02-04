"""Pytest configuration and fixtures for vcut tests."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_video(fixtures_dir):
    """Return path to sample video."""
    video = fixtures_dir / "videos" / "sample-10s.mp4"
    if not video.exists():
        pytest.skip("Sample video not available")
    return video


@pytest.fixture
def sample_transcript(fixtures_dir):
    """Return path to sample transcript."""
    return fixtures_dir / "transcripts" / "basic.txt"


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
