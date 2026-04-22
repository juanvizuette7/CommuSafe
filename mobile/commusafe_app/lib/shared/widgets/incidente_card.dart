import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../features/incidentes/models/incidente_model.dart';
import 'incident_badges.dart';

class IncidenteCard extends StatelessWidget {
  const IncidenteCard({
    super.key,
    required this.incidente,
    this.onTap,
  });

  final IncidenteModel incidente;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final categoryStyle = _categoryVisuals(incidente.categoria);

    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Ink(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.06),
                blurRadius: 24,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                height: 56,
                width: 56,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: categoryStyle.color.withValues(alpha: 0.14),
                ),
                child: Icon(
                  categoryStyle.icon,
                  color: categoryStyle.color,
                  size: 28,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            incidente.titulo,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  color: AppColors.textPrimary,
                                ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: <Widget>[
                            PriorityBadge(
                              priority: incidente.prioridad,
                              label: incidente.prioridadLabel,
                            ),
                            const SizedBox(height: 8),
                            IncidentStatusBadge(
                              status: incidente.estado,
                              label: incidente.estadoLabel,
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      incidente.descripcion,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.textSecondary,
                            height: 1.45,
                          ),
                    ),
                    if (incidente.ubicacionReferencia.trim().isNotEmpty) ...<Widget>[
                      const SizedBox(height: 10),
                      Row(
                        children: <Widget>[
                          const Icon(
                            Icons.place_outlined,
                            size: 16,
                            color: AppColors.textSecondary,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              incidente.ubicacionReferencia,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: AppColors.textSecondary,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                          ),
                        ],
                      ),
                    ],
                    const SizedBox(height: 14),
                    Wrap(
                      runSpacing: 10,
                      spacing: 10,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: <Widget>[
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            const Icon(
                              Icons.person_outline_rounded,
                              size: 16,
                              color: AppColors.textSecondary,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              incidente.reportadoPorNombre,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: AppColors.textSecondary,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                          ],
                        ),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            const Icon(
                              Icons.schedule_rounded,
                              size: 16,
                              color: AppColors.textSecondary,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              incidente.tiempoRelativo,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: AppColors.textSecondary,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                          ],
                        ),
                        if (incidente.tieneEvidencias)
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: <Widget>[
                              const Icon(
                                Icons.photo_library_outlined,
                                size: 16,
                                color: AppColors.textSecondary,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                '${incidente.totalEvidencias} evidencias',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: AppColors.textSecondary,
                                      fontWeight: FontWeight.w600,
                                    ),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  _CategoryVisual _categoryVisuals(String categoria) {
    switch (categoria.toUpperCase()) {
      case 'SEGURIDAD':
        return const _CategoryVisual(Icons.lock_rounded, AppColors.danger);
      case 'CONVIVENCIA':
        return const _CategoryVisual(
          Icons.groups_rounded,
          Color(0xFF2563EB),
        );
      case 'INFRAESTRUCTURA':
        return const _CategoryVisual(
          Icons.settings_suggest_rounded,
          Color(0xFF0F766E),
        );
      case 'EMERGENCIA':
        return const _CategoryVisual(
          Icons.warning_amber_rounded,
          AppColors.warning,
        );
      default:
        return const _CategoryVisual(Icons.info_outline_rounded, AppColors.primary);
    }
  }
}

class _CategoryVisual {
  const _CategoryVisual(this.icon, this.color);

  final IconData icon;
  final Color color;
}
