class HistorialModel {
  const HistorialModel({
    required this.id,
    required this.estadoAnterior,
    required this.estadoAnteriorLabel,
    required this.estadoNuevo,
    required this.estadoNuevoLabel,
    required this.cambiadoPorNombre,
    required this.fechaCambio,
    required this.comentario,
  });

  final String id;
  final String estadoAnterior;
  final String estadoAnteriorLabel;
  final String estadoNuevo;
  final String estadoNuevoLabel;
  final String cambiadoPorNombre;
  final DateTime? fechaCambio;
  final String comentario;

  String get transicionLegible => '$estadoAnteriorLabel → $estadoNuevoLabel';

  factory HistorialModel.fromJson(Map<String, dynamic>? json) {
    final data = json ?? <String, dynamic>{};
    final cambiadoPor = _readMap(data['cambiado_por']);

    return HistorialModel(
      id: data['id']?.toString() ?? '',
      estadoAnterior: data['estado_anterior']?.toString() ?? '',
      estadoAnteriorLabel:
          data['estado_anterior_label']?.toString().trim().isNotEmpty == true
              ? data['estado_anterior_label'].toString().trim()
              : 'Sin estado previo',
      estadoNuevo: data['estado_nuevo']?.toString() ?? '',
      estadoNuevoLabel: data['estado_nuevo_label']?.toString().trim().isNotEmpty ==
              true
          ? data['estado_nuevo_label'].toString().trim()
          : data['estado_nuevo']?.toString().replaceAll('_', ' ') ?? '',
      cambiadoPorNombre:
          cambiadoPor['nombre_completo']?.toString().trim().isNotEmpty == true
              ? cambiadoPor['nombre_completo'].toString().trim()
              : 'Sistema',
      fechaCambio: DateTime.tryParse(data['fecha_cambio']?.toString() ?? ''),
      comentario: data['comentario']?.toString().trim() ?? '',
    );
  }

  static Map<String, dynamic> _readMap(dynamic value) {
    if (value is Map<String, dynamic>) {
      return value;
    }
    if (value is Map) {
      return value.map(
        (dynamic key, dynamic val) => MapEntry(key.toString(), val),
      );
    }
    return <String, dynamic>{};
  }
}
