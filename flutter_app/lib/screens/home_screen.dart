import 'package:flutter/material.dart';

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
  String? _healthMessage;
  bool _apiOk = false;
  bool _checkingHealth = true;
  bool _analyzing = false;
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    _textController.addListener(() {
      final hasText = _textController.text.trim().isNotEmpty;
      if (hasText != _hasText) {
        setState(() => _hasText = hasText);
      }
    });
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
      final classifier = body['classifier'];
      var extra = '';
      if (classifier is Map && classifier['available'] == true) {
        extra = ' · DistilBERT ready';
      } else if (classifier is Map && classifier['available'] == false) {
        extra = ' · emotion model missing';
      }
      setState(() {
        _apiOk = true;
        _healthMessage =
            'API connected · ${body['song_count']} songs in catalog$extra';
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

  Future<void> _analyze() async {
    final text = _textController.text.trim();
    if (text.isEmpty || _analyzing) {
      return;
    }
    setState(() => _analyzing = true);
    try {
      final prediction = await widget.api.analyze(text);
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => PreferencesScreen(
            api: widget.api,
            session: RecommendationSession(
              text: prediction.inputText,
              emotion: prediction.emotion,
              confidence: prediction.confidence,
              classifierStatus: prediction.status,
              classifier: prediction.classifier,
            ),
          ),
        ),
      );
    } on ApiException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.message)),
      );
    } finally {
      if (mounted) setState(() => _analyzing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final canAnalyze = _hasText && !_analyzing;
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
                  'Write how you feel in English. DistilBERT detects the '
                  'emotion, then you choose whether to stay in that mood or '
                  'explore a different atmosphere.',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 24),
                TextField(
                  controller: _textController,
                  minLines: 3,
                  maxLines: 6,
                  enabled: !_analyzing,
                  decoration: const InputDecoration(
                    labelText: 'How do you feel?',
                    hintText:
                        'I feel overwhelmed and sad because of my exams.',
                    alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: canAnalyze ? _analyze : null,
                  child: _analyzing
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Analyze'),
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
