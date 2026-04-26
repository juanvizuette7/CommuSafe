import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../features/incidentes/models/incidente_model.dart';
import 'incident_badges.dart';

class IncidenteCard extends StatefulWidget {
  const IncidenteCard({super.key, required this.incidente, this.onTap});

  final IncidenteModel incidente;
  final VoidCallback? onTap;

  @override
  State<IncidenteCard> createState() => _IncidenteCardState();
}

class _IncidenteCardState extends State<IncidenteCard> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final incidente = widget.incidente;
    final categoryStyle = _categoryVisuals(incidente.categoria);
    final priorityColor = incidente.prioridadColor;

    return AnimatedScale(
      scale: _pressed ? 0.985 : 1,
      duration: const Duration(milliseconds: 120),
      curve: Curves.easeOut,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(24),
        child: InkWell(
          borderRadius: BorderRadius.circular(24),
          onTap: widget.onTap,
          onTapDown: (_) => setState(() => _pressed = true),
          onTapCancel: () => setState(() => _pressed = false),
          onTapUp: (_) => setState(() => _pressed = false),
          child: Ink(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: priorityColor.withValues(alpha: 0.11)),
              boxShadow: <BoxShadow>[
                BoxShadow(
                  color: priorityColor.withValues(alpha: 0.10),
                  blurRadius: 28,
                  offset: const Offset(0, 16),
                ),
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.04),
                  blurRadius: 16,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: Stack(
                children: <Widget>[
                  Positioned(
                    left: 0,
                    top: 0,
                    bottom: 0,
                    child: Container(
                      width: 7,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: <Color>[priorityColor, categoryStyle.color],
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    right: -42,
                    top: -50,
                    child: Transform.rotate(
                      angle: -0.5,
                      child: Container(
                        width: 142,
                        height: 96,
                        decoration: BoxDecoration(
                          color: categoryStyle.color.withValues(alpha: 0.07),
                          borderRadius: BorderRadius.circular(32),
                        ),
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 18, 16, 16),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        _CategoryMark(style: categoryStyle),
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
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium
                                          ?.copyWith(
                                            fontWeight: FontWeight.w900,
                                            color: AppColors.textPrimary,
                                            height: 1.18,
                                          ),
                                    ),
                                  ),
                                  const SizedBox(width: 10),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: <Widget>[
                                      PriorityBadge(
                                        priority: incidente.prioridad,
                                        label: incidente.prioridadLabel,
                                      ),
                                      const SizedBox(height: 7),
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
                                style: Theme.of(context).textTheme.bodyMedium
                                    ?.copyWith(
                                      color: AppColors.textSecondary,
                                      height: 1.45,
                                    ),
                              ),
                              if (incidente.ubicacionReferencia
                                  .trim()
                                  .isNotEmpty) ...<Widget>[
                                const SizedBox(height: 10),
                                _MetaLine(
                                  icon: Icons.place_outlined,
                                  text: incidente.ubicacionReferencia,
                                  expanded: true,
                                ),
                              ],
                              const SizedBox(height: 14),
                              Wrap(
                                runSpacing: 10,
                                spacing: 10,
                                crossAxisAlignment: WrapCrossAlignment.center,
                                children: <Widget>[
                                  _MetaLine(
                                    icon: Icons.person_outline_rounded,
                                    text: incidente.reportadoPorNombre,
                                  ),
                                  _MetaLine(
                                    icon: Icons.schedule_rounded,
                                    text: incidente.tiempoRelativo,
                                  ),
                                  if (incidente.tieneEvidencias)
                                    _EvidenceChip(
                                      count: incidente.totalEvidencias,
                                    ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
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

  _CategoryVisual _categoryVisuals(String categoria) {
    switch (categoria.toUpperCase()) {
      case 'SEGURIDAD':
        return const _CategoryVisual(Icons.lock_rounded, AppColors.danger);
      case 'CONVIVENCIA':
        return const _CategoryVisual(Icons.groups_rounded, Color(0xFF2563EB));
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
        return const _CategoryVisual(
          Icons.info_outline_rounded,
          AppColors.primary,
        );
    }
  }
}

class _CategoryMark extends StatelessWidget {
  const _CategoryMark({required this.style});

  final _CategoryVisual style;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 58,
      width: 58,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[
            style.color.withValues(alpha: 0.22),
            style.color.withValues(alpha: 0.06),
          ],
        ),
        border: Border.all(color: style.color.withValues(alpha: 0.16)),
      ),
      child: Icon(style.icon, color: style.color, size: 30),
    );
  }
}

class _MetaLine extends StatelessWidget {
  const _MetaLine({
    required this.icon,
    required this.text,
    this.expanded = false,
  });

  final IconData icon;
  final String text;
  final bool expanded;

  @override
  Widget build(BuildContext context) {
    final content = Row(
      mainAxisSize: expanded ? MainAxisSize.max : MainAxisSize.min,
      children: <Widget>[
        Icon(icon, size: 16, color: AppColors.textSecondary),
        const SizedBox(width: 6),
        Flexible(
          child: Text(
            text,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );

    return expanded ? content : IntrinsicWidth(child: content);
  }
}

class _EvidenceChip extends StatelessWidget {
  const _EvidenceChip({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: AppColors.accent.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const Icon(
            Icons.photo_library_outlined,
            size: 15,
            color: AppColors.accent,
          ),
          const SizedBox(width: 6),
          Text(
            '$count fotos',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: AppColors.accent,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _CategoryVisual {
  const _CategoryVisual(this.icon, this.color);

  final IconData icon;
  final Color color;
}
