import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'features/asistente/screens/chat_screen.dart';
import 'features/auth/providers/auth_provider.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/auth/screens/perfil_screen.dart';
import 'features/emergencias/screens/contactos_emergencia_screen.dart';
import 'features/incidentes/screens/crear_incidente_screen.dart';
import 'features/incidentes/screens/detalle_incidente_screen.dart';
import 'features/incidentes/screens/lista_incidentes_screen.dart';
import 'features/notificaciones/screens/crear_aviso_screen.dart';
import 'features/notificaciones/screens/notificaciones_screen.dart';
import 'shared/layouts/main_layout.dart';

class CommuSafeApp extends StatefulWidget {
  const CommuSafeApp({super.key});

  @override
  State<CommuSafeApp> createState() => _CommuSafeAppState();
}

class _CommuSafeAppState extends State<CommuSafeApp> {
  GoRouter? _router;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _router ??= AppRouter.create(context.read<AuthProvider>());
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'CommuSafe',
      theme: AppTheme.lightTheme,
      routerConfig: _router!,
    );
  }
}

class AppRouter {
  AppRouter._();

  static GoRouter create(AuthProvider authProvider) {
    return GoRouter(
      initialLocation: '/',
      refreshListenable: authProvider,
      routes: <RouteBase>[
        GoRoute(
          path: '/',
          builder: (BuildContext context, GoRouterState state) {
            return const _SessionBootstrapScreen();
          },
        ),
        GoRoute(
          path: '/login',
          builder: (BuildContext context, GoRouterState state) {
            return const LoginScreen();
          },
        ),
        ShellRoute(
          builder: (BuildContext context, GoRouterState state, Widget child) {
            return MainLayout(child: child);
          },
          routes: <RouteBase>[
            GoRoute(
              path: '/incidentes',
              builder: (BuildContext context, GoRouterState state) {
                return const ListaIncidentesScreen();
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
                    return DetalleIncidenteScreen(incidenteId: incidenteId);
                  },
                ),
              ],
            ),
            GoRoute(
              path: '/notificaciones',
              builder: (BuildContext context, GoRouterState state) {
                return const NotificacionesScreen();
              },
              routes: <RouteBase>[
                GoRoute(
                  path: 'crear',
                  builder: (BuildContext context, GoRouterState state) {
                    return const CrearAvisoScreen();
                  },
                ),
              ],
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
                return const ChatScreen();
              },
            ),
            GoRoute(
              path: '/emergencias',
              builder: (BuildContext context, GoRouterState state) {
                return const ContactosEmergenciaScreen();
              },
            ),
          ],
        ),
      ],
      redirect: (BuildContext context, GoRouterState state) {
        final location = state.matchedLocation;
        final isProtectedRoute = location != '/' && location != '/login';

        if (authProvider.isInitializing && location != '/') {
          return '/';
        }

        if (!authProvider.hasSession && isProtectedRoute) {
          return '/login';
        }

        if (authProvider.hasSession && location == '/login') {
          return '/incidentes';
        }

        return null;
      },
    );
  }
}

class _SessionBootstrapScreen extends StatefulWidget {
  const _SessionBootstrapScreen();

  @override
  State<_SessionBootstrapScreen> createState() =>
      _SessionBootstrapScreenState();
}

class _SessionBootstrapScreenState extends State<_SessionBootstrapScreen> {
  late Future<bool> _sessionFuture;
  bool _hasBootstrapped = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_hasBootstrapped) {
      return;
    }
    _hasBootstrapped = true;
    final authProvider = context.read<AuthProvider>();
    _sessionFuture = Future<bool>.microtask(authProvider.initSession);
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.read<AuthProvider>();

    return FutureBuilder<bool>(
      future: _sessionFuture,
      builder: (BuildContext context, AsyncSnapshot<bool> snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const _StartupLoadingScreen();
        }

        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!context.mounted) {
            return;
          }

          if (authProvider.hasSession) {
            context.go('/incidentes');
          } else {
            context.go('/login');
          }
        });

        return const _StartupLoadingScreen();
      },
    );
  }
}

class _StartupLoadingScreen extends StatelessWidget {
  const _StartupLoadingScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: <Color>[AppColors.primary, AppColors.accent],
          ),
        ),
        child: const Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              CircularProgressIndicator(color: Colors.white, strokeWidth: 2.6),
              SizedBox(height: 20),
              Text(
                'Cargando sesión de CommuSafe...',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
