import 'package:flutter/foundation.dart';

import '../models/conversacion_model.dart';
import '../models/mensaje_model.dart';
import '../services/asistente_api_service.dart';

class AsistenteProvider extends ChangeNotifier {
  final List<ConversacionModel> _conversaciones = <ConversacionModel>[];
  final List<MensajeModel> _mensajes = <MensajeModel>[];

  ConversacionModel? _conversacionActiva;
  bool _isLoadingConversations = false;
  bool _isLoadingMessages = false;
  bool _isSending = false;
  String? _errorMessage;
  String _ultimoModo = 'ia';

  List<ConversacionModel> get conversaciones =>
      List<ConversacionModel>.unmodifiable(_conversaciones);
  List<MensajeModel> get mensajes => List<MensajeModel>.unmodifiable(_mensajes);
  ConversacionModel? get conversacionActiva => _conversacionActiva;
  bool get isLoadingConversations => _isLoadingConversations;
  bool get isLoadingMessages => _isLoadingMessages;
  bool get isSending => _isSending;
  String? get errorMessage => _errorMessage;
  String get ultimoModo => _ultimoModo;
  bool get tieneConversacionActiva => _conversacionActiva != null;

  Future<void> cargarConversaciones() async {
    _isLoadingConversations = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final conversaciones = await AsistenteApiService.listarConversaciones();
      _conversaciones
        ..clear()
        ..addAll(conversaciones);
    } catch (_) {
      _errorMessage = 'No se pudieron cargar tus conversaciones.';
    } finally {
      _isLoadingConversations = false;
      notifyListeners();
    }
  }

  void nuevaConversacion() {
    _conversacionActiva = null;
    _mensajes.clear();
    _errorMessage = null;
    _ultimoModo = 'ia';
    notifyListeners();
  }

  Future<void> seleccionarConversacion(ConversacionModel conversacion) async {
    _conversacionActiva = conversacion;
    _mensajes.clear();
    _isLoadingMessages = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final mensajes = await AsistenteApiService.cargarMensajes(
        conversacion.id,
      );
      _mensajes
        ..clear()
        ..addAll(mensajes);
      for (final mensaje in _mensajes.reversed) {
        if (!mensaje.esDelUsuario && mensaje.modo != null) {
          _ultimoModo = mensaje.modo == 'error' ? 'error' : 'ia';
          break;
        }
      }
    } catch (_) {
      _errorMessage = 'No se pudo abrir esta conversación.';
    } finally {
      _isLoadingMessages = false;
      notifyListeners();
    }
  }

  Future<void> enviarMensaje(String texto) async {
    final mensaje = texto.trim();
    if (mensaje.isEmpty || _isSending) {
      return;
    }

    _isSending = true;
    _errorMessage = null;
    final localUserMessage = MensajeModel(
      contenido: mensaje,
      esDelUsuario: true,
      timestamp: DateTime.now(),
    );
    _mensajes.add(localUserMessage);
    notifyListeners();

    try {
      ConversacionModel conversacion =
          _conversacionActiva ?? await AsistenteApiService.crearConversacion();
      _conversacionActiva = conversacion;
      _upsertConversacion(conversacion);

      final respuesta = await AsistenteApiService.enviarMensaje(
        conversacionId: conversacion.id,
        mensaje: mensaje,
      );

      final localIndex = _mensajes.indexOf(localUserMessage);
      if (localIndex >= 0) {
        _mensajes[localIndex] = respuesta.mensajeUsuario;
      }
      _mensajes.add(respuesta.mensajeAsistente);
      _conversacionActiva = respuesta.conversacion;
      _ultimoModo = respuesta.modo == 'error' ? 'error' : 'ia';
      _upsertConversacion(respuesta.conversacion);
    } catch (_) {
      _errorMessage =
          'No pude conectar con CommuBot. Revisa tu conexión e intenta nuevamente.';
      _ultimoModo = 'error';
      _mensajes.add(
        MensajeModel(
          contenido: _errorMessage!,
          esDelUsuario: false,
          timestamp: DateTime.now(),
          modo: 'error',
        ),
      );
    } finally {
      _isSending = false;
      notifyListeners();
    }
  }

  Future<void> eliminarConversacion(String conversacionId) async {
    try {
      await AsistenteApiService.eliminarConversacion(conversacionId);
      _conversaciones.removeWhere((item) => item.id == conversacionId);
      if (_conversacionActiva?.id == conversacionId) {
        nuevaConversacion();
      } else {
        notifyListeners();
      }
    } catch (_) {
      _errorMessage = 'No se pudo eliminar la conversación.';
      notifyListeners();
    }
  }

  Future<void> actualizarTitulo(String titulo) async {
    final conversacion = _conversacionActiva;
    if (conversacion == null || titulo.trim().length < 3) {
      return;
    }

    try {
      final actualizada = await AsistenteApiService.actualizarTitulo(
        conversacionId: conversacion.id,
        titulo: titulo,
      );
      _conversacionActiva = actualizada;
      _upsertConversacion(actualizada);
    } catch (_) {
      _errorMessage = 'No se pudo actualizar el título.';
      notifyListeners();
    }
  }

  void reset() {
    _conversaciones.clear();
    _mensajes.clear();
    _conversacionActiva = null;
    _isLoadingConversations = false;
    _isLoadingMessages = false;
    _isSending = false;
    _errorMessage = null;
    _ultimoModo = 'ia';
    notifyListeners();
  }

  void _upsertConversacion(ConversacionModel conversacion) {
    _conversaciones.removeWhere((item) => item.id == conversacion.id);
    _conversaciones.insert(0, conversacion);
    notifyListeners();
  }
}
