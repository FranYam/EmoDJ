"""Load the teammate DistilBERT checkpoint and predict one emotion.

The notebook saved Hugging Face files under Model/EmoDJ_DistilBERT and
returned capitalized labels plus confidence as a percentage. This module
adapts that output to the Phase 0 contract:

    {"emotion": "sadness", "confidence": 0.92}

so recommend_songs() never needs to know about transformers.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

# Same six strings as the recommender. Kept here so this package does not
# import recommendation internals.
EMOTIONS = ("sadness", "joy", "love", "anger", "fear", "surprise")

LOW_CONFIDENCE_THRESHOLD = 0.50
MAX_LENGTH = 128

_DEFAULT_DESKTOP_MODEL = Path(r"D:\Desktop\EmoDJ\Model\EmoDJ_DistilBERT")
_REPO_WEIGHTS = Path(__file__).resolve().parent / "weights" / "EmoDJ_DistilBERT"

_lock = threading.Lock()
_tokenizer = None
_model = None
_loaded_path: Path | None = None


class ClassifierError(ValueError):
    """Missing text, missing checkpoint, or a label the recommender cannot use."""


def resolve_model_path() -> Path:
    """Prefer EMODJ_MODEL_PATH, then in-repo weights, then the Desktop checkpoint."""
    candidates: list[Path] = []
    env_path = os.environ.get("EMODJ_MODEL_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(_REPO_WEIGHTS)
    candidates.append(_DEFAULT_DESKTOP_MODEL)

    for path in candidates:
        if _looks_like_checkpoint(path):
            return path

    searched = ", ".join(str(path) for path in candidates)
    raise ClassifierError(
        "Emotion model not found. Set EMODJ_MODEL_PATH to the folder that "
        "contains config.json and model.safetensors. Looked at: "
        f"{searched}."
    )


def _looks_like_checkpoint(path: Path) -> bool:
    if not (path / "config.json").is_file():
        return False
    return (path / "model.safetensors").is_file() or (path / "pytorch_model.bin").is_file()


def classifier_status() -> dict[str, Any]:
    """File check only — does not load PyTorch weights."""
    try:
        path = resolve_model_path()
        available = True
        detail = str(path)
    except ClassifierError as exc:
        path = None
        available = False
        detail = str(exc)
    return {
        "available": available,
        "loaded": _model is not None,
        "path": str(path) if path else None,
        "backend": "distilbert",
        "detail": detail if not available else None,
        "low_confidence_threshold": LOW_CONFIDENCE_THRESHOLD,
    }


def _load_model() -> tuple[Any, Any]:
    global _tokenizer, _model, _loaded_path
    if _model is not None and _tokenizer is not None:
        return _tokenizer, _model

    with _lock:
        if _model is not None and _tokenizer is not None:
            return _tokenizer, _model

        path = resolve_model_path()
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise ClassifierError(
                "PyTorch and transformers are required to run the emotion model. "
                "Install them from recommendation_system/requirements.txt."
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            path, local_files_only=True
        )
        model.eval()
        _tokenizer = tokenizer
        _model = model
        _loaded_path = path
        # Keep a reference so tests can inspect the device later if needed.
        _ = torch
        return _tokenizer, _model


def _label_to_contract(raw_label: object) -> str:
    emotion = str(raw_label).strip().lower()
    if emotion not in EMOTIONS:
        allowed = ", ".join(EMOTIONS)
        raise ClassifierError(
            f"Classifier returned unsupported emotion {raw_label!r}. "
            f"Allowed: {allowed}."
        )
    return emotion


def predict(text: object) -> dict[str, Any]:
    """Run DistilBERT on one English sentence.

    Returns the stable contract plus UI extras (status, classifier name).
    Confidence is always in [0, 1], not a percentage.
    """
    if not isinstance(text, str) or not text.strip():
        raise ClassifierError("text is required and must be a non-empty string.")

    cleaned = text.strip()
    tokenizer, model = _load_model()

    import torch

    inputs = tokenizer(
        cleaned,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
    )
    with torch.no_grad():
        outputs = model(**inputs)

    probabilities = torch.softmax(outputs.logits, dim=1)[0]
    predicted_class = int(torch.argmax(probabilities).item())
    confidence = float(probabilities[predicted_class].item())

    id2label = model.config.id2label
    raw_label = id2label[predicted_class]
    emotion = _label_to_contract(raw_label)
    status = "low_confidence" if confidence < LOW_CONFIDENCE_THRESHOLD else "accepted"

    return {
        "emotion": emotion,
        "confidence": round(confidence, 4),
        "status": status,
        "classifier": "distilbert",
        "input_text": cleaned,
    }
