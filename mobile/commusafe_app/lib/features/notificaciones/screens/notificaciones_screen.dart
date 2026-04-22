import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/empty_state_card.dart';
import '../../../shared/widgets/section_card.dart';
import '../providers/notificaciones_provider.dart';

class NotificacionesScreen extends StatelessWidget {
  const NotificacionesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<NotificacionesProvider>();

    return ListView(
      padding: const EdgeInsets.all(20),
      children: <Widget>[
        SectionCard(
          title: 'Centro de notificaciones',
          subtitle: 'Alertas internas, cambios de estado y avisos administrativos.',
          child: provider.items.isEmpty
              ? const EmptyStateCard(
                  icon: Icons.notifications_none_rounded,
                  title: 'Sin notificaciones por ahora',
                  message:
                      'La integración con alertas push y notificaciones internas ya tiene su base preparada.',
                )
              : Column(
                  children: provider.items
                      .map(
                        (item) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: CircleAvatar(
                            backgroundColor: item.leida
                                ? AppColors.muted
                                : AppColors.danger.withValues(alpha: 0.12),
                            child: Icon(
                              item.leida
                                  ? Icons.notifications_none_rounded
                                  : Icons.notifications_active_rounded,
                              color: item.leida
                                  ? AppColors.textSecondary
                                  : AppColors.danger,
                            ),
                          ),
                          title: Text(item.titulo),
                          subtitle: Text(item.cuerpo),
                        ),
                      )
                      .toList(),
                ),
        ),
      ],
    );
  }
}
