import 'song.dart';

class RecommendResponse {
  const RecommendResponse({
    required this.detectedEmotion,
    required this.mode,
    required this.category,
    required this.targetEmotions,
    required this.requestedLimit,
    required this.count,
    required this.recommendations,
  });

  final String detectedEmotion;
  final String mode;
  final String category;
  final List<String> targetEmotions;
  final int requestedLimit;
  final int count;
  final List<Song> recommendations;

  factory RecommendResponse.fromJson(Map<String, dynamic> json) {
    final rawSongs = json['recommendations'] as List<dynamic>? ?? [];
    return RecommendResponse(
      detectedEmotion: json['detected_emotion'] as String? ?? '',
      mode: json['mode'] as String? ?? '',
      category: json['category'] as String? ?? '',
      targetEmotions: List<String>.from(json['target_emotions'] as List? ?? []),
      requestedLimit: json['requested_limit'] as int? ?? rawSongs.length,
      count: json['count'] as int? ?? rawSongs.length,
      recommendations: rawSongs
          .map((item) => Song.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
