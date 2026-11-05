# Emotion classifier contract

The recommendation system never trains or edits the NLP model. It only
consumes a prediction.

## Checkpoint

- Source: `D:\Desktop\EmoDJ\Model\EmoDJ_DistilBERT` (teammate DistilBERT).
- Override with environment variable `EMODJ_MODEL_PATH`.
- Optional copy: `emotion_classifier/weights/EmoDJ_DistilBERT`.

The teammate notebook labels are capitalized (`Sadness`, `Joy`, ...).
The wrapper lowercases them before calling `recommend_songs`.

## Classifier → recommendation

```json
{
  "emotion": "sadness",
  "confidence": 0.92
}
```

- `emotion`: required, one of `sadness`, `joy`, `love`, `anger`, `fear`, `surprise`.
- `confidence`: float in `[0, 1]` (the notebook used a percentage; the API does not).

## HTTP

- `POST /analyze` — `{ "text": "..." }` → emotion + confidence.
- `POST /analyze-and-recommend` — `{ "text", "mode", "category", "limit" }` →
  classify then recommend. No manual `emotion` field.
- `POST /recommend` — still accepts a known emotion for tests and debugging.
  The Flutter app no longer sends a user-picked emotion.

If confidence is below 0.50 the API still recommends songs, but marks
`status` as `low_confidence` so the UI can warn the user.
