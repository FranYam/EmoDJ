"""Unit tests for the DistilBERT adapter (no GPU required)."""

from emotion_classifier.classifier import (
    ClassifierError,
    _label_to_contract,
    classifier_status,
    predict,
)
import pytest


def test_label_adapter_accepts_teammate_capitalization():
    assert _label_to_contract("Sadness") == "sadness"
    assert _label_to_contract("JOY") == "joy"


def test_label_adapter_rejects_unknown_class():
    with pytest.raises(ClassifierError, match="unsupported emotion"):
        _label_to_contract("happy")


def test_predict_rejects_blank_text():
    with pytest.raises(ClassifierError, match="text is required"):
        predict("   ")


def test_status_reports_checkpoint_or_clear_error():
    status = classifier_status()
    assert "available" in status
    assert status["backend"] == "distilbert"
    if status["available"]:
        assert status["path"]
        assert status["detail"] is None
    else:
        assert "EMODJ_MODEL_PATH" in (status["detail"] or "")


@pytest.mark.skipif(
    not classifier_status()["available"],
    reason="DistilBERT checkpoint not found on this machine",
)
def test_live_model_predicts_sadness_example():
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    result = predict("I feel overwhelmed and sad because of my exams.")
    assert result["emotion"] in {
        "sadness",
        "joy",
        "love",
        "anger",
        "fear",
        "surprise",
    }
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["classifier"] == "distilbert"
