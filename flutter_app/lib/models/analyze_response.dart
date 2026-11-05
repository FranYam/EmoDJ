class AnalyzeResponse {
  const AnalyzeResponse({
    required this.inputText,
    required this.emotion,
    required this.confidence,
    required this.status,
    required this.classifier,
  });

  final String inputText;
  final String emotion;
  final double confidence;
  final String status;
  final String classifier;

  factory AnalyzeResponse.fromJson(Map<String, dynamic> json) {
    return AnalyzeResponse(
      inputText: json['input_text'] as String? ?? '',
      emotion: json['emotion'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      status: json['status'] as String? ?? '',
      classifier: json['classifier'] as String? ?? 'distilbert',
    );
  }
}
