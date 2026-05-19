import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/aviso_banner.dart';
import '../../../shared/widgets/commusafe_animated_background.dart';
import '../../../shared/widgets/empty_state_card.dart';
import '../../../shared/widgets/incidente_card.dart';
import '../../auth/providers/auth_provider.dart';
import '../../notificaciones/providers/notificacion_provider.dart';
import '../providers/incidente_provider.dart';

class ListaIncidentesScreen extends StatefulWidget {
  const ListaIncidentesScreen({super.key});

  @override
  State<ListaIncidentesScreen> createState() => _ListaIncidentesScreenState();
}

class _ListaIncidentesScreenState extends State<ListaIncidentesScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _searchController = TextEditingController();
  Timer? _searchDebounce;
  bool _initialized = false;

  static const List<Map<String, String?>> _categories = <Map<String, String?>>[
    <String, String?>{'value': null, 'label': 'Todos'},
    <String, String?>{'value': 'SEGURIDAD', 'label': 'Seguridad'},
    <String, String?>{'value': 'CONVIVENCIA', 'label': 'Convivencia'},
    <String, String?>{'value': 'INFRAESTRUCTURA', 'label': 'Infraestructura'},
    <String, String?>{'value': 'EMERGENCIA', 'label': 'Emergencia'},
  ];

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_handleScroll);
    final notificacionProvider = context.read<NotificacionProvider>();
    Future<void>.microtask(notificacionProvider.cargarAvisosVigentes);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initialized) {
      return;
    }
    _initialized = true;
    final provider = context.read<IncidenteProvider>();
    _searchController.text = provider.busquedaActiva;
    Future<void>.microtask(() => provider.cargarIncidentes(refresh: true));
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _searchController.dispose();
    _scrollController
      ..removeListener(_handleScroll)
      ..dispose();
    super.dispose();
  }

  void _handleScroll() {
    if (!_scrollController.hasClients) {
      return;
    }

    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 320) {
      context.read<IncidenteProvider>().cargarMas();
    }
  }

  void _onSearchChanged(String value) {
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 450), () {
      if (!mounted) {
        return;
      }
      context.read<IncidenteProvider>().aplicarFiltro(
        categoria: context.read<IncidenteProvider>().categoriaActiva,
        busqueda: value,
      );
    });
  }

  Future<void> _clearFilters() async {
    _searchController.clear();
    await context.read<IncidenteProvider>().aplicarFiltro(
      categoria: null,
      busqueda: '',
    );
  }

  Future<void> _goToCreate() async {
    final created = await context.push<bool>('/incidentes/crear');
    if (!mounted) {
      return;
    }
    if (created == true) {
      await context.read<IncidenteProvider>().cargarIncidentes(refresh: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<IncidenteProvider>();
    final notificacionProvider = context.watch<NotificacionProvider>();
    final authProvider = context.watch<AuthProvider>();
    final usuario = authProvider.usuarioActual;
    final avisosVigentes = notificacionProvider.avisosVigentes;
    final canCreate =
        usuario?.esResidente == true || usuario?.esVigilante == true;
    final highPriorityCount = provider.incidentes
        .where((incidente) => incidente.prioridad.toUpperCase() == 'ALTA')
        .length;
    final activeCount = provider.incidentes
        .where(
          (incidente) =>
              incidente.estado.toUpperCase() != 'RESUELTO' &&
              incidente.estado.toUpperCase() != 'CERRADO',
        )
        .length;

    return CommuSafeAnimatedBackground(
      dark: false,
      child: SafeArea(
        child: Stack(
          children: <Widget>[
            RefreshIndicator(
              onRefresh: () async {
                await Future.wait(<Future<void>>[
                  context.read<IncidenteProvider>().cargarIncidentes(
                    refresh: true,
                  ),
                  context.read<NotificacionProvider>().cargarAvisosVigentes(),
                ]);
              },
              child: CustomScrollView(
                controller: _scrollController,
                physics: const AlwaysScrollableScrollPhysics(
                  parent: BouncingScrollPhysics(),
                ),
                slivers: <Widget>[
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Row(
                            children: <Widget>[
                              Builder(
                                builder: (BuildContext context) {
                                  return IconButton.filledTonal(
                                    onPressed: () =>
                                        Scaffold.of(context).openDrawer(),
                                    icon: const Icon(Icons.menu_rounded),
                                  );
                                },
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: <Widget>[
                                    Text(
                                      'Centro de incidentes',
                                      style: Theme.of(context)
                                          .textTheme
                                          .headlineSmall
                                          ?.copyWith(
                                            fontWeight: FontWeight.w900,
                                          ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      usuario?.esResidente == true
                                          ? 'Consulta tus reportes y registra casos con evidencia.'
                                          : 'Monitorea y atiende incidentes de Remansos del Norte.',
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodyMedium
                                          ?.copyWith(
                                            color: AppColors.textSecondary,
                                            height: 1.45,
                                          ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 18),
                          _IncidentCommandPanel(
                            visibleCount: provider.incidentes.length,
                            activeCount: activeCount,
                            highPriorityCount: highPriorityCount,
                            filtered: provider.tieneFiltrosActivos,
                          ),
                          const SizedBox(height: 18),
                          TextField(
                            controller: _searchController,
                            onChanged: _onSearchChanged,
                            onSubmitted: _onSearchChanged,
                            textInputAction: TextInputAction.search,
                            decoration: InputDecoration(
                              hintText: 'Buscar por título o descripción',
                              prefixIcon: const Icon(Icons.search_rounded),
                              suffixIcon: _searchController.text.trim().isEmpty
                                  ? null
                                  : IconButton(
                                      onPressed: _clearFilters,
                                      icon: const Icon(Icons.close_rounded),
                                    ),
                            ),
                          ),
                          const SizedBox(height: 14),
                          if (avisosVigentes.isNotEmpty) ...<Widget>[
                            Column(
                              children: avisosVigentes
                                  .map((aviso) => AvisoBanner(aviso: aviso))
                                  .toList(),
                            ),
                            const SizedBox(height: 2),
                          ],
                          SizedBox(
                            height: 42,
                            child: ListView.separated(
                              scrollDirection: Axis.horizontal,
                              itemCount: _categories.length,
                              separatorBuilder: (_, __) =>
                                  const SizedBox(width: 10),
                              itemBuilder: (BuildContext context, int index) {
                                final category = _categories[index];
                                final isActive =
                                    provider.categoriaActiva ==
                                    category['value'];
                                return ChoiceChip(
                                  label: Text(category['label'] ?? ''),
                                  selected: isActive,
                                  onSelected: (_) {
                                    context
                                        .read<IncidenteProvider>()
                                        .aplicarFiltro(
                                          categoria: category['value'],
                                          busqueda: _searchController.text,
                                        );
                                  },
                                  selectedColor: AppColors.primary,
                                  backgroundColor: Colors.white,
                                  side: const BorderSide(
                                    color: Color(0xFFE2E8F0),
                                  ),
                                  labelStyle: TextStyle(
                                    color: isActive
                                        ? Colors.white
                                        : AppColors.textSecondary,
                                    fontWeight: FontWeight.w800,
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (provider.isLoading && provider.incidentes.isEmpty)
                    SliverPadding(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                      sliver: SliverList.builder(
                        itemCount: 4,
                        itemBuilder: (BuildContext context, int index) {
                          return const Padding(
                            padding: EdgeInsets.only(bottom: 14),
                            child: _IncidentCardSkeleton(),
                          );
                        },
                      ),
                    )
                  else if (provider.incidentes.isEmpty)
                    SliverFillRemaining(
                      hasScrollBody: false,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(20, 16, 20, 120),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: <Widget>[
                            EmptyStateCard(
                              icon: provider.errorMessage != null
                                  ? Icons.cloud_off_rounded
                                  : provider.tieneFiltrosActivos
                                  ? Icons.filter_alt_off_rounded
                                  : Icons.inbox_rounded,
                              title: provider.errorMessage != null
                                  ? 'No se pudieron cargar los incidentes'
                                  : provider.tieneFiltrosActivos
                                  ? 'No hay resultados con esos filtros'
                                  : 'Aún no hay incidentes reportados',
                              message:
                                  provider.errorMessage ??
                                  (provider.tieneFiltrosActivos
                                      ? 'Prueba ajustando la categoría o la búsqueda para encontrar incidentes.'
                                      : 'Cuando se registre un nuevo incidente aparecerá aquí con su estado y prioridad.'),
                              actionLabel: provider.errorMessage != null
                                  ? 'Reintentar'
                                  : null,
                              onAction: provider.errorMessage != null
                                  ? () => context
                                        .read<IncidenteProvider>()
                                        .cargarIncidentes(refresh: true)
                                  : null,
                              toneColor: provider.errorMessage != null
                                  ? AppColors.danger
                                  : null,
                            ),
                            if (provider.tieneFiltrosActivos) ...<Widget>[
                              const SizedBox(height: 18),
                              OutlinedButton.icon(
                                onPressed: _clearFilters,
                                icon: const Icon(Icons.restart_alt_rounded),
                                label: const Text('Limpiar filtros'),
                              ),
                            ],
                          ],
                        ),
                      ),
                    )
                  else
                    SliverPadding(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
                      sliver: SliverList.builder(
                        itemCount: provider.incidentes.length,
                        itemBuilder: (BuildContext context, int index) {
                          final incidente = provider.incidentes[index];
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 14),
                            child: TweenAnimationBuilder<double>(
                              duration: Duration(
                                milliseconds: 360 + (index % 6) * 70,
                              ),
                              tween: Tween<double>(begin: 0, end: 1),
                              curve: Curves.easeOutCubic,
                              builder:
                                  (
                                    BuildContext context,
                                    double value,
                                    Widget? child,
                                  ) {
                                    return Opacity(
                                      opacity: value,
                                      child: Transform.translate(
                                        offset: Offset(0, (1 - value) * 22),
                                        child: child,
                                      ),
                                    );
                                  },
                              child: IncidenteCard(
                                incidente: incidente,
                                onTap: () =>
                                    context.push('/incidentes/${incidente.id}'),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  if (provider.isLoadingMore)
                    const SliverToBoxAdapter(
                      child: Padding(
                        padding: EdgeInsets.symmetric(vertical: 18),
                        child: Center(child: CircularProgressIndicator()),
                      ),
                    ),
                  SliverToBoxAdapter(
                    child: SizedBox(height: canCreate ? 110 : 32),
                  ),
                ],
              ),
            ),
            if (canCreate)
              Positioned(
                right: 20,
                bottom: 20,
                child: FloatingActionButton.extended(
                  onPressed: _goToCreate,
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('Nuevo'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _IncidentCommandPanel extends StatelessWidget {
  const _IncidentCommandPanel({
    required this.visibleCount,
    required this.activeCount,
    required this.highPriorityCount,
    required this.filtered,
  });

  final int visibleCount;
  final int activeCount;
  final int highPriorityCount;
  final bool filtered;

  @override
  Widget build(BuildContext context) {
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(26),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: AppColors.primary.withValues(alpha: 0.22),
            blurRadius: 28,
            offset: const Offset(0, 18),
          ),
        ],
      ),
      child: Stack(
        children: <Widget>[
          const Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: <Color>[
                    AppColors.primary,
                    AppColors.accent,
                    Color(0xFF3B0A1E),
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(child: CustomPaint(painter: _CommandPanelPainter())),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Container(
                      height: 48,
                      width: 48,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.14),
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.14),
                        ),
                      ),
                      child: const Icon(
                        Icons.radar_rounded,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            filtered
                                ? 'Vista filtrada'
                                : 'Monitoreo comunitario activo',
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            filtered
                                ? 'La lista responde a tus criterios actuales.'
                                : 'Seguimiento en tiempo real para Remansos del Norte.',
                            style: Theme.of(context).textTheme.bodySmall
                                ?.copyWith(
                                  color: Colors.white.withValues(alpha: 0.82),
                                  height: 1.45,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  children: <Widget>[
                    _MetricPill(
                      value: visibleCount,
                      label: 'visibles',
                      color: Colors.white,
                    ),
                    const SizedBox(width: 10),
                    _MetricPill(
                      value: activeCount,
                      label: 'activos',
                      color: AppColors.success,
                    ),
                    const SizedBox(width: 10),
                    _MetricPill(
                      value: highPriorityCount,
                      label: 'alta',
                      color: AppColors.danger,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricPill extends StatelessWidget {
  const _MetricPill({
    required this.value,
    required this.label,
    required this.color,
  });

  final int value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
        ),
        child: Column(
          children: <Widget>[
            TweenAnimationBuilder<int>(
              duration: const Duration(milliseconds: 550),
              tween: IntTween(begin: 0, end: value),
              builder:
                  (BuildContext context, int animatedValue, Widget? child) {
                    return Text(
                      animatedValue.toString(),
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: color,
                        fontWeight: FontWeight.w900,
                      ),
                    );
                  },
            ),
            const SizedBox(height: 2),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: Colors.white.withValues(alpha: 0.78),
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CommandPanelPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final linePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.1
      ..color = Colors.white.withValues(alpha: 0.10);
    final strongPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.8
      ..strokeCap = StrokeCap.round
      ..color = AppColors.danger.withValues(alpha: 0.20);

    for (var i = 0; i < 7; i++) {
      final y = size.height * (i / 6);
      canvas.drawLine(
        Offset(-20, y + 24),
        Offset(size.width + 20, y - 28),
        linePaint,
      );
    }

    final route = Path()
      ..moveTo(size.width * 0.08, size.height * 0.76)
      ..cubicTo(
        size.width * 0.34,
        size.height * 0.45,
        size.width * 0.64,
        size.height * 0.92,
        size.width * 0.94,
        size.height * 0.28,
      );
    canvas.drawPath(route, strongPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _IncidentCardSkeleton extends StatelessWidget {
  const _IncidentCardSkeleton();

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: const Color(0xFFE2E8F0),
      highlightColor: const Color(0xFFF8FAFC),
      child: Container(
        height: 174,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
        ),
      ),
    );
  }
}
