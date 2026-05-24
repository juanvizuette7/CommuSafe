class MensajeModel {
  const MensajeModel({
    required this.contenido,
    required bool esDelUsuario,
    required DateTime timestamp,
    this.id,
    this.conversacionId,
    this.modo,
  }) : rol = esDelUsuario ? 'USUARIO' : 'ASISTENTE',
       fechaCreacion = timestamp;

  const MensajeModel.persistido({
    required this.id,
    required this.conversacionId,
    required this.rol,
    required this.contenido,
    required this.fechaCreacion,
    this.modo,
  });

  final String? id;
  final String? conversacionId;
  final String rol;
  final String contenido;
  final DateTime fechaCreacion;
  final String? modo;

  bool get esDelUsuario => rol.toUpperCase() == 'USUARIO';

  DateTime get timestamp => fechaCreacion;

  factory MensajeModel.fromJson(Map<String, dynamic> json) {
    return MensajeModel.persistido(
      id: json['id']?.toString(),
      conversacionId: json['conversacion']?.toString(),
      rol: json['rol']?.toString() ?? 'ASISTENTE',
      contenido: json['contenido']?.toString() ?? '',
      fechaCreacion:
          DateTime.tryParse(json['fecha_creacion']?.toString() ?? '') ??
          DateTime.now(),
      modo: json['modo']?.toString(),
    );
  }

  MensajeModel copyWith({
    String? id,
    String? conversacionId,
    String? rol,
    String? contenido,
    DateTime? fechaCreacion,
    String? modo,
  }) {
    return MensajeModel.persistido(
      id: id ?? this.id,
      conversacionId: conversacionId ?? this.conversacionId,
      rol: rol ?? this.rol,
      contenido: contenido ?? this.contenido,
      fechaCreacion: fechaCreacion ?? this.fechaCreacion,
      modo: modo ?? this.modo,
    );
  }
}
