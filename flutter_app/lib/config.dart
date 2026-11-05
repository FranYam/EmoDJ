/// Runtime settings for talking to FastAPI.
///
/// Override at launch, for example:
///   flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
///
/// Android emulator cannot use localhost; use http://10.0.2.2:8000 instead.
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  static const int defaultLimit = 5;

  static const List<String> emotions = [
    'sadness',
    'joy',
    'love',
    'anger',
    'fear',
    'surprise',
  ];
}
