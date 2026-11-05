"""EmoDJ music recommendation package.

This package does not load or train the teammate's emotion classifier.
It only consumes a lowercase emotion string produced by emotion_classifier.
It only consumes an emotion label (and later, optional confidence).
"""

from .recommendation import recommend_songs

__all__ = ["recommend_songs"]
