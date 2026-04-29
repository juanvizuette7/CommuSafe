class AvisoDestacadoModel {
  const AvisoDestacadoModel({
    required this.id,
    required this.titulo,
    required this.cuerpo,
    required this.tipo,
    required this.fechaEnvio,
  });

  final String id;
  final String titulo;
  final String cuerpo;
  final String tipo;
  final DateTime fechaEnvio;

  bool get esEmergencia => tipo.toUpperCase() == 'EMERGENCIA';

  factory AvisoDestacadoModel.fromJson(Map<String, dynamic> json) {
    return AvisoDestacadoModel(
      id: json['id']?.toString() ?? '',
      titulo: json['titulo']?.toString() ?? 'Aviso comunitario',
      cuerpo: json['cuerpo']?.toString() ?? '',
      tipo: json['tipo']?.toString() ?? 'AVISO_ADMIN',
      fechaEnvio:
          DateTime.tryParse(json['fecha_envio']?.toString() ?? '') ??
          DateTime.now(),
    );
  }
}
