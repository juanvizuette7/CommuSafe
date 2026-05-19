import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import 'app.dart';
import 'core/services/api_service.dart';
import 'core/services/firebase_messaging_service.dart';
import 'core/services/notification_service.dart';
import 'features/auth/providers/auth_provider.dart';
import 'features/incidentes/providers/incidente_provider.dart';
import 'features/notificaciones/providers/notificacion_provider.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('es_CO');
  Intl.defaultLocale = 'es_CO';
  FirebaseMessagingService.registerBackgroundHandler();
  await ApiService.init();
  await NotificationService.init();
  await FirebaseMessagingService.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthProvider>(create: (_) => AuthProvider()),
        ChangeNotifierProvider<IncidenteProvider>(
          create: (_) => IncidenteProvider(),
        ),
        ChangeNotifierProvider<NotificacionProvider>(
          create: (_) => NotificacionProvider(),
        ),
      ],
      child: const CommuSafeApp(),
    ),
  );
}
