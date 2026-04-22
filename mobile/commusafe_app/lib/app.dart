import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'core/services/storage_service.dart';
import 'core/theme/app_theme.dart';
import 'features/asistente/screens/asistente_screen.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/auth/screens/perfil_screen.dart';
import 'features/emergencias/screens/emergencias_screen.dart';
import 'features/incidentes/screens/crear_incidente_screen.dart';
import 'features/incidentes/screens/incidente_detalle_screen.dart';
import 'features/incidentes/screens/incidentes_list_screen.dart';
import 'features/notificaciones/screens/notificaciones_screen.dart';
import 'shared/layouts/main_layout.dart';

class CommuSafeApp extends StatelessWidget {
  const CommuSafeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'CommuSafe',
      theme: AppTheme.lightTheme,
      routerConfig: AppRouter.router,
    );
  }
}

class AppRouter {
  static final GoRouter router = GoRouter(
    initialLocation: '/',
    routes: <RouteBase>[
      GoRoute(
        path: '/',
        redirect: (_, __) async {
          final hasSession = await StorageService.hasActiveSession();
          return hasSession ? '/incidentes' : '/login';
        },
      ),
      GoRoute(
        path: '/login',
        builder: (BuildContext context, GoRouterState state) {
          return const LoginScreen();
        },
      ),
      ShellRoute(
        builder: (
          BuildContext context,
          GoRouterState state,
          Widget child,
        ) {
          return MainLayout(child: child);
        },
        routes: <RouteBase>[
          GoRoute(
            path: '/incidentes',
            builder: (BuildContext context, GoRouterState state) {
              return const IncidentesListScreen();
            },
            routes: <RouteBase>[
              GoRoute(
                path: 'crear',
                builder: (BuildContext context, GoRouterState state) {
                  return const CrearIncidenteScreen();
                },
              ),
              GoRoute(
                path: ':id',
                builder: (BuildContext context, GoRouterState state) {
                  final incidenteId = state.pathParameters['id'] ?? '';
                  return IncidenteDetalleScreen(incidenteId: incidenteId);
                },
              ),
            ],
          ),
          GoRoute(
            path: '/notificaciones',
            builder: (BuildContext context, GoRouterState state) {
              return const NotificacionesScreen();
            },
          ),
          GoRoute(
            path: '/perfil',
            builder: (BuildContext context, GoRouterState state) {
              return const PerfilScreen();
            },
          ),
          GoRoute(
            path: '/asistente',
            builder: (BuildContext context, GoRouterState state) {
              return const AsistenteScreen();
            },
          ),
          GoRoute(
            path: '/emergencias',
            builder: (BuildContext context, GoRouterState state) {
              return const EmergenciasScreen();
            },
          ),
        ],
      ),
    ],
    redirect: (BuildContext context, GoRouterState state) async {
      final hasSession = await StorageService.hasActiveSession();
      final isLoginRoute = state.matchedLocation == '/login';

      if (!hasSession && !isLoginRoute) {
        return '/login';
      }

      if (hasSession && isLoginRoute) {
        return '/incidentes';
      }

      return null;
    },
  );
}
