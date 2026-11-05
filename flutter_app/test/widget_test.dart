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
          jsonEncode({'status': 'ok', 'song_count': 60}),
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
  });

  testWidgets('Analyze stays disabled until an emotion is selected',
      (tester) async {
    await _pumpApp(tester);

    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
      isNull,
    );

    await tester.tap(find.text('sadness'));
    await tester.pump();

    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
      isNotNull,
    );
  });

  testWidgets('full flow: home → preferences → results → back', (tester) async {
    await _pumpApp(tester);

    await tester.enterText(
      find.byType(TextField),
      'I feel overwhelmed and sad because of my exams.',
    );
    await tester.tap(find.text('sadness'));
    await tester.pump();
    await tester.tap(find.text('Analyze'));
    await tester.pumpAndSettle();

    expect(find.text('Recommendation preferences'), findsOneWidget);
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
