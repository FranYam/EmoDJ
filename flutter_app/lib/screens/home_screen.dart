import 'package:flutter/material.dart';

import '../config.dart';
import '../models/session.dart';
import '../services/api_client.dart';
import '../services/api_exception.dart';
import 'preferences_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _textController = TextEditingController();
  String? _emotion;
  String? _healthMessage;
  bool _apiOk = false;
  bool _checkingHealth = true;

  @override
  void initState() {
    super.initState();
    _refreshHealth();
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _refreshHealth() async {
    setState(() {
      _checkingHealth = true;
    });
    try {
      final body = await widget.api.health();
      if (!mounted) return;
      setState(() {
        _apiOk = true;
        _healthMessage =
            'API connected · ${body['song_count']} songs in catalog';
      });
    } on ApiException catch (error) {
      if (!mounted) return;
      setState(() {
        _apiOk = false;
        _healthMessage = error.message;
      });
    } finally {
      if (mounted) {
        setState(() {
          _checkingHealth = false;
        });
      }
    }
  }

  void _goToPreferences() {
    if (_emotion == null) {
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PreferencesScreen(
          api: widget.api,
          session: RecommendationSession(
            text: _textController.text.trim(),
            emotion: _emotion!,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: CircleAvatar(
                    radius: 28,
                    backgroundColor: scheme.primaryContainer,
                    child: Icon(
                      Icons.headphones,
                      color: scheme.onPrimaryContainer,
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'EmoDJ',
                  style: Theme.of(context).textTheme.displaySmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Write how you feel in English, then pick an emotion. '
                  'The app recommends songs that stay with that mood or '
                  'offer a different atmosphere.',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 24),
                TextField(
                  controller: _textController,
                  minLines: 3,
                  maxLines: 6,
                  decoration: const InputDecoration(
                    labelText: 'How do you feel?',
                    hintText:
                        'I feel overwhelmed and sad because of my exams.',
                    alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  'Emotion (manual, for testing)',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  'Required until the teammate NLP model is connected. '
                  'The sentence is stored but not classified yet.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final emotion in AppConfig.emotions)
                      ChoiceChip(
                        label: Text(emotion),
                        selected: _emotion == emotion,
                        onSelected: (_) => setState(() => _emotion = emotion),
                      ),
                  ],
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _emotion == null ? null : _goToPreferences,
                  child: const Text('Analyze'),
                ),
                const SizedBox(height: 16),
                if (_checkingHealth)
                  const LinearProgressIndicator()
                else
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(
                      _apiOk ? Icons.check_circle : Icons.error_outline,
                      color: _apiOk ? Colors.greenAccent : Colors.orangeAccent,
                    ),
                    title: Text(_healthMessage ?? ''),
                    trailing: IconButton(
                      onPressed: _refreshHealth,
                      icon: const Icon(Icons.refresh),
                      tooltip: 'Retry API check',
                    ),
                  ),
              ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
