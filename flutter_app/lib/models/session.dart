/// Values collected on Home after DistilBERT, then reused on later screens.
class RecommendationSession {
  const RecommendationSession({
    required this.text,
    required this.emotion,
    this.confidence,
    this.classifierStatus,
    this.classifier = 'distilbert',
  });

  final String text;
  final String emotion;
  final double? confidence;
  final String? classifierStatus;
  final String classifier;

  bool get isLowConfidence => classifierStatus == 'low_confidence';
}
