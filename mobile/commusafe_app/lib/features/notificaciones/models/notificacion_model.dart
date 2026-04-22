class NotificacionModel {
  const NotificacionModel({
    required this.id,
    required this.titulo,
    required this.cuerpo,
    required this.tipo,
    required this.leida,
    required this.fechaEnvio,
    this.tituloIncidente,
  });

  final String id;
  final String titulo;
  final String cuerpo;
  final String tipo;
  final bool leida;
  final DateTime fechaEnvio;
  final String? tituloIncidente;

  String get tipoLegible {
    switch (tipo.toUpperCase()) {
      case 'INCIDENTE_NUEVO':
        return 'Incidente nuevo';
      case 'CAMBIO_ESTADO':
        return 'Cambio de estado';
      case 'AVISO_ADMIN':
        return 'Aviso administrativo';
      case 'EMERGENCIA':
        return 'Emergencia';
      default:
        return tipo;
    }
  }

  factory NotificacionModel.fromJson(Map<String, dynamic> json) {
    return NotificacionModel(
      id: json['id']?.toString() ?? '',
      titulo: json['titulo']?.toString() ?? '',
      cuerpo: json['cuerpo']?.toString() ?? '',
      tipo: json['tipo']?.toString() ?? '',
      leida: json['leida'] as bool? ?? false,
      fechaEnvio:
          DateTime.tryParse(json['fecha_envio']?.toString() ?? '') ?? DateTime.now(),
      tituloIncidente: json['incidente_titulo']?.toString(),
    );
  }
}
