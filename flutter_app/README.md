# EmoDJ Flutter client (Phase 6)

Thin UI for the Python recommendation API. Song selection stays in FastAPI.

## Screens

1. **Home** — sentence + manual emotion (classifier comes in Phase 7).
2. **Preferences** — Stay / Change mood, Classic / Rap.
3. **Results** — title, artist, category, YouTube link. Back keeps the emotion.

## Run

Start the API from the EmoDJ repo root first:

```text
py -3 -m uvicorn backend_api.main:app --reload --host 127.0.0.1 --port 8000
```

Then, using the Flutter SDK on this machine:

```text
C:\Users\yameo\Desktop\Set of my project\Fluuter-src\flutter\bin\flutter.bat pub get
C:\Users\yameo\Desktop\Set of my project\Fluuter-src\flutter\bin\flutter.bat run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
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
