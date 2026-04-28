import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../constants/app_constants.dart';
import 'api_service.dart';
import 'navigation_service.dart';
import 'notification_service.dart';
import 'storage_service.dart';

@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

class FirebaseMessagingService {
  FirebaseMessagingService._();

  static StreamSubscription<String>? _tokenRefreshSubscription;
  static bool _initialized = false;
  static bool _tokenRefreshListenerRegistered = false;

  static void registerBackgroundHandler() {
    FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);
  }

  static Future<void> init() async {
    if (_initialized) {
      return;
    }

    await Firebase.initializeApp();
    await FirebaseMessaging.instance.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);

    final initialMessage = await FirebaseMessaging.instance.getInitialMessage();
    if (initialMessage != null) {
      _handleMessageOpenedApp(initialMessage);
    }

    registerTokenRefreshSync();
    _initialized = true;
  }

  static Future<String?> getToken() {
    return FirebaseMessaging.instance.getToken();
  }

  static void registerTokenRefreshSync() {
    if (_tokenRefreshListenerRegistered) {
      return;
    }

    _tokenRefreshListenerRegistered = true;
    _tokenRefreshSubscription = FirebaseMessaging.instance.onTokenRefresh
        .listen((String token) {
          unawaited(syncTokenWithBackend(token: token));
        });
  }

  static Future<void> syncTokenWithBackend({String? token}) async {
    try {
      final hasSession = await StorageService.hasActiveSession();
      if (!hasSession) {
        return;
      }

      final fcmToken = token ?? await getToken();
      if (fcmToken == null || fcmToken.trim().isEmpty) {
        return;
      }

      await ApiService.post<Map<String, dynamic>>(
        AppConstants.fcmEndpoint,
        data: <String, dynamic>{'fcm_token': fcmToken.trim()},
      );
    } catch (error, stackTrace) {
      debugPrint('No se pudo sincronizar el token FCM: $error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }

  static Future<void> dispose() async {
    await _tokenRefreshSubscription?.cancel();
    _tokenRefreshSubscription = null;
    _tokenRefreshListenerRegistered = false;
    _initialized = false;
  }

  static Future<void> _handleForegroundMessage(RemoteMessage message) async {
    final notification = message.notification;
    final title =
        notification?.title ??
        message.data['titulo']?.toString() ??
        message.data['title']?.toString() ??
        'Notificacion de CommuSafe';
    final body =
        notification?.body ??
        message.data['cuerpo']?.toString() ??
        message.data['body']?.toString() ??
        'Tienes una nueva actualizacion en CommuSafe.';

    await NotificationService.showBasicNotification(
      id: DateTime.now().millisecondsSinceEpoch.remainder(100000),
      title: title,
      body: body,
    );
  }

  static void _handleMessageOpenedApp(RemoteMessage message) {
    final incidenteId =
        message.data['incidente_id']?.toString() ??
        message.data['incident_id']?.toString() ??
        '';
    AppNavigationService.abrirIncidente(incidenteId);
  }
}
