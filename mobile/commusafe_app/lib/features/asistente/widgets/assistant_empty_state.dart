import 'package:flutter/material.dart';

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
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 620),
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Container(
                height: 86,
                width: 86,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: const LinearGradient(
                    colors: <Color>[Color(0xFF1D4ED8), Color(0xFFE94560)],
                  ),
                  boxShadow: <BoxShadow>[
                    BoxShadow(
                      color: const Color(0xFF1D4ED8).withValues(alpha: 0.35),
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
                'Tu asistente conversacional para Remansos del Norte. Puedo ayudarte con incidentes, avisos, normas, emergencias, administración y uso de CommuSafe.',
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
                    avatar: const Icon(Icons.auto_awesome_rounded, size: 16),
                    label: Text(texto),
                    backgroundColor: const Color(0xFF172033),
                    side: const BorderSide(color: Color(0xFF2E3A50)),
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
