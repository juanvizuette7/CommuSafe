import '../../../core/constants/app_constants.dart';
import '../../../core/services/api_service.dart';
import '../models/conversacion_model.dart';
import '../models/mensaje_model.dart';

class AsistenteApiService {
  const AsistenteApiService._();

  static List<dynamic> _extraerResultados(dynamic data) {
    if (data is Map<String, dynamic> && data['results'] is List) {
      return data['results'] as List<dynamic>;
    }
    if (data is List) {
      return data;
    }
    return const <dynamic>[];
  }

  static Future<List<ConversacionModel>> listarConversaciones() async {
    final response = await ApiService.get<dynamic>(
      AppConstants.assistantConversationsEndpoint,
    );
    return _extraerResultados(response.data)
        .whereType<Map<String, dynamic>>()
        .map(ConversacionModel.fromJson)
        .toList();
  }

  static Future<ConversacionModel> crearConversacion({String? titulo}) async {
    final response = await ApiService.post<Map<String, dynamic>>(
      AppConstants.assistantConversationsEndpoint,
      data: <String, dynamic>{
        if (titulo != null && titulo.trim().isNotEmpty) 'titulo': titulo.trim(),
      },
    );
    return ConversacionModel.fromJson(response.data ?? <String, dynamic>{});
  }

  static Future<List<MensajeModel>> cargarMensajes(String conversacionId) async {
    final response = await ApiService.get<dynamic>(
      '${AppConstants.assistantConversationsEndpoint}$conversacionId/mensajes/',
    );
    return _extraerResultados(response.data)
        .whereType<Map<String, dynamic>>()
        .map(MensajeModel.fromJson)
        .toList();
  }

  static Future<EnviarMensajeResponse> enviarMensaje({
    required String conversacionId,
    required String mensaje,
  }) async {
    final response = await ApiService.post<Map<String, dynamic>>(
      '${AppConstants.assistantConversationsEndpoint}$conversacionId/enviar/',
      data: <String, dynamic>{'mensaje': mensaje},
    );
    return EnviarMensajeResponse.fromJson(response.data ?? <String, dynamic>{});
  }

  static Future<ConversacionModel> actualizarTitulo({
    required String conversacionId,
    required String titulo,
  }) async {
    final response = await ApiService.patch<Map<String, dynamic>>(
      '${AppConstants.assistantConversationsEndpoint}$conversacionId/titulo/',
      data: <String, dynamic>{'titulo': titulo},
    );
    return ConversacionModel.fromJson(response.data ?? <String, dynamic>{});
  }

  static Future<void> eliminarConversacion(String conversacionId) async {
    await ApiService.delete(
      '${AppConstants.assistantConversationsEndpoint}$conversacionId/',
    );
  }
}

class EnviarMensajeResponse {
  const EnviarMensajeResponse({
    required this.conversacion,
    required this.mensajeUsuario,
    required this.mensajeAsistente,
    required this.modo,
    required this.proveedor,
    required this.modeloUsado,
  });

  final ConversacionModel conversacion;
  final MensajeModel mensajeUsuario;
  final MensajeModel mensajeAsistente;
  final String modo;
  final String proveedor;
  final String modeloUsado;

  factory EnviarMensajeResponse.fromJson(Map<String, dynamic> json) {
    return EnviarMensajeResponse(
      conversacion: ConversacionModel.fromJson(
        (json['conversacion'] as Map?)?.cast<String, dynamic>() ??
            <String, dynamic>{},
      ),
      mensajeUsuario: MensajeModel.fromJson(
        (json['mensaje_usuario'] as Map?)?.cast<String, dynamic>() ??
            <String, dynamic>{},
      ),
      mensajeAsistente: MensajeModel.fromJson(
        (json['mensaje_asistente'] as Map?)?.cast<String, dynamic>() ??
            <String, dynamic>{},
      ).copyWith(modo: json['modo']?.toString()),
      modo: json['modo']?.toString() ?? 'ia',
      proveedor: json['proveedor']?.toString() ?? 'gemini',
      modeloUsado: json['modelo_usado']?.toString() ?? '',
    );
  }
}
