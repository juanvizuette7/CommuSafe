class MensajeModel {
  const MensajeModel({
    required this.contenido,
    required this.esDelUsuario,
    required this.timestamp,
  });

  final String contenido;
  final bool esDelUsuario;
  final DateTime timestamp;
}
