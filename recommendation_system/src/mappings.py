"""Stay-in-mood and change-mood emotion targets.

CSV `emotion` is a curator tag used for retrieval. It is not a clinical
claim: we suggest songs, we do not treat mood.

Change-mood uses an ordered list: the first target is preferred. Later
targets are used only if the preferred bin has no usable songs for the
chosen category (see recommend_songs).
"""

from .config import EMOTIONS

# Stay: play from the same labeled bin as the detected emotion.
STAY_MOOD_MAP = {emotion: [emotion] for emotion in EMOTIONS}

# Change: leave the detected bin. Mapping A from Phase 0:
# joy -> surprise so Mode B is not a reshuffle of the same 5 joy tracks.
# anger -> joy/surprise, not fear/sadness (those bins are not a calm catalog).
CHANGE_MOOD_MAP = {
    "sadness": ["joy", "surprise"],
    "joy": ["surprise", "love"],
    "love": ["joy", "surprise"],
    "anger": ["joy", "surprise"],
    "fear": ["joy", "love"],
    "surprise": ["joy", "love"],
}


def get_target_emotions(emotion: str, mode: str) -> list[str]:
    """Return ordered target emotion labels for a validated emotion and mode."""
    if mode == "stay_mood":
        return list(STAY_MOOD_MAP[emotion])
    return list(CHANGE_MOOD_MAP[emotion])
