import 'package:flutter/material.dart';

import '../models/recommend_response.dart';
import '../models/session.dart';
import '../widgets/song_card.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({
    super.key,
    required this.session,
    required this.result,
  });

  final RecommendationSession session;
  final RecommendResponse result;

  String get _modeLabel =>
      result.mode == 'change_mood' ? 'Change my mood' : 'Stay in my mood';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recommendations')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  Chip(label: Text('emotion: ${result.detectedEmotion}')),
                  Chip(label: Text(_modeLabel)),
                  Chip(label: Text('category: ${result.category}')),
                  Chip(
                    label: Text(
                      'targets: ${result.targetEmotions.join(', ')}',
                    ),
                  ),
                  if (session.confidence != null)
                    Chip(
                      label: Text(
                        '${(session.confidence! * 100).toStringAsFixed(0)}% confidence',
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '${result.count} song${result.count == 1 ? '' : 's'} '
                '(suggestions, not a mood treatment).',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              for (var i = 0; i < result.recommendations.length; i++)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: SongCard(
                    song: result.recommendations[i],
                    category: result.category,
                    index: i,
                  ),
                ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Change preferences'),
              ),
            ],
            ),
          ),
        ),
      ),
    );
  }
}
