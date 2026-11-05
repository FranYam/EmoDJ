/// Values collected on Home, then reused on Preferences and Results.
class RecommendationSession {
  const RecommendationSession({
    required this.text,
    required this.emotion,
  });

  final String text;
  final String emotion;
}
