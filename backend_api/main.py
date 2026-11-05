"""FastAPI entry point for Flutter.

Flutter cannot import Python. HTTP is the boundary.

  Flutter  →  POST /analyze  →  DistilBERT  →  emotion
           →  POST /recommend →  recommendation_system  →  songs

Or one call: POST /analyze-and-recommend.

Run from the EmoDJ repo root:
  py -3 -m uvicorn backend_api.main:app --reload --host 127.0.0.1 --port 8000
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

from emotion_classifier.classifier import ClassifierError, classifier_status, predict
from src.config import CATEGORIES, DEFAULT_LIMIT, EMOTIONS, MAX_LIMIT, MIN_LIMIT, MODES
from src.data_loader import load_songs
from src.recommendation import RecommendationError, recommend_songs

app = FastAPI(
    title="EmoDJ Recommendation API",
    description=(
        "Classifies English text with the teammate DistilBERT model, "
        "then recommends songs from a labeled CSV."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    """Body for POST /recommend after an emotion is already known."""

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


class AnalyzeRequest(BaseModel):
    text: str = Field(..., examples=["I feel overwhelmed and sad because of my exams."])


class AnalyzeResponse(BaseModel):
    input_text: str
    emotion: str
    confidence: float
    status: str
    classifier: str


class AnalyzeRecommendRequest(BaseModel):
    """Full pipeline: sentence in, songs out. Emotion is never sent by the client."""

    text: str = Field(..., examples=["I feel overwhelmed and sad because of my exams."])
    mode: str
    category: str
    limit: int | None = None


class AnalyzeRecommendResponse(RecommendResponse):
    input_text: str
    confidence: float
    classifier: str
    status: str


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


def _predict_or_http_error(text: str) -> dict[str, Any]:
    try:
        return predict(text)
    except ClassifierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness check plus catalog and classifier file status."""
    catalog = load_songs()
    return {
        "status": "ok",
        "song_count": int(len(catalog)),
        "emotions": list(EMOTIONS),
        "categories": list(CATEGORIES),
        "modes": list(MODES),
        "default_limit": DEFAULT_LIMIT,
        "limit_range": [MIN_LIMIT, MAX_LIMIT],
        "classifier": classifier_status(),
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest) -> dict[str, Any]:
    """Classify text only. Flutter uses this on the Home Analyze button."""
    return _predict_or_http_error(body.text)


@app.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendRequest) -> dict[str, Any]:
    """Recommend songs from a known emotion (after /analyze, or for tests)."""
    return _recommend_or_http_error(body.emotion, body.mode, body.category, body.limit)


@app.post("/analyze-and-recommend", response_model=AnalyzeRecommendResponse)
def analyze_and_recommend(body: AnalyzeRecommendRequest) -> dict[str, Any]:
    """Classify the sentence, then recommend. Same recommend_songs() as /recommend."""
    prediction = _predict_or_http_error(body.text)
    payload = _recommend_or_http_error(
        prediction["emotion"], body.mode, body.category, body.limit
    )
    payload["input_text"] = prediction["input_text"]
    payload["confidence"] = prediction["confidence"]
    payload["classifier"] = prediction["classifier"]
    payload["status"] = prediction["status"]
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend_api.main:app", host="127.0.0.1", port=8000, reload=True)
