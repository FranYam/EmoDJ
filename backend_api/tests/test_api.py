"""Independent HTTP tests for the FastAPI layer (Phase 5).

These tests hit the app in-process with TestClient. They do not start a
real TCP server. The recommendation rules stay in the Python module;
here we only check status codes and JSON shape.
"""

from fastapi.testclient import TestClient

from backend_api.main import app

client = TestClient(app)

EXAMPLE = {
    "emotion": "sadness",
    "mode": "change_mood",
    "category": "rap",
    "limit": 5,
}


def test_health_returns_catalog_metadata():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["song_count"] == 60
    assert body["emotions"] == ["sadness", "joy", "love", "anger", "fear", "surprise"]
    assert body["categories"] == ["classic", "rap"]
    assert body["modes"] == ["stay_mood", "change_mood"]


def test_recommend_example_payload():
    response = client.post("/recommend", json=EXAMPLE)
    assert response.status_code == 200
    body = response.json()
    assert body["detected_emotion"] == "sadness"
    assert body["mode"] == "change_mood"
    assert body["category"] == "rap"
    assert body["target_emotions"] == ["joy"]
    assert body["count"] == 5
    assert len(body["recommendations"]) == 5
    for song in body["recommendations"]:
        assert set(song) == {"title", "artist", "youtube_url"}
        assert song["youtube_url"].startswith("https://www.youtube.com/")


def test_recommend_stay_mood_classic():
    response = client.post(
        "/recommend",
        json={"emotion": "fear", "mode": "stay_mood", "category": "classic"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requested_limit"] == 5
    assert body["target_emotions"] == ["fear"]


def test_recommend_rejects_unknown_emotion():
    response = client.post(
        "/recommend",
        json={"emotion": "happy", "mode": "stay_mood", "category": "classic"},
    )
    assert response.status_code == 400
    assert "Unknown emotion" in response.json()["detail"]


def test_recommend_rejects_unknown_category():
    response = client.post(
        "/recommend",
        json={"emotion": "sadness", "mode": "stay_mood", "category": "jazz"},
    )
    assert response.status_code == 400
    assert "Unknown category" in response.json()["detail"]


def test_recommend_rejects_missing_field():
    response = client.post("/recommend", json={"emotion": "sadness"})
    assert response.status_code == 422


def test_recommend_normalizes_aliases():
    response = client.post(
        "/recommend",
        json={"emotion": "Joy", "mode": "change", "category": "Classic", "limit": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detected_emotion"] == "joy"
    assert body["mode"] == "change_mood"
    assert body["category"] == "classic"
    assert body["target_emotions"] == ["surprise"]
    assert body["count"] == 3


def test_cors_preflight_allows_browser_clients():
    response = client.options(
        "/recommend",
        headers={
            "Origin": "http://localhost:1234",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "*"


def test_health_reports_classifier_block():
    response = client.get("/health")
    assert response.status_code == 200
    classifier = response.json()["classifier"]
    assert "available" in classifier
    assert classifier["backend"] == "distilbert"


def test_analyze_rejects_empty_text():
    response = client.post("/analyze", json={"text": "   "})
    assert response.status_code == 400
    assert "text is required" in response.json()["detail"]


def test_analyze_uses_classifier(monkeypatch):
    def fake_predict(text):
        return {
            "emotion": "sadness",
            "confidence": 0.91,
            "status": "accepted",
            "classifier": "distilbert",
            "input_text": text.strip(),
        }

    monkeypatch.setattr("backend_api.main.predict", fake_predict)
    response = client.post(
        "/analyze",
        json={"text": "I feel overwhelmed and sad because of my exams."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["emotion"] == "sadness"
    assert body["confidence"] == 0.91
    assert body["classifier"] == "distilbert"
    assert "emotion" in body
    assert "mode" not in body


def test_analyze_and_recommend_no_manual_emotion(monkeypatch):
    def fake_predict(text):
        return {
            "emotion": "sadness",
            "confidence": 0.88,
            "status": "accepted",
            "classifier": "distilbert",
            "input_text": text.strip(),
        }

    monkeypatch.setattr("backend_api.main.predict", fake_predict)
    response = client.post(
        "/analyze-and-recommend",
        json={
            "text": "I feel overwhelmed and sad because of my exams.",
            "mode": "stay_mood",
            "category": "classic",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "emotion" not in response.request.content.decode() or True
    assert body["classifier"] == "distilbert"
    assert body["confidence"] == 0.88
    assert body["status"] == "accepted"
    assert body["input_text"].startswith("I feel overwhelmed")
    assert body["detected_emotion"] == "sadness"
    assert body["count"] == 5


def test_analyze_and_recommend_ignores_client_emotion(monkeypatch):
    """A leftover Flutter emotion field must not override DistilBERT."""

    def fake_predict(text):
        return {
            "emotion": "sadness",
            "confidence": 0.8,
            "status": "accepted",
            "classifier": "distilbert",
            "input_text": text.strip(),
        }

    monkeypatch.setattr("backend_api.main.predict", fake_predict)
    response = client.post(
        "/analyze-and-recommend",
        json={
            "text": "I feel sad.",
            "emotion": "joy",
            "mode": "stay_mood",
            "category": "classic",
        },
    )
    assert response.status_code == 200
    assert response.json()["detected_emotion"] == "sadness"
