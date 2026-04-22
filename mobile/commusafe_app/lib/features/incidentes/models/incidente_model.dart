class IncidenteModel {
  const IncidenteModel({
    required this.id,
    required this.titulo,
    required this.descripcion,
    required this.categoria,
    required this.prioridad,
    required this.estado,
    required this.fechaReporte,
    this.ubicacionReferencia,
    this.reportadoPorNombre,
  });

  final String id;
  final String titulo;
  final String descripcion;
  final String categoria;
  final String prioridad;
  final String estado;
  final DateTime fechaReporte;
  final String? ubicacionReferencia;
  final String? reportadoPorNombre;

  String get categoriaLegible {
    switch (categoria.toUpperCase()) {
      case 'SEGURIDAD':
        return 'Seguridad';
      case 'CONVIVENCIA':
        return 'Convivencia';
      case 'INFRAESTRUCTURA':
        return 'Infraestructura';
      case 'EMERGENCIA':
        return 'Emergencia';
      default:
        return categoria;
    }
  }

  String get prioridadLegible {
    switch (prioridad.toUpperCase()) {
      case 'ALTA':
        return 'Alta';
      case 'MEDIA':
        return 'Media';
      case 'BAJA':
        return 'Baja';
      default:
        return prioridad;
    }
  }

  String get estadoLegible {
    switch (estado.toUpperCase()) {
      case 'REGISTRADO':
        return 'Registrado';
      case 'EN_PROCESO':
        return 'En proceso';
      case 'RESUELTO':
        return 'Resuelto';
      case 'CERRADO':
        return 'Cerrado';
      default:
        return estado;
    }
  }

  factory IncidenteModel.fromJson(Map<String, dynamic> json) {
    return IncidenteModel(
      id: json['id']?.toString() ?? '',
      titulo: json['titulo']?.toString() ?? '',
      descripcion: json['descripcion']?.toString() ?? '',
      categoria: json['categoria']?.toString() ?? '',
      prioridad: json['prioridad']?.toString() ?? '',
      estado: json['estado']?.toString() ?? '',
      fechaReporte: DateTime.tryParse(
            json['fecha_reporte']?.toString() ?? '',
          ) ??
          DateTime.now(),
      ubicacionReferencia: json['ubicacion_referencia']?.toString(),
      reportadoPorNombre: json['reportado_por_nombre']?.toString(),
    );
  }
}
