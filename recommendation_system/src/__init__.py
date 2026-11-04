"""EmoDJ music recommendation package.

This package does not load or call the teammate's emotion classifier.
It only consumes an emotion label (and later, optional confidence).
"""

from .recommendation import recommend_songs

__all__ = ["recommend_songs"]
