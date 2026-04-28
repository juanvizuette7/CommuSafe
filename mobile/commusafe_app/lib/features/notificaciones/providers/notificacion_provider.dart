import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/services/api_service.dart';
import '../models/destinatario_aviso_model.dart';
import '../models/notificacion_model.dart';

class NotificacionProvider extends ChangeNotifier {
  final List<NotificacionModel> _notificaciones = <NotificacionModel>[];
  final List<DestinatarioAvisoModel> _residentesAviso =
      <DestinatarioAvisoModel>[];
  final List<DestinatarioAvisoModel> _vigilantesAviso =
      <DestinatarioAvisoModel>[];
  final List<DestinatarioAvisoModel> _administradoresAviso =
      <DestinatarioAvisoModel>[];

  bool _isLoading = false;
  bool _isCreatingNotice = false;
  bool _isLoadingNoticeRecipients = false;
  int _noLeidasCount = 0;
  String? _errorMessage;

  List<NotificacionModel> get notificaciones =>
      List<NotificacionModel>.unmodifiable(_notificaciones);
  List<DestinatarioAvisoModel> get residentesAviso =>
      List<DestinatarioAvisoModel>.unmodifiable(_residentesAviso);
  List<DestinatarioAvisoModel> get vigilantesAviso =>
      List<DestinatarioAvisoModel>.unmodifiable(_vigilantesAviso);
  List<DestinatarioAvisoModel> get administradoresAviso =>
      List<DestinatarioAvisoModel>.unmodifiable(_administradoresAviso);
  List<NotificacionModel> get items => notificaciones;
  bool get isLoading => _isLoading;
  bool get loading => _isLoading;
  bool get isCreatingNotice => _isCreatingNotice;
  bool get isLoadingNoticeRecipients => _isLoadingNoticeRecipients;
  int get noLeidasCount => _noLeidasCount;
  String? get errorMessage => _errorMessage;

  Future<void> cargarNotificaciones() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.get<dynamic>(
        AppConstants.notificationsEndpoint,
      );
      final payload = _normalizeMap(response.data);
      final rawResults = response.data is List
          ? response.data as List<dynamic>
          : (payload['results'] is List
                ? payload['results'] as List
                : <dynamic>[]);

      final nuevas = rawResults
          .map((item) => NotificacionModel.fromJson(_normalizeMap(item)))
          .toList();

      _notificaciones
        ..clear()
        ..addAll(nuevas);
      _noLeidasCount = nuevas.where((item) => !item.leida).length;
      _errorMessage = null;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
    } catch (_) {
      _errorMessage = 'No fue posible cargar las notificaciones.';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> cargarConteoNoLeidas() async {
    try {
      final response = await ApiService.get<Map<String, dynamic>>(
        AppConstants.unreadNotificationsCountEndpoint,
      );
      final payload = _normalizeMap(response.data);
      _noLeidasCount =
          _toInt(payload['no_leidas']) ??
          _toInt(payload['count']) ??
          _noLeidasCount;
      notifyListeners();
    } catch (_) {
      // El refresco manual no debe interrumpir la experiencia principal.
    }
  }

  Future<void> marcarLeida(String id) async {
    final index = _notificaciones.indexWhere((item) => item.id == id);
    if (index < 0) {
      return;
    }

    final current = _notificaciones[index];
    if (current.leida) {
      return;
    }

    _notificaciones[index] = current.copyWith(leida: true);
    _noLeidasCount = (_noLeidasCount - 1).clamp(0, 999999);
    notifyListeners();

    try {
      await ApiService.post<Map<String, dynamic>>(
        '${AppConstants.notificationsEndpoint}$id/leer/',
      );
      await cargarConteoNoLeidas();
    } catch (_) {
      _notificaciones[index] = current;
      _noLeidasCount += 1;
      notifyListeners();
    }
  }

  Future<void> marcarTodasLeidas() async {
    if (_notificaciones.isEmpty && _noLeidasCount == 0) {
      return;
    }

    final previous = List<NotificacionModel>.from(_notificaciones);
    for (var i = 0; i < _notificaciones.length; i++) {
      _notificaciones[i] = _notificaciones[i].copyWith(leida: true);
    }
    _noLeidasCount = 0;
    notifyListeners();

    try {
      await ApiService.post<Map<String, dynamic>>(
        '${AppConstants.notificationsEndpoint}leer-todas/',
      );
      await cargarConteoNoLeidas();
    } catch (_) {
      _notificaciones
        ..clear()
        ..addAll(previous);
      _noLeidasCount = previous.where((item) => !item.leida).length;
      notifyListeners();
    }
  }

  Future<int?> crearAviso({
    required String titulo,
    required String cuerpo,
    required String audiencia,
    required String tipo,
    List<String> destinatariosIds = const <String>[],
  }) async {
    _isCreatingNotice = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.post<Map<String, dynamic>>(
        AppConstants.createNoticeEndpoint,
        data: <String, dynamic>{
          'titulo': titulo.trim(),
          'cuerpo': cuerpo.trim(),
          'audiencia': audiencia.trim().toUpperCase(),
          'tipo': tipo.trim().toUpperCase(),
          if (destinatariosIds.isNotEmpty)
            'destinatarios_ids': destinatariosIds,
        },
      );
      final payload = _normalizeMap(response.data);
      _errorMessage = null;
      await cargarConteoNoLeidas();
      return _toInt(payload['total_destinatarios']) ?? 0;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
      return null;
    } catch (_) {
      _errorMessage = 'No fue posible enviar el aviso comunitario.';
      return null;
    } finally {
      _isCreatingNotice = false;
      notifyListeners();
    }
  }

  Future<void> cargarDestinatariosAviso() async {
    _isLoadingNoticeRecipients = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.get<Map<String, dynamic>>(
        AppConstants.noticeRecipientsEndpoint,
      );
      final payload = _normalizeMap(response.data);
      _residentesAviso
        ..clear()
        ..addAll(_parseDestinatarios(payload['residentes']));
      _vigilantesAviso
        ..clear()
        ..addAll(_parseDestinatarios(payload['vigilantes']));
      _administradoresAviso
        ..clear()
        ..addAll(_parseDestinatarios(payload['administradores']));
      _errorMessage = null;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
    } catch (_) {
      _errorMessage = 'No fue posible cargar los destinatarios del aviso.';
    } finally {
      _isLoadingNoticeRecipients = false;
      notifyListeners();
    }
  }

  void reset() {
    _notificaciones.clear();
    _isLoading = false;
    _isCreatingNotice = false;
    _isLoadingNoticeRecipients = false;
    _noLeidasCount = 0;
    _errorMessage = null;
    _residentesAviso.clear();
    _vigilantesAviso.clear();
    _administradoresAviso.clear();
    notifyListeners();
  }

  Map<String, dynamic> _normalizeMap(dynamic value) {
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

  int? _toInt(dynamic value) {
    if (value is int) {
      return value;
    }
    return int.tryParse(value?.toString() ?? '');
  }

  List<DestinatarioAvisoModel> _parseDestinatarios(dynamic value) {
    final raw = value is List ? value : <dynamic>[];
    return raw
        .map((item) => DestinatarioAvisoModel.fromJson(_normalizeMap(item)))
        .where((item) => item.id.isNotEmpty)
        .toList();
  }

  String _extractErrorMessage(DioException error) {
    if (_isNetworkError(error)) {
      return 'No se pudo conectar con el backend. Verifica que Django esté ejecutándose en http://10.0.2.2:8000.';
    }

    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.trim().isNotEmpty) {
        return detail;
      }
      final mensaje = data['mensaje'];
      if (mensaje is String && mensaje.trim().isNotEmpty) {
        return mensaje;
      }
      final nonFieldErrors = data['non_field_errors'];
      if (nonFieldErrors is List && nonFieldErrors.isNotEmpty) {
        return nonFieldErrors.first.toString();
      }
      for (final value in data.values) {
        if (value is List && value.isNotEmpty) {
          return value.first.toString();
        }
        if (value is String && value.trim().isNotEmpty) {
          return value;
        }
      }
    }
    return 'No fue posible completar la operación con notificaciones.';
  }

  bool _isNetworkError(DioException error) {
    return error.response == null ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError;
  }
}
