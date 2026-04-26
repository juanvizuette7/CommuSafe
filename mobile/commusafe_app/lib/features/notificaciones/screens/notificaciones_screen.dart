import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/empty_state_card.dart';
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
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<NotificacionProvider>();
    final items = provider.notificaciones;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Notificaciones'),
        actions: <Widget>[
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
      body: RefreshIndicator(
        onRefresh: provider.cargarNotificaciones,
        child: provider.isLoading && items.isEmpty
            ? const _NotificationsLoading()
            : items.isEmpty
            ? const _EmptyNotifications()
            : ListView.separated(
                physics: const AlwaysScrollableScrollPhysics(
                  parent: BouncingScrollPhysics(),
                ),
                padding: const EdgeInsets.fromLTRB(16, 18, 16, 28),
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

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item, required this.onTap});

  final NotificacionModel item;
  final VoidCallback onTap;

  Color _typeColor() {
    switch (item.tipo.toUpperCase()) {
      case 'EMERGENCIA':
        return AppColors.danger;
      case 'INCIDENTE_NUEVO':
        return AppColors.inProgress;
      case 'CAMBIO_ESTADO':
        return AppColors.success;
      case 'AVISO_ADMIN':
        return AppColors.textSecondary;
      default:
        return AppColors.primary;
    }
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
