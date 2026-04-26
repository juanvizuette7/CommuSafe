import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  NotificationService._();

  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    const androidSettings = AndroidInitializationSettings(
      '@mipmap/ic_launcher',
    );
    const settings = InitializationSettings(android: androidSettings);
    await _plugin.initialize(settings);
  }

  static Future<void> showBasicNotification({
    required int id,
    required String title,
    required String body,
  }) {
    return _plugin.show(
      id,
      title,
      body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'commusafe_alertas',
          'Alertas de CommuSafe',
          channelDescription: 'Canal principal de notificaciones de CommuSafe.',
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
    );
  }
}
