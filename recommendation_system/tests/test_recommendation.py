"""Phase 4 tests for the rule-based recommender.

Covers every emotion × mode × category on the real catalog, plus fixture
CSVs for empty data, missing columns, invalid rows, duplicates, missing
YouTube links, category isolation, partial bins, and change-mood fallback.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.config import CATEGORIES, EMOTIONS, MODES
from src.mappings import CHANGE_MOOD_MAP, STAY_MOOD_MAP, get_target_emotions
from src.data_loader import load_songs, youtube_search_url
from src.recommendation import (
    RecommendationError,
    format_recommendations,
    recommend_songs,
    validate_category,
    validate_emotion,
    validate_limit,
    validate_mode,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REAL_CSV = Path(__file__).resolve().parents[1] / "dataset" / "songs.csv"

REQUIRED_OUTPUT_KEYS = (
    "detected_emotion",
    "mode",
    "category",
    "target_emotions",
    "requested_limit",
    "count",
    "recommendations",
)
SONG_KEYS = ("title", "artist", "youtube_url")


# Mapping table used in assertions. Keep in sync with mappings.py (Mapping A).
EXPECTED_CHANGE_PRIMARY = {
    "sadness": "joy",
    "joy": "surprise",
    "love": "joy",
    "anger": "joy",
    "fear": "joy",
    "surprise": "joy",
}


def _titles(result: dict) -> list[str]:
    return [song["title"] for song in result["recommendations"]]


def test_config_constants_match_mappings():
    """Avoid importing a constant that does not exist on config."""
    assert set(STAY_MOOD_MAP) == set(EMOTIONS)
    assert set(CHANGE_MOOD_MAP) == set(EMOTIONS)
    for emotion in EMOTIONS:
        assert STAY_MOOD_MAP[emotion] == [emotion]
        assert CHANGE_MOOD_MAP[emotion][0] == EXPECTED_CHANGE_PRIMARY[emotion]


# ---------------------------------------------------------------------------
# Real catalog: 6 emotions × 2 modes × 2 categories
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("emotion", EMOTIONS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("category", CATEGORIES)
def test_all_combinations_return_five_structured_songs(emotion, mode, category):
    result = recommend_songs(
        emotion, mode, category, limit=5, csv_path=REAL_CSV, random_state=42
    )

    for key in REQUIRED_OUTPUT_KEYS:
        assert key in result

    assert result["detected_emotion"] == emotion
    assert result["mode"] == mode
    assert result["category"] == category
    assert result["requested_limit"] == 5
    assert result["count"] == 5
    assert len(result["recommendations"]) == 5

    expected_primary = emotion if mode == "stay_mood" else EXPECTED_CHANGE_PRIMARY[emotion]
    assert result["target_emotions"] == [expected_primary]

    seen = set()
    for song in result["recommendations"]:
        for field in SONG_KEYS:
            assert field in song
            assert isinstance(song[field], str) and song[field].strip()
        key = (song["title"].casefold(), song["artist"].casefold())
        assert key not in seen
        seen.add(key)
        assert song["youtube_url"].startswith("https://www.youtube.com/")


@pytest.mark.parametrize("emotion", EMOTIONS)
@pytest.mark.parametrize("category", CATEGORIES)
def test_stay_mood_uses_detected_emotion_only(emotion, category):
    result = recommend_songs(emotion, "stay_mood", category, csv_path=REAL_CSV)
    assert get_target_emotions(emotion, "stay_mood") == [emotion]
    assert result["target_emotions"] == [emotion]


@pytest.mark.parametrize("emotion", EMOTIONS)
@pytest.mark.parametrize("category", CATEGORIES)
def test_change_mood_uses_transition_mapping(emotion, category):
    targets = get_target_emotions(emotion, "change_mood")
    assert targets == CHANGE_MOOD_MAP[emotion]
    result = recommend_songs(emotion, "change_mood", category, csv_path=REAL_CSV)
    assert result["target_emotions"] == [CHANGE_MOOD_MAP[emotion][0]]
    if emotion != "joy":
        assert emotion not in result["target_emotions"]


def test_joy_change_mood_leaves_the_joy_bin():
    result = recommend_songs("joy", "change_mood", "classic", csv_path=REAL_CSV)
    assert result["target_emotions"] == ["surprise"]


def test_anger_change_mood_does_not_route_to_fear_or_sadness():
    targets = get_target_emotions("anger", "change_mood")
    assert "fear" not in targets
    assert "sadness" not in targets
    result = recommend_songs("anger", "change_mood", "classic", csv_path=REAL_CSV)
    assert result["target_emotions"] == ["joy"]


def test_classic_never_returns_rap_titles_from_isolation_fixture():
    csv_path = FIXTURES / "category_isolation.csv"
    result = recommend_songs("sadness", "stay_mood", "classic", csv_path=csv_path)
    assert _titles(result) == ["Classic Track"]
    assert "Rap Track" not in _titles(result)


def test_rap_never_returns_classic_titles_from_isolation_fixture():
    csv_path = FIXTURES / "category_isolation.csv"
    result = recommend_songs("sadness", "stay_mood", "rap", csv_path=csv_path)
    assert _titles(result) == ["Rap Track"]
    assert "Classic Track" not in _titles(result)


def test_real_catalog_category_filter_matches_csv_labels():
    catalog = load_songs(REAL_CSV)
    for category in CATEGORIES:
        result = recommend_songs("sadness", "stay_mood", category, csv_path=REAL_CSV)
        for song in result["recommendations"]:
            rows = catalog[
                (catalog["title"] == song["title"]) & (catalog["artist"] == song["artist"])
            ]
            assert not rows.empty
            assert (rows["category"] == category).all()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["happy", "SAD", "sad", "", "  ", 12, None])
def test_invalid_emotion_rejected(bad):
    if isinstance(bad, str) and bad.strip().lower() == "sadness":
        pytest.skip("normalized sadness is valid")
    with pytest.raises(RecommendationError, match="emotion"):
        recommend_songs(bad, "stay_mood", "classic", csv_path=REAL_CSV)


def test_emotion_is_normalized_to_lowercase():
    result = recommend_songs("Sadness", "stay_mood", "Classic", csv_path=REAL_CSV)
    assert result["detected_emotion"] == "sadness"
    assert result["category"] == "classic"


@pytest.mark.parametrize("bad", ["jazz", "hiphop", "HIP-HOP", "", None, 1])
def test_invalid_category_rejected(bad):
    with pytest.raises(RecommendationError, match="category"):
        recommend_songs("sadness", "stay_mood", bad, csv_path=REAL_CSV)


@pytest.mark.parametrize("bad", ["shuffle", "mood", "", None, 3])
def test_invalid_mode_rejected(bad):
    with pytest.raises(RecommendationError, match="mode"):
        recommend_songs("sadness", bad, "classic", csv_path=REAL_CSV)


@pytest.mark.parametrize(
    "alias,expected",
    [
        ("stay", "stay_mood"),
        ("stay_in_my_mood", "stay_mood"),
        ("change", "change_mood"),
        ("change_my_mood", "change_mood"),
    ],
)
def test_mode_aliases(alias, expected):
    assert validate_mode(alias) == expected


@pytest.mark.parametrize("bad", [0, 21, -1, "five", object()])
def test_invalid_limit_rejected(bad):
    with pytest.raises(RecommendationError, match="limit"):
        recommend_songs("sadness", "stay_mood", "classic", limit=bad, csv_path=REAL_CSV)


def test_default_limit_is_five():
    result = recommend_songs("sadness", "stay_mood", "classic", csv_path=REAL_CSV)
    assert result["requested_limit"] == 5
    assert result["count"] == 5


# ---------------------------------------------------------------------------
# Fixture CSVs: empty, missing fields, duplicates, missing URLs
# ---------------------------------------------------------------------------


def test_empty_dataset_raises_informative_error():
    with pytest.raises(RecommendationError, match="No songs available"):
        recommend_songs("sadness", "stay_mood", "classic", csv_path=FIXTURES / "empty.csv")


def test_missing_csv_columns_raise_value_error():
    with pytest.raises(ValueError, match="missing columns"):
        load_songs(FIXTURES / "missing_columns.csv")


def test_invalid_and_incomplete_rows_are_dropped():
    songs = load_songs(FIXTURES / "invalid_rows.csv")
    assert len(songs) == 1
    assert songs.iloc[0]["title"] == "Valid Song"


def test_duplicate_title_artist_are_collapsed():
    songs = load_songs(FIXTURES / "duplicates.csv")
    assert len(songs) == 2
    result = recommend_songs(
        "sadness", "stay_mood", "classic", limit=5, csv_path=FIXTURES / "duplicates.csv"
    )
    assert result["count"] == 2
    titles = _titles(result)
    assert titles.count("Same Song") == 1
    assert "Other Song" in titles
    same = next(s for s in result["recommendations"] if s["title"] == "Same Song")
    assert same["youtube_url"].endswith("firsturl001")


def test_missing_youtube_url_becomes_search_url():
    songs = load_songs(FIXTURES / "missing_youtube.csv")
    assert len(songs) == 2
    for _, row in songs.iterrows():
        expected = youtube_search_url(row["title"], row["artist"])
        assert row["youtube_url"] == expected
        assert "search_query=" in row["youtube_url"]

    result = recommend_songs(
        "sadness", "stay_mood", "classic", csv_path=FIXTURES / "missing_youtube.csv"
    )
    for song in result["recommendations"]:
        assert "search_query=" in song["youtube_url"]


def test_partial_bin_returns_fewer_than_limit():
    result = recommend_songs(
        "sadness", "stay_mood", "classic", limit=5, csv_path=FIXTURES / "partial_bin.csv"
    )
    assert result["count"] == 2
    assert result["requested_limit"] == 5
    assert len(result["recommendations"]) == 2


def test_change_mood_fallback_when_primary_bin_is_empty():
    # sadness -> joy (empty classic) -> surprise (present)
    result = recommend_songs(
        "sadness", "change_mood", "classic", csv_path=FIXTURES / "fallback_change_mood.csv"
    )
    assert result["target_emotions"] == ["surprise"]
    assert _titles(result) == ["Fallback Surprise"]


def test_change_mood_errors_when_all_targets_empty():
    # fear -> joy, then love. This fixture has neither in classic.
    with pytest.raises(RecommendationError, match="No songs available"):
        recommend_songs(
            "fear", "change_mood", "classic", csv_path=FIXTURES / "fallback_change_mood.csv"
        )


def test_missing_catalog_file():
    with pytest.raises(FileNotFoundError):
        load_songs(FIXTURES / "does_not_exist.csv")


def test_format_recommendations_shape():
    rows = pd.DataFrame(
        [
            {
                "title": "A",
                "artist": "B",
                "youtube_url": "https://www.youtube.com/watch?v=abcdefghijk",
                "emotion": "joy",
                "category": "classic",
            }
        ]
    )
    formatted = format_recommendations(rows)
    assert formatted == [
        {
            "title": "A",
            "artist": "B",
            "youtube_url": "https://www.youtube.com/watch?v=abcdefghijk",
        }
    ]


def test_validate_helpers_reject_blank_strings():
    with pytest.raises(RecommendationError):
        validate_emotion("   ")
    with pytest.raises(RecommendationError):
        validate_category("   ")
    with pytest.raises(RecommendationError):
        validate_mode("   ")
    assert validate_limit(None) == 5
    assert validate_emotion(" LOVE ") == "love"
