class AppConstants {
  const AppConstants._();

  static const String appName = 'CommuSafe';
  static const String residentialComplexName = 'Remansos del Norte';
  static const String baseUrl = 'http://10.0.2.2:8000';

  static const Duration requestTimeout = Duration(seconds: 30);

  static const String loginEndpoint = '/api/auth/login/';
  static const String refreshEndpoint = '/api/auth/refresh/';
  static const String profileEndpoint = '/api/auth/perfil/';
  static const String fcmEndpoint = '/api/auth/fcm/';
  static const String usersEndpoint = '/api/auth/usuarios/';
  static const String incidentsEndpoint = '/api/incidentes/';
  static const String notificationsEndpoint = '/api/notificaciones/';
  static const String unreadNotificationsCountEndpoint =
      '/api/notificaciones/no-leidas-count/';
  static const String chatEndpoint = '/api/asistente/chat/';
}
