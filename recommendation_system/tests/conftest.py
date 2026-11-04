"""Shared paths for Phase 4 tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
REAL_CSV = Path(__file__).resolve().parents[1] / "dataset" / "songs.csv"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def real_csv() -> Path:
    return REAL_CSV
