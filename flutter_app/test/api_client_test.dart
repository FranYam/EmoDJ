import 'dart:convert';

import 'package:emodj_app/models/recommend_response.dart';
import 'package:emodj_app/services/api_client.dart';
import 'package:emodj_app/services/api_exception.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('recommend parses FastAPI JSON', () async {
    final client = ApiClient(
      baseUrl: 'http://127.0.0.1:8000',
      httpClient: MockClient((request) async {
        expect(request.url.path, '/recommend');
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body['emotion'], 'sadness');
        expect(body['mode'], 'change_mood');
        expect(body['category'], 'rap');
        return http.Response(
          jsonEncode({
            'detected_emotion': 'sadness',
            'mode': 'change_mood',
            'category': 'rap',
            'target_emotions': ['joy'],
            'requested_limit': 5,
            'count': 1,
            'recommendations': [
              {
                'title': 'Example Song',
                'artist': 'Example Artist',
                'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
              },
            ],
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );

    final result = await client.recommend(
      emotion: 'sadness',
      mode: 'change_mood',
      category: 'rap',
    );

    expect(result, isA<RecommendResponse>());
    expect(result.count, 1);
    expect(result.recommendations.first.title, 'Example Song');
    expect(result.targetEmotions, ['joy']);
  });

  test('recommend surfaces API detail on 400', () async {
    final client = ApiClient(
      baseUrl: 'http://127.0.0.1:8000',
      httpClient: MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': "Unknown emotion 'happy'."}),
          400,
          headers: {'content-type': 'application/json'},
        );
      }),
    );

    expect(
      () => client.recommend(
        emotion: 'happy',
        mode: 'stay_mood',
        category: 'classic',
      ),
      throwsA(
        isA<ApiException>().having(
          (error) => error.message,
          'message',
          contains('Unknown emotion'),
        ),
      ),
    );
  });
}
