import 'package:flutter/material.dart';

import '../models/session.dart';
import '../services/api_client.dart';
import '../services/api_exception.dart';
import 'results_screen.dart';

class PreferencesScreen extends StatefulWidget {
  const PreferencesScreen({
    super.key,
    required this.api,
    required this.session,
  });

  final ApiClient api;
  final RecommendationSession session;

  @override
  State<PreferencesScreen> createState() => _PreferencesScreenState();
}

class _PreferencesScreenState extends State<PreferencesScreen> {
  String _mode = 'stay_mood';
  String _category = 'classic';
  bool _loading = false;

  Future<void> _fetchRecommendations() async {
    setState(() => _loading = true);
    try {
      final result = await widget.api.recommend(
        emotion: widget.session.emotion,
        mode: _mode,
        category: _category,
      );
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ResultsScreen(
            session: widget.session,
            result: result,
          ),
        ),
      );
    } on ApiException catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.message)),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recommendation preferences')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
              Text(
                'Detected emotion',
                style: Theme.of(context).textTheme.labelLarge,
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  Chip(
                    label: Text(widget.session.emotion),
                    avatar: const Icon(Icons.mood),
                  ),
                  if (widget.session.confidence != null)
                    Chip(
                      label: Text(
                        '${(widget.session.confidence! * 100).toStringAsFixed(0)}% confidence',
                      ),
                    ),
                ],
              ),
              if (widget.session.isLowConfidence) ...[
                const SizedBox(height: 12),
                Text(
                  'The classifier is unsure about this sentence. '
                  'You can still get suggestions, but they may not match '
                  'how you feel.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
              if (widget.session.text.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  widget.session.text,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
              const SizedBox(height: 24),
              Text(
                'Recommendation mode',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              _OptionCard(
                value: 'stay_mood',
                groupValue: _mode,
                title: 'Stay in my mood',
                subtitle: 'Songs labeled with the same emotion.',
                icon: Icons.nights_stay,
                onSelect: (value) => setState(() => _mode = value),
              ),
              const SizedBox(height: 8),
              _OptionCard(
                value: 'change_mood',
                groupValue: _mode,
                title: 'Change my mood',
                subtitle: 'Songs from the mapped alternative emotion.',
                icon: Icons.wb_sunny,
                onSelect: (value) => setState(() => _mode = value),
              ),
              const SizedBox(height: 24),
              Text(
                'Music category',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              _OptionCard(
                value: 'classic',
                groupValue: _category,
                title: 'Classic',
                subtitle: 'Pop, R&B, soul, acoustic, and other non-rap songs.',
                icon: Icons.music_note,
                onSelect: (value) => setState(() => _category = value),
              ),
              const SizedBox(height: 8),
              _OptionCard(
                value: 'rap',
                groupValue: _category,
                title: 'Rap',
                subtitle: 'Rap and hip-hop only. Never mixed with Classic.',
                icon: Icons.graphic_eq,
                onSelect: (value) => setState(() => _category = value),
              ),
              const SizedBox(height: 32),
              FilledButton(
                onPressed: _loading ? null : _fetchRecommendations,
                child: _loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Get recommendations'),
              ),
            ],
            ),
          ),
        ),
      ),
    );
  }
}

class _OptionCard extends StatelessWidget {
  const _OptionCard({
    required this.value,
    required this.groupValue,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onSelect,
  });

  final String value;
  final String groupValue;
  final String title;
  final String subtitle;
  final IconData icon;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    final selected = value == groupValue;
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => onSelect(value),
        borderRadius: BorderRadius.circular(16),
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            color: selected
                ? scheme.primary.withValues(alpha: 0.16)
                : const Color(0xFF1A1E2B),
            border: Border.all(
              color: selected ? scheme.primary : Colors.white12,
              width: selected ? 2 : 1,
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(icon, color: selected ? scheme.primary : scheme.onSurface),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: Theme.of(context).textTheme.titleSmall),
                      const SizedBox(height: 2),
                      Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
                Icon(
                  selected ? Icons.check_circle : Icons.circle_outlined,
                  color: selected ? scheme.primary : scheme.onSurfaceVariant,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
