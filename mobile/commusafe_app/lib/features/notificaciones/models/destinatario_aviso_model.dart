class DestinatarioAvisoModel {
  const DestinatarioAvisoModel({
    required this.id,
    required this.nombreCompleto,
    required this.email,
    required this.rol,
    required this.telefono,
    required this.unidadResidencial,
  });

  final String id;
  final String nombreCompleto;
  final String email;
  final String rol;
  final String telefono;
  final String unidadResidencial;

  factory DestinatarioAvisoModel.fromJson(Map<String, dynamic> json) {
    final nombre = json['nombre_completo']?.toString().trim();
    final fallbackNombre = [
      json['nombre']?.toString().trim() ?? '',
      json['apellido']?.toString().trim() ?? '',
    ].where((value) => value.isNotEmpty).join(' ');

    return DestinatarioAvisoModel(
      id: json['id']?.toString() ?? '',
      nombreCompleto: nombre?.isNotEmpty == true ? nombre! : fallbackNombre,
      email: json['email']?.toString().trim() ?? '',
      rol: json['rol']?.toString().trim() ?? '',
      telefono: json['telefono']?.toString().trim() ?? '',
      unidadResidencial: json['unidad_residencial']?.toString().trim() ?? '',
    );
  }

  String get descripcion {
    final partes = <String>[
      if (unidadResidencial.isNotEmpty) unidadResidencial,
      if (telefono.isNotEmpty) telefono,
    ];
    return partes.isEmpty ? email : partes.join(' · ');
  }
}
