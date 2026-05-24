class ConversacionModel {
  const ConversacionModel({
    required this.id,
    required this.titulo,
    required this.fechaCreacion,
    required this.fechaActualizacion,
    required this.totalMensajes,
    required this.ultimoMensaje,
  });

  final String id;
  final String titulo;
  final DateTime fechaCreacion;
  final DateTime fechaActualizacion;
  final int totalMensajes;
  final String ultimoMensaje;

  factory ConversacionModel.fromJson(Map<String, dynamic> json) {
    return ConversacionModel(
      id: json['id']?.toString() ?? '',
      titulo: json['titulo']?.toString() ?? 'Nueva conversación',
      fechaCreacion:
          DateTime.tryParse(json['fecha_creacion']?.toString() ?? '') ??
          DateTime.now(),
      fechaActualizacion:
          DateTime.tryParse(json['fecha_actualizacion']?.toString() ?? '') ??
          DateTime.now(),
      totalMensajes: int.tryParse(json['total_mensajes']?.toString() ?? '') ?? 0,
      ultimoMensaje: json['ultimo_mensaje']?.toString() ?? '',
    );
  }

  ConversacionModel copyWith({
    String? titulo,
    DateTime? fechaActualizacion,
    int? totalMensajes,
    String? ultimoMensaje,
  }) {
    return ConversacionModel(
      id: id,
      titulo: titulo ?? this.titulo,
      fechaCreacion: fechaCreacion,
      fechaActualizacion: fechaActualizacion ?? this.fechaActualizacion,
      totalMensajes: totalMensajes ?? this.totalMensajes,
      ultimoMensaje: ultimoMensaje ?? this.ultimoMensaje,
    );
  }
}
