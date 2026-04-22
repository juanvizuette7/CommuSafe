import 'package:flutter/foundation.dart';

import '../../../core/services/storage_service.dart';
import '../models/usuario_model.dart';

class AuthProvider extends ChangeNotifier {
  AuthProvider() {
    _loadStoredSession();
  }

  bool _loading = true;
  UsuarioModel? _usuario;

  bool get loading => _loading;
  UsuarioModel? get usuario => _usuario;
  bool get hasSession => _usuario != null;

  Future<void> _loadStoredSession() async {
    _loading = true;
    notifyListeners();

    final userData = await StorageService.getUserData();
    if (userData != null) {
      _usuario = UsuarioModel.fromJson(userData);
    }

    _loading = false;
    notifyListeners();
  }

  Future<void> refreshSession() async {
    await _loadStoredSession();
  }

  Future<void> setSession({
    required String accessToken,
    required String refreshToken,
    required UsuarioModel usuario,
  }) async {
    await StorageService.saveTokens(
      accessToken: accessToken,
      refreshToken: refreshToken,
    );
    await StorageService.saveUserData(usuario.toJson());
    _usuario = usuario;
    notifyListeners();
  }

  Future<void> clearSession() async {
    await StorageService.clearSession();
    _usuario = null;
    notifyListeners();
  }
}
