class UsuarioModel {
  const UsuarioModel({
    required this.id,
    required this.email,
    required this.nombre,
    required this.apellido,
    required this.rol,
    this.unidadResidencial,
    this.telefono,
    this.fotoPerfil,
    this.activo = true,
  });

  final String id;
  final String email;
  final String nombre;
  final String apellido;
  final String rol;
  final String? unidadResidencial;
  final String? telefono;
  final String? fotoPerfil;
  final bool activo;

  String get nombreCompleto => '$nombre $apellido'.trim();

  String get rolLegible {
    switch (rol.toUpperCase()) {
      case 'ADMINISTRADOR':
        return 'Administrador';
      case 'VIGILANTE':
        return 'Vigilante';
      case 'RESIDENTE':
        return 'Residente';
      default:
        return rol;
    }
  }

  factory UsuarioModel.fromJson(Map<String, dynamic> json) {
    return UsuarioModel(
      id: json['id']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      nombre: json['nombre']?.toString() ?? '',
      apellido: json['apellido']?.toString() ?? '',
      rol: json['rol']?.toString() ?? '',
      unidadResidencial: json['unidad_residencial']?.toString(),
      telefono: json['telefono']?.toString(),
      fotoPerfil: json['foto_perfil']?.toString(),
      activo: json['activo'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'email': email,
      'nombre': nombre,
      'apellido': apellido,
      'rol': rol,
      'unidad_residencial': unidadResidencial,
      'telefono': telefono,
      'foto_perfil': fotoPerfil,
      'activo': activo,
    };
  }
}
