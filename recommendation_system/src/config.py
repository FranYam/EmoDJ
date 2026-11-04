"""Allowed values and defaults for the recommendation module.

Keeping these in one file means Flutter, FastAPI, and tests all share the
same spelling of emotions, categories, and modes. The teammate's classifier
must emit these exact emotion strings.
"""

from pathlib import Path

EMOTIONS = ("sadness", "joy", "love", "anger", "fear", "surprise")
CATEGORIES = ("classic", "rap")
MODES = ("stay_mood", "change_mood")

DEFAULT_LIMIT = 5
MIN_LIMIT = 1
MAX_LIMIT = 20

# recommendation_system/dataset/songs.csv, independent of the process cwd
DATASET_PATH = Path(__file__).resolve().parent.parent / "dataset" / "songs.csv"

REQUIRED_COLUMNS = ("emotion", "category", "title", "artist", "youtube_url")
