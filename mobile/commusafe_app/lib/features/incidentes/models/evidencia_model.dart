import '../../../core/constants/app_constants.dart';

class EvidenciaModel {
  const EvidenciaModel({
    required this.id,
    required this.imagenUrl,
    required this.descripcion,
    required this.fechaSubida,
  });

  final String id;
  final String imagenUrl;
  final String descripcion;
  final DateTime? fechaSubida;

  factory EvidenciaModel.fromJson(Map<String, dynamic>? json) {
    final data = json ?? <String, dynamic>{};
    return EvidenciaModel(
      id: data['id']?.toString() ?? '',
      imagenUrl: _resolveMediaUrl(data['imagen']?.toString()),
      descripcion: data['descripcion']?.toString().trim() ?? '',
      fechaSubida: DateTime.tryParse(data['fecha_subida']?.toString() ?? ''),
    );
  }

  static String _resolveMediaUrl(String? rawValue) {
    if (rawValue == null || rawValue.trim().isEmpty) {
      return '';
    }

    final normalizedValue = rawValue.trim();
    if (normalizedValue.startsWith('http://') ||
        normalizedValue.startsWith('https://')) {
      return normalizedValue;
    }

    if (normalizedValue.startsWith('/')) {
      return '${AppConstants.baseUrl}$normalizedValue';
    }

    return '${AppConstants.baseUrl}/$normalizedValue';
  }
}
