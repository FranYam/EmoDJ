import 'dart:convert';

import 'package:emodj_app/main.dart';
import 'package:emodj_app/services/api_client.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

ApiClient _mockApi() {
  return ApiClient(
    httpClient: MockClient((request) async {
      if (request.url.path == '/health') {
        return http.Response(
          jsonEncode({
            'status': 'ok',
            'song_count': 60,
            'classifier': {'available': true, 'backend': 'distilbert'},
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path == '/analyze') {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        expect(body.containsKey('emotion'), isFalse);
        return http.Response(
          jsonEncode({
            'input_text': body['text'],
            'emotion': 'sadness',
            'confidence': 0.91,
            'status': 'accepted',
            'classifier': 'distilbert',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response(
        jsonEncode({
          'detected_emotion': 'sadness',
          'mode': 'stay_mood',
          'category': 'classic',
          'target_emotions': ['sadness'],
          'requested_limit': 5,
          'count': 1,
          'recommendations': [
            {
              'title': 'Someone Like You',
              'artist': 'Adele',
              'youtube_url': 'https://www.youtube.com/watch?v=hLQl3WQQoQ0',
            },
          ],
        }),
        200,
        headers: {'content-type': 'application/json'},
      );
    }),
  );
}

void main() {
  Future<void> _pumpApp(WidgetTester tester) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(EmoDjApp(api: _mockApi()));
    await tester.pumpAndSettle();
  }

  testWidgets('home screen shows EmoDJ and Analyze', (tester) async {
    await _pumpApp(tester);

    expect(find.text('EmoDJ'), findsOneWidget);
    expect(find.text('Analyze'), findsOneWidget);
    expect(find.textContaining('API connected'), findsOneWidget);
    expect(find.text('sadness'), findsNothing);
  });

  testWidgets('Analyze stays disabled until the user types a sentence',
      (tester) async {
    await _pumpApp(tester);

    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
      isNull,
    );

    await tester.enterText(
      find.byType(TextField),
      'I feel overwhelmed and sad because of my exams.',
    );
    await tester.pump();

    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
      isNotNull,
    );
  });

  testWidgets('full flow: home → analyze → preferences → results → back',
      (tester) async {
    await _pumpApp(tester);

    await tester.enterText(
      find.byType(TextField),
      'I feel overwhelmed and sad because of my exams.',
    );
    await tester.pump();
    await tester.tap(find.text('Analyze'));
    await tester.pumpAndSettle();

    expect(find.text('Recommendation preferences'), findsOneWidget);
    expect(find.text('sadness'), findsOneWidget);
    expect(find.text('91% confidence'), findsOneWidget);
    expect(find.text('Stay in my mood'), findsOneWidget);
    expect(find.text('Classic'), findsOneWidget);

    await tester.tap(find.text('Get recommendations'));
    await tester.pumpAndSettle();

    expect(find.text('Recommendations'), findsOneWidget);
    expect(find.text('Someone Like You'), findsOneWidget);
    expect(find.text('Adele'), findsOneWidget);
    expect(find.text('YouTube'), findsOneWidget);
    expect(find.textContaining('category: classic'), findsOneWidget);

    await tester.tap(find.text('Change preferences'));
    await tester.pumpAndSettle();

    expect(find.text('Recommendation preferences'), findsOneWidget);
    expect(find.text('Someone Like You'), findsNothing);
  });
}
