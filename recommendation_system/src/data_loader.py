"""Load and clean songs.csv.

Invalid rows are dropped rather than guessed. Growing the CSV does not
require code changes as long as the column names stay the same.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd

from .config import CATEGORIES, DATASET_PATH, EMOTIONS, REQUIRED_COLUMNS


def youtube_search_url(title: str, artist: str) -> str:
    """Build a YouTube search URL when a specific video id is missing."""
    query = f"{artist} {title} official"
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"


def load_songs(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Read the catalog, drop unusable rows, normalize labels.

    A row is kept only if it has emotion, category, title, and artist, and
    those labels belong to the allowed sets. Missing youtube_url is replaced
    by a search URL so the Flutter YouTube button still has somewhere to go.
    """
    path = Path(csv_path) if csv_path is not None else DATASET_PATH
    if not path.exists():
        raise FileNotFoundError(f"Song catalog not found: {path}")

    df = pd.read_csv(path)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"songs.csv is missing columns: {missing_cols}")

    df = df.copy()
    for col in REQUIRED_COLUMNS:
        df[col] = df[col].apply(lambda value: "" if pd.isna(value) else str(value).strip())

    df["emotion"] = df["emotion"].str.lower()
    df["category"] = df["category"].str.lower()

    usable = (
        df["emotion"].isin(EMOTIONS)
        & df["category"].isin(CATEGORIES)
        & df["title"].ne("")
        & df["artist"].ne("")
    )
    df = df.loc[usable].copy()

    missing_url = df["youtube_url"].eq("")
    df.loc[missing_url, "youtube_url"] = [
        youtube_search_url(title, artist)
        for title, artist in zip(df.loc[missing_url, "title"], df.loc[missing_url, "artist"])
    ]

    df = df.drop_duplicates(subset=["title", "artist"], keep="first")
    return df.reset_index(drop=True)
