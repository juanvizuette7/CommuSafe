import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  NotificationService._();

  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) {
      return;
    }

    const androidSettings = AndroidInitializationSettings(
      '@mipmap/ic_launcher',
    );
    const settings = InitializationSettings(android: androidSettings);
    try {
      await _plugin.initialize(settings);
      _initialized = true;
    } catch (_) {
      _initialized = false;
    }
  }

  static Future<bool> showBasicNotification({
    required int id,
    required String title,
    required String body,
  }) async {
    if (!_initialized) {
      await init();
    }

    if (!_initialized) {
      return false;
    }

    try {
      await _plugin.show(
        id,
        title,
        body,
        const NotificationDetails(
          android: AndroidNotificationDetails(
            'commusafe_alertas',
            'Alertas de CommuSafe',
            channelDescription:
                'Canal principal de notificaciones de CommuSafe.',
            importance: Importance.high,
            priority: Priority.high,
          ),
        ),
      );
      return true;
    } catch (_) {
      return false;
    }
  }
}
