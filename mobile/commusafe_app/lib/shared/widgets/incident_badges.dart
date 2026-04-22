import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

class PriorityBadge extends StatelessWidget {
  const PriorityBadge({
    super.key,
    required this.priority,
  });

  final String priority;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.priorityColor(priority);
    return _BadgeBase(label: priority, color: color);
  }
}

class IncidentStatusBadge extends StatelessWidget {
  const IncidentStatusBadge({
    super.key,
    required this.status,
  });

  final String status;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.incidentStateColor(status);
    return _BadgeBase(label: status.replaceAll('_', ' '), color: color);
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
