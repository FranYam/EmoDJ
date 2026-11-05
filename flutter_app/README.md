# EmoDJ Flutter client (Phase 6)

Thin UI for the Python recommendation API. Song selection stays in FastAPI.

## Screens

1. **Home** — English sentence only. Analyze calls DistilBERT (`POST /analyze`). There is no manual emotion picker.
2. **Preferences** — shows the detected emotion and confidence, then Stay / Change mood and Classic / Rap.
3. **Results** — title, artist, category, YouTube link. Back keeps the detected emotion.

## Run

Start the API from the EmoDJ repo root first:

```text
py -3 -m uvicorn backend_api.main:app --reload --host 127.0.0.1 --port 8000
```

Then, using the Flutter SDK on this machine:

```text
C:\src\flutter\bin\flutter.bat pub get
C:\src\flutter\bin\flutter.bat run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Windows desktop:

```text
...\flutter.bat run -d windows --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Android emulator cannot use `localhost`. Use `http://10.0.2.2:8000`.

## Tests

```text
...\flutter.bat test
```
