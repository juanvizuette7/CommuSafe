import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_constants.dart';
import '../../core/localization/app_localizations.dart';
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
    if (location.startsWith('/perfil') || location.startsWith('/ajustes')) {
      return 3;
    }
    return 0;
  }

  bool _showTopAppBar(String location) {
    return location.startsWith('/perfil') || location.startsWith('/ajustes');
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
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);
    final roleIcon = usuario?.esAdmin == true
        ? Icons.admin_panel_settings_rounded
        : usuario?.esVigilante == true
        ? Icons.security_rounded
        : Icons.home_rounded;

    return Scaffold(
      appBar: _showTopAppBar(currentLocation)
          ? AppBar(
              title: Text(
                currentLocation.startsWith('/ajustes')
                    ? l10n.tr('Ajustes', 'Settings')
                    : l10n.tr('Perfil', 'Profile'),
              ),
            )
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
                    gradient: LinearGradient(
                      colors: <Color>[theme.primary, theme.accent],
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
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 7,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.18),
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            Icon(roleIcon, color: Colors.white, size: 16),
                            const SizedBox(width: 6),
                            Text(
                              usuario?.rolLegible ??
                                  l10n.tr(
                                    'Sesion no disponible',
                                    'Session unavailable',
                                  ),
                              style: Theme.of(context).textTheme.labelMedium
                                  ?.copyWith(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w900,
                                  ),
                            ),
                          ],
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
                  leading: const Icon(Icons.tune_rounded),
                  title: Text(
                    l10n.tr('Ajustes de experiencia', 'Experience settings'),
                  ),
                  subtitle: Text(
                    l10n.tr(
                      'Contraste, color, letra e idioma',
                      'Contrast, color, text and language',
                    ),
                  ),
                  onTap: () {
                    Navigator.of(context).pop();
                    context.push('/ajustes');
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.contact_phone_rounded),
                  title: Text(
                    l10n.tr('Contactos de emergencia', 'Emergency contacts'),
                  ),
                  subtitle: Text(
                    l10n.tr(
                      'Accesos rapidos del conjunto',
                      'Community quick access',
                    ),
                  ),
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
                    title: Text(l10n.tr('Crear aviso', 'Create notice')),
                    subtitle: Text(
                      l10n.tr(
                        'Enviar alertas a residentes',
                        'Send alerts to residents',
                      ),
                    ),
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
                  title: Text(l10n.tr('Cerrar sesion', 'Log out')),
                  subtitle: Text(
                    l10n.tr(
                      'Borra credenciales guardadas',
                      'Clear saved credentials',
                    ),
                  ),
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
          BottomNavigationBarItem(
            icon: const Icon(Icons.warning_amber_rounded),
            label: l10n.tr('Incidentes', 'Incidents'),
          ),
          BottomNavigationBarItem(
            icon: Badge(
              isLabelVisible: unreadCount > 0,
              backgroundColor: AppColors.danger,
              label: Text(unreadCount > 99 ? '99+' : unreadCount.toString()),
              child: const Icon(Icons.notifications_outlined),
            ),
            label: l10n.tr('Alertas', 'Alerts'),
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.smart_toy_outlined),
            label: l10n.tr('Asistente', 'Assistant'),
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.person_outline_rounded),
            label: l10n.tr('Perfil', 'Profile'),
          ),
        ],
      ),
    );
  }
}
