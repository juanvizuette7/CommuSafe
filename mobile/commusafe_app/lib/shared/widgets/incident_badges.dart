import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

class PriorityBadge extends StatelessWidget {
  const PriorityBadge({
    super.key,
    required this.priority,
    this.label,
  });

  final String priority;
  final String? label;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.priorityColor(priority);
    return _BadgeBase(
      label: (label ?? priority).toUpperCase(),
      color: color,
    );
  }
}

class IncidentStatusBadge extends StatelessWidget {
  const IncidentStatusBadge({
    super.key,
    required this.status,
    this.label,
  });

  final String status;
  final String? label;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.incidentStateColor(status);
    return _BadgeBase(
      label: label ?? _formatStatus(status),
      color: color,
    );
  }

  static String _formatStatus(String status) {
    final normalized = status.toUpperCase();
    switch (normalized) {
      case 'REGISTRADO':
        return 'Registrado';
      case 'EN_PROCESO':
        return 'En proceso';
      case 'RESUELTO':
        return 'Resuelto';
      case 'CERRADO':
        return 'Cerrado';
      default:
        return status.replaceAll('_', ' ');
    }
  }
}

class _BadgeBase extends StatelessWidget {
  const _BadgeBase({
    required this.label,
    required this.color,
  });

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }
}
