import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';
import '../models/usuario_model.dart';

class AuthProvider extends ChangeNotifier {
  UsuarioModel? _usuarioActual;
  bool _isLoading = false;
  bool _isInitializing = true;
  String? _errorMessage;
  Future<bool>? _initializationFuture;

  UsuarioModel? get usuarioActual => _usuarioActual;
  bool get isLoading => _isLoading;
  bool get isInitializing => _isInitializing;
  String? get errorMessage => _errorMessage;
  bool get hasSession => _usuarioActual != null;

  Future<bool> initSession({bool force = false}) {
    if (force) {
      _initializationFuture = null;
    }

    return _initializationFuture ??= _performInitSession();
  }

  Future<bool> _performInitSession() async {
    _isInitializing = true;
    _errorMessage = null;
    notifyListeners();

    final accessToken = await StorageService.getAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      _usuarioActual = null;
      _isInitializing = false;
      notifyListeners();
      return false;
    }

    try {
      await cargarPerfil(notifyLoading: false);
    } catch (_) {
      final storedUser = await StorageService.getUserData();
      if (storedUser != null && await StorageService.hasActiveSession()) {
        _usuarioActual = UsuarioModel.fromJson(storedUser);
      } else {
        await StorageService.clearSession();
        _usuarioActual = null;
      }
    }

    _isInitializing = false;
    notifyListeners();
    return hasSession;
  }

  Future<bool> login({required String email, required String password}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.post<Map<String, dynamic>>(
        AppConstants.loginEndpoint,
        data: <String, dynamic>{
          'email': email.trim().toLowerCase(),
          'password': password,
        },
        options: Options(extra: <String, dynamic>{'omitAuth': true}),
      );

      final payload = response.data ?? <String, dynamic>{};
      final accessToken = payload['access']?.toString() ?? '';
      final refreshToken = payload['refresh']?.toString() ?? '';
      final rawUser = payload['usuario'];

      if (accessToken.isEmpty || refreshToken.isEmpty || rawUser is! Map) {
        _errorMessage =
            'La respuesta del servidor no contiene la información de autenticación necesaria.';
        _isLoading = false;
        notifyListeners();
        return false;
      }

      await StorageService.saveTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );

      final usuarioParcial = UsuarioModel.fromJson(
        Map<String, dynamic>.from(rawUser),
      );
      await StorageService.saveUserData(usuarioParcial.toJson());
      _usuarioActual = usuarioParcial;
      _isInitializing = false;
      notifyListeners();

      try {
        await cargarPerfil(notifyLoading: false);
      } catch (_) {
        // Si el perfil detallado falla, se conserva la información mínima del login.
      }

      _initializationFuture = Future<bool>.value(true);
      _isLoading = false;
      notifyListeners();
      return true;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (_) {
      _errorMessage =
          'No fue posible iniciar sesión. Intenta nuevamente en unos segundos.';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> cargarPerfil({bool notifyLoading = true}) async {
    if (notifyLoading) {
      _isLoading = true;
      _errorMessage = null;
      notifyListeners();
    }

    try {
      final response = await ApiService.get<Map<String, dynamic>>(
        AppConstants.profileEndpoint,
      );
      final payload = response.data ?? <String, dynamic>{};
      final usuario = UsuarioModel.fromJson(payload);
      _usuarioActual = usuario;
      await StorageService.saveUserData(usuario.toJson());
      _errorMessage = null;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
      rethrow;
    } finally {
      if (notifyLoading) {
        _isLoading = false;
      }
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await StorageService.clearSession();
    _usuarioActual = null;
    _isLoading = false;
    _isInitializing = false;
    _errorMessage = null;
    _initializationFuture = Future<bool>.value(false);
    notifyListeners();
  }

  void clearError() {
    if (_errorMessage == null) {
      return;
    }

    _errorMessage = null;
    notifyListeners();
  }

  String _extractErrorMessage(DioException error) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.trim().isNotEmpty) {
        return detail;
      }

      final nonFieldErrors = data['non_field_errors'];
      if (nonFieldErrors is List && nonFieldErrors.isNotEmpty) {
        return nonFieldErrors.first.toString();
      }

      for (final entry in data.entries) {
        final value = entry.value;
        if (value is List && value.isNotEmpty) {
          return value.first.toString();
        }
        if (value is String && value.trim().isNotEmpty) {
          return value;
        }
      }
    }

    if (data is String && data.trim().isNotEmpty) {
      return data;
    }

    return 'No fue posible completar la autenticación. Verifica tus credenciales.';
  }
}
