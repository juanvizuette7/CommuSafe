import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/empty_state_card.dart';
import '../../../shared/widgets/section_card.dart';
import '../providers/incidentes_provider.dart';

class IncidentesListScreen extends StatelessWidget {
  const IncidentesListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final incidentesProvider = context.watch<IncidentesProvider>();

    return ListView(
      padding: const EdgeInsets.all(20),
      children: <Widget>[
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            gradient: const LinearGradient(
              colors: <Color>[
                AppColors.primary,
                AppColors.accent,
              ],
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'Centro de incidentes',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                'Reporta novedades, revisa el estado de tus casos y accede a la trazabilidad de cada incidente.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.white.withValues(alpha: 0.85),
                      height: 1.5,
                    ),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: () => context.push('/incidentes/crear'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: AppColors.primary,
                ),
                icon: const Icon(Icons.add_alert_rounded),
                label: const Text('Crear incidente'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        SectionCard(
          title: 'Mis reportes',
          subtitle: 'La sincronización real con el backend llegará en el próximo sprint.',
          child: incidentesProvider.incidentes.isEmpty
              ? const EmptyStateCard(
                  icon: Icons.inbox_rounded,
                  title: 'No hay incidentes cargados',
                  message:
                      'La estructura ya está lista para consumir el API y mostrar tus reportes en tiempo real.',
                )
              : Column(
                  children: incidentesProvider.incidentes
                      .map(
                        (incidente) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(incidente.titulo),
                          subtitle: Text(
                            DateFormat('dd MMM yyyy, hh:mm a')
                                .format(incidente.fechaReporte),
                          ),
                          trailing: const Icon(Icons.chevron_right_rounded),
                          onTap: () => context.push('/incidentes/${incidente.id}'),
                        ),
                      )
                      .toList(),
                ),
        ),
      ],
    );
  }
}
