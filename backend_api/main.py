"""FastAPI entry point for Flutter (Phase 5).

Why an API exists:
  Flutter (Dart) cannot import the Python recommender. HTTP is the boundary.
  All song selection still happens in recommendation_system.src.recommendation.

Run from the EmoDJ repo root:
  py -3 -m uvicorn backend_api.main:app --reload --host 127.0.0.1 --port 8000

Android emulator later uses http://10.0.2.2:8000 instead of localhost.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REC_SYS = _REPO_ROOT / "recommendation_system"
for _path in (_REPO_ROOT, _REC_SYS):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from src.config import CATEGORIES, DEFAULT_LIMIT, EMOTIONS, MAX_LIMIT, MIN_LIMIT, MODES
from src.data_loader import load_songs
from src.recommendation import RecommendationError, recommend_songs

app = FastAPI(
    title="EmoDJ Recommendation API",
    description=(
        "Rule-based song recommendations from a labeled CSV. "
        "Does not run the teammate emotion classifier (Phase 7)."
    ),
    version="0.1.0",
)

# Flutter web / desktop will call this API from another origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    """Body for POST /recommend. Strings are validated by the Python module."""

    emotion: str = Field(..., examples=["sadness"])
    mode: str = Field(..., examples=["stay_mood"])
    category: str = Field(..., examples=["classic"])
    limit: int | None = Field(default=None, examples=[5])


class SongRecord(BaseModel):
    title: str
    artist: str
    youtube_url: str


class RecommendResponse(BaseModel):
    detected_emotion: str
    mode: str
    category: str
    target_emotions: list[str]
    requested_limit: int
    count: int
    recommendations: list[SongRecord]


class AnalyzeRecommendRequest(BaseModel):
    """Prototype stand-in until the classifier exists.

    `text` is accepted so Flutter can send the sentence now. The mock
    ignores NLP and uses `emotion` (manual selection) with confidence 1.0.
    """

    text: str = Field(..., examples=["I feel overwhelmed and sad because of my exams."])
    mode: str
    category: str
    limit: int | None = None
    emotion: str | None = Field(
        default=None,
        description="Required for the mock classifier. Later filled by the NLP model.",
        examples=["sadness"],
    )


class AnalyzeRecommendResponse(RecommendResponse):
    input_text: str
    confidence: float
    classifier: str


def _recommend_or_http_error(
    emotion: str,
    mode: str,
    category: str,
    limit: int | None,
) -> dict[str, Any]:
    try:
        return recommend_songs(emotion, mode, category, limit=limit)
    except RecommendationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness check plus a cheap catalog load so a missing CSV is visible."""
    catalog = load_songs()
    return {
        "status": "ok",
        "song_count": int(len(catalog)),
        "emotions": list(EMOTIONS),
        "categories": list(CATEGORIES),
        "modes": list(MODES),
        "default_limit": DEFAULT_LIMIT,
        "limit_range": [MIN_LIMIT, MAX_LIMIT],
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendRequest) -> dict[str, Any]:
    """Recommend songs from a known emotion. This is the stable Flutter contract."""
    return _recommend_or_http_error(body.emotion, body.mode, body.category, body.limit)


@app.post("/analyze-and-recommend", response_model=AnalyzeRecommendResponse)
def analyze_and_recommend(body: AnalyzeRecommendRequest) -> dict[str, Any]:
    """Mock pipeline: sentence is stored, emotion must be supplied manually.

    Phase 7 will replace the mock with teammate.predict(text) and keep
    the recommend_songs call unchanged.
    """
    if body.emotion is None or not str(body.emotion).strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "Mock classifier requires 'emotion' until the NLP model is integrated. "
                "Send the same six labels as /recommend."
            ),
        )
    payload = _recommend_or_http_error(body.emotion, body.mode, body.category, body.limit)
    payload["input_text"] = body.text
    payload["confidence"] = 1.0
    payload["classifier"] = "mock"
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend_api.main:app", host="127.0.0.1", port=8000, reload=True)
