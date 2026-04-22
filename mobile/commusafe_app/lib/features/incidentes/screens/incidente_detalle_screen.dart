import 'package:flutter/material.dart';

import '../../../shared/widgets/empty_state_card.dart';
import '../../../shared/widgets/section_card.dart';

class IncidenteDetalleScreen extends StatelessWidget {
  const IncidenteDetalleScreen({
    super.key,
    required this.incidenteId,
  });

  final String incidenteId;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: <Widget>[
        SectionCard(
          title: 'Detalle del incidente',
          subtitle: 'Identificador del caso: $incidenteId',
          child: const EmptyStateCard(
            icon: Icons.receipt_long_rounded,
            title: 'Detalle listo para conectar',
            message:
                'Este espacio mostrará descripción, evidencias, historial y cambios de estado una vez se conecte el módulo de incidentes al backend.',
          ),
        ),
      ],
    );
  }
}
