import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_constants.dart';
import '../../core/theme/app_theme.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/incidentes/providers/incidente_provider.dart';
import '../../features/notificaciones/providers/notificacion_provider.dart';

class MainLayout extends StatefulWidget {
  const MainLayout({super.key, required this.child});

  final Widget child;

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  bool _notificationCountLoaded = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_notificationCountLoaded) {
      return;
    }
    _notificationCountLoaded = true;
    final authProvider = context.read<AuthProvider>();
    if (authProvider.hasSession) {
      context.read<NotificacionProvider>().cargarConteoNoLeidas();
    }
  }

  int _currentIndexForLocation(String location) {
    if (location.startsWith('/notificaciones')) {
      return 1;
    }
    if (location.startsWith('/asistente')) {
      return 2;
    }
    if (location.startsWith('/perfil')) {
      return 3;
    }
    return 0;
  }

  String _titleForLocation(String location) {
    if (location.startsWith('/perfil')) {
      return 'Perfil';
    }
    return 'CommuSafe';
  }

  bool _showTopAppBar(String location) {
    return location.startsWith('/perfil');
  }

  void _onNavigationTap(BuildContext context, int index) {
    switch (index) {
      case 0:
        context.go('/incidentes');
        break;
      case 1:
        context.go('/notificaciones');
        break;
      case 2:
        context.go('/asistente');
        break;
      case 3:
        context.go('/perfil');
        break;
    }
  }

  Future<void> _logout(BuildContext context) async {
    final authProvider = context.read<AuthProvider>();
    final incidenteProvider = context.read<IncidenteProvider>();
    final notificacionProvider = context.read<NotificacionProvider>();

    await authProvider.logout();
    incidenteProvider.reset();
    notificacionProvider.reset();
    if (!context.mounted) {
      return;
    }
    context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final state = GoRouterState.of(context);
    final currentLocation = state.uri.path;
    final notificationsProvider = context.watch<NotificacionProvider>();
    final authProvider = context.watch<AuthProvider>();
    final usuario = authProvider.usuarioActual;
    final currentIndex = _currentIndexForLocation(currentLocation);
    final unreadCount = notificationsProvider.noLeidasCount;

    return Scaffold(
      appBar: _showTopAppBar(currentLocation)
          ? AppBar(title: Text(_titleForLocation(currentLocation)))
          : null,
      drawer: Drawer(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(24),
                    gradient: const LinearGradient(
                      colors: <Color>[AppColors.primary, AppColors.accent],
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: Colors.white.withValues(alpha: 0.18),
                        backgroundImage: usuario?.fotoPerfilUrl != null
                            ? CachedNetworkImageProvider(
                                usuario!.fotoPerfilUrl!,
                              )
                            : null,
                        child: usuario?.fotoPerfilUrl == null
                            ? Text(
                                usuario?.iniciales ?? 'CS',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 18,
                                ),
                              )
                            : null,
                      ),
                      const SizedBox(height: 14),
                      Text(
                        usuario?.nombreCompleto ?? AppConstants.appName,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        usuario?.rolLegible ?? 'Sesión no disponible',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.white.withValues(alpha: 0.78),
                        ),
                      ),
                      if (usuario?.email != null) ...<Widget>[
                        const SizedBox(height: 8),
                        Text(
                          usuario!.email,
                          style: Theme.of(context).textTheme.bodySmall
                              ?.copyWith(
                                color: Colors.white.withValues(alpha: 0.86),
                              ),
                        ),
                      ],
                      if (usuario?.unidadResidencial != null &&
                          usuario!.unidadResidencial!
                              .trim()
                              .isNotEmpty) ...<Widget>[
                        const SizedBox(height: 4),
                        Text(
                          usuario.unidadResidencial!,
                          style: Theme.of(context).textTheme.bodySmall
                              ?.copyWith(
                                color: Colors.white.withValues(alpha: 0.74),
                              ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.contact_phone_rounded),
                  title: const Text('Contactos de emergencia'),
                  subtitle: const Text('Accesos rápidos del conjunto'),
                  onTap: () {
                    Navigator.of(context).pop();
                    context.push('/emergencias');
                  },
                ),
                if (usuario?.esAdmin == true ||
                    usuario?.esVigilante == true) ...<Widget>[
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.campaign_rounded),
                    title: const Text('Crear aviso'),
                    subtitle: const Text('Enviar alertas a residentes'),
                    onTap: () {
                      Navigator.of(context).pop();
                      context.push('/notificaciones/crear');
                    },
                  ),
                ],
                const Divider(height: 32),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(
                    Icons.logout_rounded,
                    color: AppColors.danger,
                  ),
                  title: const Text('Cerrar sesión'),
                  subtitle: const Text('Borra credenciales guardadas'),
                  onTap: () async {
                    Navigator.of(context).pop();
                    await _logout(context);
                  },
                ),
              ],
            ),
          ),
        ),
      ),
      body: widget.child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: currentIndex,
        type: BottomNavigationBarType.fixed,
        onTap: (int index) => _onNavigationTap(context, index),
        items: <BottomNavigationBarItem>[
          const BottomNavigationBarItem(
            icon: Icon(Icons.warning_amber_rounded),
            label: 'Incidentes',
          ),
          BottomNavigationBarItem(
            icon: Badge(
              isLabelVisible: unreadCount > 0,
              backgroundColor: AppColors.danger,
              label: Text(unreadCount > 99 ? '99+' : unreadCount.toString()),
              child: const Icon(Icons.notifications_outlined),
            ),
            label: 'Alertas',
          ),
          const BottomNavigationBarItem(
            icon: Icon(Icons.smart_toy_outlined),
            label: 'Asistente',
          ),
          const BottomNavigationBarItem(
            icon: Icon(Icons.person_outline_rounded),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}
