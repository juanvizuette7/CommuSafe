import '../../../core/constants/app_constants.dart';

class UsuarioModel {
  const UsuarioModel({
    required this.id,
    required this.email,
    required this.nombre,
    required this.apellido,
    required this.nombreCompleto,
    required this.rol,
    this.unidadResidencial,
    this.telefono,
    this.fotoPerfilUrl,
    this.activo = true,
  });

  final String id;
  final String email;
  final String nombre;
  final String apellido;
  final String nombreCompleto;
  final String? unidadResidencial;
  final String rol;
  final String? telefono;
  final String? fotoPerfilUrl;
  final bool activo;

  bool get esAdmin => rol.toUpperCase() == 'ADMINISTRADOR';
  bool get esVigilante => rol.toUpperCase() == 'VIGILANTE';
  bool get esResidente => rol.toUpperCase() == 'RESIDENTE';

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

  String get iniciales {
    final nombreInicial = nombre.trim().isEmpty ? '' : nombre.trim()[0];
    final apellidoInicial = apellido.trim().isEmpty ? '' : apellido.trim()[0];
    final initials = '$nombreInicial$apellidoInicial'.trim();
    return initials.isEmpty ? 'CS' : initials.toUpperCase();
  }

  factory UsuarioModel.fromJson(Map<String, dynamic> json) {
    final nombre = json['nombre']?.toString().trim() ?? '';
    final apellido = json['apellido']?.toString().trim() ?? '';
    final nombreCompleto =
        json['nombre_completo']?.toString().trim() ??
        '$nombre $apellido'.trim();

    return UsuarioModel(
      id: json['id']?.toString() ?? '',
      email: json['email']?.toString().trim() ?? '',
      nombre: nombre,
      apellido: apellido,
      nombreCompleto: nombreCompleto,
      unidadResidencial: json['unidad_residencial']?.toString(),
      rol: json['rol']?.toString() ?? '',
      telefono: json['telefono']?.toString(),
      fotoPerfilUrl: _resolvePhotoUrl(json['foto_perfil']?.toString()),
      activo: json['activo'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'email': email,
      'nombre': nombre,
      'apellido': apellido,
      'nombre_completo': nombreCompleto,
      'unidad_residencial': unidadResidencial,
      'rol': rol,
      'telefono': telefono,
      'foto_perfil': fotoPerfilUrl,
      'activo': activo,
    };
  }

  static String? _resolvePhotoUrl(String? rawValue) {
    if (rawValue == null || rawValue.trim().isEmpty) {
      return null;
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
