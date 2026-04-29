import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../features/notificaciones/models/aviso_destacado_model.dart';
import '../../features/notificaciones/providers/notificacion_provider.dart';

class AvisoBanner extends StatelessWidget {
  const AvisoBanner({required this.aviso, super.key});

  final AvisoDestacadoModel aviso;

  @override
  Widget build(BuildContext context) {
    final emergencia = aviso.esEmergencia;
    final colors = emergencia
        ? const <Color>[Color(0xFFE94560), Color(0xFF8B1029)]
        : const <Color>[Color(0xFFF97316), Color(0xFFB45309)];

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: colors,
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: colors.last.withValues(alpha: 0.24),
            blurRadius: 22,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 10, 14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                height: 46,
                width: 46,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.22),
                  ),
                ),
                child: Icon(
                  emergencia
                      ? Icons.emergency_share_rounded
                      : Icons.campaign_rounded,
                  color: Colors.white,
                  size: 26,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      aviso.titulo,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      aviso.cuerpo,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.white.withValues(alpha: 0.88),
                        fontWeight: FontWeight.w600,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                tooltip: 'Descartar aviso',
                onPressed: () {
                  context.read<NotificacionProvider>().marcarLeida(aviso.id);
                },
                icon: const Icon(Icons.close_rounded),
                color: Colors.white,
                style: IconButton.styleFrom(
                  backgroundColor: Colors.white.withValues(alpha: 0.14),
                  fixedSize: const Size(38, 38),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
