import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../incidentes/providers/incidente_provider.dart';
import '../../notificaciones/providers/notificaciones_provider.dart';
import '../models/usuario_model.dart';
import '../providers/auth_provider.dart';

class PerfilScreen extends StatelessWidget {
  const PerfilScreen({super.key});

  Future<void> _logout(BuildContext context) async {
    final authProvider = context.read<AuthProvider>();
    final incidenteProvider = context.read<IncidenteProvider>();
    final notificacionesProvider = context.read<NotificacionesProvider>();

    await authProvider.logout();
    incidenteProvider.reset();
    notificacionesProvider.reset();
    if (!context.mounted) {
      return;
    }
    context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final usuario = authProvider.usuarioActual;

    if (usuario == null && authProvider.isInitializing) {
      return const Center(child: CircularProgressIndicator());
    }

    if (usuario == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'No fue posible cargar la información del perfil.',
            style: Theme.of(context).textTheme.titleMedium,
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => context.read<AuthProvider>().cargarPerfil(),
      child: ListView(
        padding: EdgeInsets.zero,
        children: <Widget>[
          _ProfileHeader(usuario: usuario),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
            child: Column(
              children: <Widget>[
                _ProfileInfoCard(
                  icon: Icons.alternate_email_rounded,
                  title: 'Correo electrónico',
                  value: usuario.email,
                ),
                const SizedBox(height: 14),
                _ProfileInfoCard(
                  icon: Icons.home_work_outlined,
                  title: 'Unidad residencial',
                  value: usuario.unidadResidencial?.trim().isNotEmpty == true
                      ? usuario.unidadResidencial!
                      : 'No registrada',
                ),
                const SizedBox(height: 14),
                _ProfileInfoCard(
                  icon: Icons.phone_outlined,
                  title: 'Teléfono',
                  value: usuario.telefono?.trim().isNotEmpty == true
                      ? usuario.telefono!
                      : 'No registrado',
                ),
                const SizedBox(height: 28),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _logout(context),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.danger,
                      foregroundColor: Colors.white,
                      minimumSize: const Size.fromHeight(54),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    icon: const Icon(Icons.logout_rounded),
                    label: const Text('Cerrar sesión'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({
    required this.usuario,
  });

  final UsuarioModel usuario;

  Color _badgeColor() {
    if (usuario.esAdmin) {
      return const Color(0xFF1D4ED8);
    }
    if (usuario.esVigilante) {
      return const Color(0xFF2563EB);
    }
    return AppColors.success;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 28, 24, 30),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[
            AppColors.primary,
            AppColors.accent,
          ],
        ),
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(30),
          bottomRight: Radius.circular(30),
        ),
      ),
      child: Column(
        children: <Widget>[
          Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(
                color: Colors.white.withValues(alpha: 0.35),
                width: 2,
              ),
            ),
            child: CircleAvatar(
              radius: 42,
              backgroundColor: Colors.white.withValues(alpha: 0.15),
              backgroundImage: usuario.fotoPerfilUrl != null
                  ? CachedNetworkImageProvider(usuario.fotoPerfilUrl!)
                  : null,
              child: usuario.fotoPerfilUrl == null
                  ? Text(
                      usuario.iniciales,
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                          ),
                    )
                  : null,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            usuario.nombreCompleto,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: _badgeColor().withValues(alpha: 0.22),
              borderRadius: BorderRadius.circular(999),
              border: Border.all(
                color: Colors.white.withValues(alpha: 0.16),
              ),
            ),
            child: Text(
              usuario.rolLegible,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileInfoCard extends StatelessWidget {
  const _ProfileInfoCard({
    required this.icon,
    required this.title,
    required this.value,
  });

  final IconData icon;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          children: <Widget>[
            Container(
              height: 48,
              width: 48,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: AppColors.primary),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textSecondary,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    value,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
