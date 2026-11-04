"""Rule-based song recommendation.

Pipeline:
1. Validate emotion, mode, category, and limit.
2. Map the detected emotion to one or more target emotions (mode).
3. Filter the catalog by category (hard) and target emotion.
4. Deduplicate, sample up to `limit`, format JSON-ready records.

This module never calls the NLP classifier. It only needs an emotion string.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import CATEGORIES, DEFAULT_LIMIT, EMOTIONS, MAX_LIMIT, MIN_LIMIT, MODES
from .data_loader import load_songs
from .mappings import get_target_emotions as map_target_emotions


class RecommendationError(ValueError):
    """Invalid input or empty catalog for the requested filters."""


def validate_emotion(emotion: object) -> str:
    if not isinstance(emotion, str) or not emotion.strip():
        raise RecommendationError("emotion is required and must be a non-empty string.")
    value = emotion.strip().lower()
    if value not in EMOTIONS:
        allowed = ", ".join(EMOTIONS)
        raise RecommendationError(f"Unknown emotion '{emotion}'. Allowed: {allowed}.")
    return value


def validate_category(category: object) -> str:
    if not isinstance(category, str) or not category.strip():
        raise RecommendationError("category is required and must be a non-empty string.")
    value = category.strip().lower()
    if value not in CATEGORIES:
        allowed = ", ".join(CATEGORIES)
        raise RecommendationError(f"Unknown category '{category}'. Allowed: {allowed}.")
    return value


def validate_mode(mode: object) -> str:
    if not isinstance(mode, str) or not mode.strip():
        raise RecommendationError("mode is required and must be a non-empty string.")
    value = mode.strip().lower()
    aliases = {
        "stay": "stay_mood",
        "stay_in_my_mood": "stay_mood",
        "change": "change_mood",
        "change_my_mood": "change_mood",
    }
    value = aliases.get(value, value)
    if value not in MODES:
        allowed = ", ".join(MODES)
        raise RecommendationError(f"Unknown mode '{mode}'. Allowed: {allowed}.")
    return value


def validate_limit(limit: object) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    try:
        value = int(limit)
    except (TypeError, ValueError) as exc:
        raise RecommendationError("limit must be an integer.") from exc
    if value < MIN_LIMIT or value > MAX_LIMIT:
        raise RecommendationError(f"limit must be between {MIN_LIMIT} and {MAX_LIMIT}.")
    return value


def get_target_emotions(emotion: object, mode: object) -> list[str]:
    """Public helper: validate inputs, then return ordered target emotions."""
    return map_target_emotions(validate_emotion(emotion), validate_mode(mode))


def _filter_bin(songs: pd.DataFrame, emotion: str, category: str) -> pd.DataFrame:
    return songs[(songs["emotion"] == emotion) & (songs["category"] == category)]


def _pick_rows(pool: pd.DataFrame, limit: int, random_state: int | None) -> pd.DataFrame:
    if pool.empty:
        return pool
    unique = pool.drop_duplicates(subset=["title", "artist"], keep="first")
    if len(unique) <= limit:
        return unique.reset_index(drop=True)
    return unique.sample(n=limit, random_state=random_state).reset_index(drop=True)


def format_recommendations(rows: pd.DataFrame) -> list[dict[str, str]]:
    """Keep only the fields the Flutter song card needs."""
    records = []
    for row in rows.itertuples(index=False):
        records.append(
            {
                "title": row.title,
                "artist": row.artist,
                "youtube_url": row.youtube_url,
            }
        )
    return records


def recommend_songs(
    emotion: object,
    mode: object,
    category: object,
    limit: object = None,
    *,
    csv_path: str | Path | None = None,
    songs: pd.DataFrame | None = None,
    random_state: int | None = 42,
) -> dict:
    """Return structured recommendations for one emotion / mode / category.

    `random_state` is fixed by default so demos and tests are reproducible.
    Pass `random_state=None` later if you want a different shuffle each call.
    """
    emotion = validate_emotion(emotion)
    mode = validate_mode(mode)
    category = validate_category(category)
    limit = validate_limit(limit)

    catalog = songs if songs is not None else load_songs(csv_path)
    targets = map_target_emotions(emotion, mode)

    chosen = pd.DataFrame(columns=catalog.columns)
    used_targets: list[str] = []
    for target in targets:
        pool = _filter_bin(catalog, target, category)
        if pool.empty:
            continue
        used_targets.append(target)
        chosen = pool
        break

    if chosen.empty:
        raise RecommendationError(
            "No songs available for "
            f"emotion={emotion!r}, mode={mode!r}, category={category!r}, "
            f"target_emotions={targets}."
        )

    picked = _pick_rows(chosen, limit, random_state)
    payload = {
        "detected_emotion": emotion,
        "mode": mode,
        "category": category,
        "target_emotions": used_targets,
        "requested_limit": limit,
        "count": int(len(picked)),
        "recommendations": format_recommendations(picked),
    }
    return payload


def _demo() -> None:
    """Manual checks used in Phase 3 (not the full Phase 4 test suite)."""
    examples = [
        {"emotion": "sadness", "mode": "stay_mood", "category": "classic", "limit": 5},
        {"emotion": "sadness", "mode": "change_mood", "category": "rap", "limit": 5},
        {"emotion": "joy", "mode": "change_mood", "category": "classic", "limit": 5},
        {"emotion": "anger", "mode": "stay_mood", "category": "rap", "limit": 3},
    ]
    for example in examples:
        result = recommend_songs(**example)
        print("=" * 72)
        print(
            f"{result['detected_emotion']} | {result['mode']} | "
            f"{result['category']} -> {result['target_emotions']} "
            f"({result['count']} songs)"
        )
        for song in result["recommendations"]:
            print(f"  - {song['title']} — {song['artist']}")
            print(f"    {song['youtube_url']}")


if __name__ == "__main__":
    _demo()
