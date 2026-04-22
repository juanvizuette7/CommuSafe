import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import 'app.dart';
import 'core/services/api_service.dart';
import 'core/services/notification_service.dart';
import 'features/auth/providers/auth_provider.dart';
import 'features/incidentes/providers/incidentes_provider.dart';
import 'features/notificaciones/providers/notificaciones_provider.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('es_CO');
  Intl.defaultLocale = 'es_CO';
  await ApiService.init();
  await NotificationService.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthProvider>(create: (_) => AuthProvider()),
        ChangeNotifierProvider<IncidentesProvider>(
          create: (_) => IncidentesProvider(),
        ),
        ChangeNotifierProvider<NotificacionesProvider>(
          create: (_) => NotificacionesProvider(),
        ),
      ],
      child: const CommuSafeApp(),
    ),
  );
}
