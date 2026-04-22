import 'package:flutter/material.dart';

import '../../../shared/widgets/section_card.dart';

class CrearIncidenteScreen extends StatelessWidget {
  const CrearIncidenteScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: const <Widget>[
        SectionCard(
          title: 'Nuevo incidente',
          subtitle: 'Formulario base listo para el sprint funcional de reportes.',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text('Aquí se integrará el formulario completo con categorías, prioridad automática, ubicación y evidencias fotográficas.'),
            ],
          ),
        ),
      ],
    );
  }
}
