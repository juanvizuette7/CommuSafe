import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';

class AssistantEmptyState extends StatelessWidget {
  const AssistantEmptyState({super.key, required this.onSuggestionSelected});

  final ValueChanged<String> onSuggestionSelected;

  static const List<String> _sugerencias = <String>[
    '¿Cómo reporto un incidente?',
    'Horarios de áreas comunes',
    'Normas de convivencia',
    '¿Dónde veo mis avisos?',
  ];

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 620),
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Container(
                height: 88,
                width: 88,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: <Color>[theme.primary, theme.accent],
                  ),
                  boxShadow: <BoxShadow>[
                    BoxShadow(
                      color: theme.accent.withValues(alpha: 0.35),
                      blurRadius: 34,
                      offset: const Offset(0, 16),
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.smart_toy_rounded,
                  color: Colors.white,
                  size: 42,
                ),
              ),
              const SizedBox(height: 22),
              Text(
                'CommuBot',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Asistente IA de Remansos del Norte. Puedes preguntarme sobre incidentes, avisos, normas, emergencias, administración y uso de CommuSafe.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: const Color(0xFFCBD5E1),
                  height: 1.55,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 24),
              Wrap(
                alignment: WrapAlignment.center,
                spacing: 10,
                runSpacing: 10,
                children: _sugerencias.map((texto) {
                  return ActionChip(
                    onPressed: () => onSuggestionSelected(texto),
                    avatar: Icon(
                      Icons.auto_awesome_rounded,
                      size: 16,
                      color: theme.accent,
                    ),
                    label: Text(texto),
                    backgroundColor: Color.lerp(
                      const Color(0xFF172033),
                      theme.secondary,
                      0.22,
                    ),
                    side: BorderSide(
                      color: theme.accent.withValues(alpha: 0.28),
                    ),
                    labelStyle: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  );
                }).toList(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
