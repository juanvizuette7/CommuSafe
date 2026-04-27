import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/empty_state_card.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/notificacion_model.dart';
import '../providers/notificacion_provider.dart';

class NotificacionesScreen extends StatefulWidget {
  const NotificacionesScreen({super.key});

  @override
  State<NotificacionesScreen> createState() => _NotificacionesScreenState();
}

class _NotificacionesScreenState extends State<NotificacionesScreen> {
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initialized) {
      return;
    }
    _initialized = true;
    final provider = context.read<NotificacionProvider>();
    Future<void>.microtask(() async {
      provider.startPolling();
      await provider.cargarNotificaciones();
    });
  }

  Future<void> _onNotificationTap(NotificacionModel item) async {
    final provider = context.read<NotificacionProvider>();
    await provider.marcarLeida(item.id);

    if (!mounted) {
      return;
    }

    final incidenteId = item.incidenteRelacionado;
    if (incidenteId != null && incidenteId.isNotEmpty) {
      context.push('/incidentes/$incidenteId');
      return;
    }

    await _showNotificationDetail(item);
  }

  Future<void> _showNotificationDetail(NotificacionModel item) async {
    final color = _notificationColor(item);

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (BuildContext context) {
        return SafeArea(
          child: Container(
            margin: const EdgeInsets.all(14),
            padding: const EdgeInsets.fromLTRB(22, 14, 22, 22),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(28),
              boxShadow: <BoxShadow>[
                BoxShadow(
                  color: AppColors.primary.withValues(alpha: 0.18),
                  blurRadius: 26,
                  offset: const Offset(0, 14),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Center(
                  child: Container(
                    width: 46,
                    height: 5,
                    decoration: BoxDecoration(
                      color: AppColors.muted,
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Container(
                      height: 56,
                      width: 56,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: <Color>[
                            color,
                            color.withValues(alpha: 0.72),
                          ],
                        ),
                      ),
                      child: Icon(
                        item.iconoPorTipo(),
                        color: Colors.white,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            item.tipoLabel,
                            style: Theme.of(context).textTheme.labelLarge
                                ?.copyWith(
                                  color: color,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: 0.2,
                                ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            item.titulo,
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(
                                  color: AppColors.textPrimary,
                                  fontWeight: FontWeight.w900,
                                  height: 1.08,
                                ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            item.tiempoRelativo,
                            style: Theme.of(context).textTheme.labelMedium
                                ?.copyWith(
                                  color: AppColors.textSecondary,
                                  fontWeight: FontWeight.w700,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.muted),
                  ),
                  child: Text(
                    item.cuerpo,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppColors.textPrimary,
                      height: 1.35,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.check_rounded),
                    label: const Text('Entendido'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _goToCreateNotice() async {
    final created = await context.push<bool>('/notificaciones/crear');
    if (!mounted || created != true) {
      return;
    }
    await context.read<NotificacionProvider>().cargarNotificaciones();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<NotificacionProvider>();
    final usuario = context.watch<AuthProvider>().usuarioActual;
    final canCreateNotice =
        usuario?.esAdmin == true || usuario?.esVigilante == true;
    final items = provider.notificaciones;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Notificaciones'),
        actions: <Widget>[
          if (canCreateNotice)
            IconButton(
              onPressed: _goToCreateNotice,
              icon: const Icon(Icons.add_alert_rounded),
              tooltip: 'Crear aviso',
            ),
          TextButton(
            onPressed: provider.noLeidasCount == 0
                ? null
                : () => provider.marcarTodasLeidas(),
            child: const Text(
              'Marcar todas leídas',
              style: TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
      floatingActionButton: canCreateNotice
          ? FloatingActionButton.extended(
              onPressed: _goToCreateNotice,
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.campaign_rounded),
              label: const Text('Crear aviso'),
            )
          : null,
      body: RefreshIndicator(
        onRefresh: provider.cargarNotificaciones,
        child: provider.isLoading && items.isEmpty
            ? const _NotificationsLoading()
            : provider.errorMessage != null && items.isEmpty
            ? _NotificationsError(
                message: provider.errorMessage!,
                onRetry: provider.cargarNotificaciones,
              )
            : items.isEmpty
            ? const _EmptyNotifications()
            : ListView.separated(
                physics: const AlwaysScrollableScrollPhysics(
                  parent: BouncingScrollPhysics(),
                ),
                padding: EdgeInsets.fromLTRB(
                  16,
                  18,
                  16,
                  canCreateNotice ? 104 : 28,
                ),
                itemCount: items.length,
                separatorBuilder: (_, __) => const SizedBox(height: 12),
                itemBuilder: (BuildContext context, int index) {
                  final item = items[index];
                  return Dismissible(
                    key: ValueKey<String>(item.id),
                    direction: item.leida
                        ? DismissDirection.none
                        : DismissDirection.endToStart,
                    confirmDismiss: (_) async {
                      await provider.marcarLeida(item.id);
                      return false;
                    },
                    background: Container(
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.only(right: 22),
                      decoration: BoxDecoration(
                        color: AppColors.success,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Icon(
                        Icons.done_all_rounded,
                        color: Colors.white,
                      ),
                    ),
                    child: _NotificationTile(
                      item: item,
                      onTap: () => _onNotificationTap(item),
                    ),
                  );
                },
              ),
      ),
    );
  }
}

Color _notificationColor(NotificacionModel item) {
  switch (item.tipo.toUpperCase()) {
    case 'EMERGENCIA':
      return AppColors.danger;
    case 'INCIDENTE_NUEVO':
      return AppColors.inProgress;
    case 'CAMBIO_ESTADO':
      return AppColors.success;
    case 'AVISO_ADMIN':
      return AppColors.warning;
    default:
      return AppColors.primary;
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item, required this.onTap});

  final NotificacionModel item;
  final VoidCallback onTap;

  Color _typeColor() {
    return _notificationColor(item);
  }

  @override
  Widget build(BuildContext context) {
    final color = _typeColor();

    return Material(
      color: item.leida
          ? Colors.white
          : AppColors.inProgress.withValues(alpha: 0.08),
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                height: 48,
                width: 48,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: color.withValues(alpha: 0.14),
                ),
                child: Icon(item.iconoPorTipo(), color: color),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            item.titulo,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.titleSmall
                                ?.copyWith(
                                  fontWeight: item.leida
                                      ? FontWeight.w600
                                      : FontWeight.w900,
                                  color: AppColors.textPrimary,
                                ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Text(
                          item.tiempoRelativo,
                          style: Theme.of(context).textTheme.labelSmall
                              ?.copyWith(
                                color: AppColors.textSecondary,
                                fontWeight: FontWeight.w700,
                              ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      item.cuerpo,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    if (item.incidenteTitulo != null) ...<Widget>[
                      const SizedBox(height: 8),
                      Text(
                        item.incidenteTitulo!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.labelMedium
                            ?.copyWith(
                              color: color,
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationsLoading extends StatelessWidget {
  const _NotificationsLoading();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 5,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (BuildContext context, int index) {
        return Container(
          height: 82,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Center(child: CircularProgressIndicator()),
        );
      },
    );
  }
}

class _EmptyNotifications extends StatelessWidget {
  const _EmptyNotifications();

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(20),
      children: <Widget>[
        const SizedBox(height: 120),
        const EmptyStateCard(
          icon: Icons.notifications_none_rounded,
          title: 'Sin notificaciones por ahora',
          message:
              'Cuando cambie el estado de un incidente o llegue un aviso, aparecerá aquí.',
        ),
      ],
    );
  }
}

class _NotificationsError extends StatelessWidget {
  const _NotificationsError({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(20),
      children: <Widget>[
        const SizedBox(height: 120),
        EmptyStateCard(
          icon: Icons.cloud_off_rounded,
          title: 'No se pudieron cargar las alertas',
          message: message,
          actionLabel: 'Reintentar',
          onAction: onRetry,
          toneColor: AppColors.danger,
        ),
      ],
    );
  }
}
