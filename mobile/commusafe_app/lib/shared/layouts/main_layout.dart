import 'package:badges/badges.dart' as badges;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_constants.dart';
import '../../core/theme/app_theme.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/notificaciones/providers/notificaciones_provider.dart';

class MainLayout extends StatelessWidget {
  const MainLayout({
    super.key,
    required this.child,
  });

  final Widget child;

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
    if (location.startsWith('/incidentes/crear')) {
      return 'Nuevo incidente';
    }
    if (location.startsWith('/incidentes/') && location != '/incidentes') {
      return 'Detalle del incidente';
    }
    if (location.startsWith('/notificaciones')) {
      return 'Notificaciones';
    }
    if (location.startsWith('/asistente')) {
      return 'Asistente virtual';
    }
    if (location.startsWith('/perfil')) {
      return 'Perfil';
    }
    if (location.startsWith('/emergencias')) {
      return 'Contactos de emergencia';
    }
    return 'Incidentes';
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
    await context.read<AuthProvider>().clearSession();
    if (!context.mounted) {
      return;
    }
    context.read<NotificacionesProvider>().reset();
    context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final state = GoRouterState.of(context);
    final currentLocation = state.uri.toString();
    final notificationsProvider = context.watch<NotificacionesProvider>();
    final authProvider = context.watch<AuthProvider>();
    final usuario = authProvider.usuario;
    final currentIndex = _currentIndexForLocation(currentLocation);

    return Scaffold(
      appBar: AppBar(
        title: Text(_titleForLocation(currentLocation)),
      ),
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
                      colors: <Color>[
                        AppColors.primary,
                        AppColors.accent,
                      ],
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: Colors.white.withValues(alpha: 0.18),
                        child: Text(
                          usuario == null
                              ? 'CS'
                              : '${usuario.nombre.characters.first}${usuario.apellido.characters.first}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                            fontSize: 18,
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        usuario?.nombreCompleto ?? AppConstants.appName,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        usuario?.rolLegible ??
                            'Sesión pendiente de autenticación real',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.white.withValues(alpha: 0.78),
                            ),
                      ),
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
                const Divider(height: 32),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.logout_rounded, color: AppColors.danger),
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
      body: child,
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
            icon: badges.Badge(
              showBadge: notificationsProvider.noLeidasCount > 0,
              badgeContent: Text(
                notificationsProvider.noLeidasCount.toString(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                ),
              ),
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
