import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class StorageService {
  StorageService._();

  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userDataKey = 'user_data';
  static const String _settingsPrefix = 'app_setting_';

  static const FlutterSecureStorage _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static Future<void> saveAccessToken(String token) {
    return _storage.write(key: _accessTokenKey, value: token);
  }

  static Future<void> saveRefreshToken(String token) {
    return _storage.write(key: _refreshTokenKey, value: token);
  }

  static Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await Future.wait(<Future<void>>[
      saveAccessToken(accessToken),
      saveRefreshToken(refreshToken),
    ]);
  }

  static Future<String?> getAccessToken() {
    return _storage.read(key: _accessTokenKey);
  }

  static Future<String?> getRefreshToken() {
    return _storage.read(key: _refreshTokenKey);
  }

  static Future<void> saveUserData(Map<String, dynamic> userJson) {
    return _storage.write(key: _userDataKey, value: jsonEncode(userJson));
  }

  static Future<Map<String, dynamic>?> getUserData() async {
    final rawValue = await _storage.read(key: _userDataKey);
    if (rawValue == null || rawValue.isEmpty) {
      return null;
    }

    final decoded = jsonDecode(rawValue);
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }

    return null;
  }

  static Future<bool> hasActiveSession() async {
    final accessToken = await getAccessToken();
    return accessToken != null && accessToken.isNotEmpty;
  }

  static Future<String?> readSetting(String key) {
    return _storage.read(key: '$_settingsPrefix$key');
  }

  static Future<void> saveSetting(String key, String value) {
    return _storage.write(key: '$_settingsPrefix$key', value: value);
  }

  static Future<void> deleteSetting(String key) {
    return _storage.delete(key: '$_settingsPrefix$key');
  }

  static Future<void> clearSession() {
    return Future.wait(<Future<void>>[
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _refreshTokenKey),
      _storage.delete(key: _userDataKey),
    ]);
  }
}
