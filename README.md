# EmoDJ
EmoDJ is an AI-powered music system that analyzes your text with NLP and Deep Learning to detect your current emotion. It then recommends songs that match your mood or help you shift to a better state, creating a truly personalized, interactive, smart and intelligent musical experience for you

## Phase 7 — classifier integration

The Flutter app no longer lets the user pick an emotion. The teammate DistilBERT checkpoint is loaded by `emotion_classifier/classifier.py`.

Default checkpoint path: `D:\Desktop\EmoDJ\Model\EmoDJ_DistilBERT`  
Override: `EMODJ_MODEL_PATH`

Pipeline:

1. User types an English sentence.
2. `POST /analyze` → `{ emotion, confidence }` (labels lowercased to match the recommender).
3. User chooses Stay/Change mood and Classic/Rap.
4. `POST /recommend` uses that emotion. Song rules are unchanged.

Install Python deps from `recommendation_system/requirements.txt` (includes `torch` and `transformers`).
