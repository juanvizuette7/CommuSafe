class MensajeModel {
  const MensajeModel({
    required this.contenido,
    required this.esDelUsuario,
    required this.timestamp,
    this.modo,
  });

  final String contenido;
  final bool esDelUsuario;
  final DateTime timestamp;
  final String? modo;
}
