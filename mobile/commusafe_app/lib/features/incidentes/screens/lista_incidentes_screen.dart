import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/empty_state_card.dart';
import '../../../shared/widgets/incidente_card.dart';
import '../../auth/providers/auth_provider.dart';
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
    final authProvider = context.watch<AuthProvider>();
    final usuario = authProvider.usuarioActual;
    final canCreate =
        usuario?.esResidente == true || usuario?.esVigilante == true;

    return SafeArea(
      child: Stack(
        children: <Widget>[
          RefreshIndicator(
            onRefresh: () => context
                .read<IncidenteProvider>()
                .cargarIncidentes(refresh: true),
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
                                  onPressed: () => Scaffold.of(context).openDrawer(),
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
                                          fontWeight: FontWeight.w800,
                                        ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    usuario?.esResidente == true
                                        ? 'Consulta el estado de tus reportes y registra nuevos casos.'
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
                        Container(
                          padding: const EdgeInsets.all(18),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: <Color>[
                                AppColors.primary,
                                AppColors.accent,
                              ],
                            ),
                            borderRadius: BorderRadius.circular(24),
                          ),
                          child: Row(
                            children: <Widget>[
                              Container(
                                height: 48,
                                width: 48,
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.14),
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: const Icon(
                                  Icons.warning_amber_rounded,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: <Widget>[
                                    Text(
                                      '${provider.incidentes.length} incidentes visibles',
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium
                                          ?.copyWith(
                                            color: Colors.white,
                                            fontWeight: FontWeight.w800,
                                          ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      provider.tieneFiltrosActivos
                                          ? 'La lista está filtrada según tus criterios actuales.'
                                          : 'Sigue la trazabilidad de cada incidente desde la app.',
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.copyWith(
                                            color: Colors.white.withValues(alpha: 0.84),
                                            height: 1.45,
                                          ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
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
                        SizedBox(
                          height: 42,
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemCount: _categories.length,
                            separatorBuilder: (_, __) => const SizedBox(width: 10),
                            itemBuilder: (BuildContext context, int index) {
                              final category = _categories[index];
                              final isActive =
                                  provider.categoriaActiva == category['value'];
                              return ChoiceChip(
                                label: Text(category['label'] ?? ''),
                                selected: isActive,
                                onSelected: (_) {
                                  context.read<IncidenteProvider>().aplicarFiltro(
                                        categoria: category['value'],
                                        busqueda: _searchController.text,
                                      );
                                },
                                selectedColor: AppColors.primary,
                                backgroundColor: Colors.white,
                                side: const BorderSide(color: Color(0xFFE2E8F0)),
                                labelStyle: TextStyle(
                                  color: isActive
                                      ? Colors.white
                                      : AppColors.textSecondary,
                                  fontWeight: FontWeight.w700,
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
                            icon: provider.tieneFiltrosActivos
                                ? Icons.filter_alt_off_rounded
                                : Icons.inbox_rounded,
                            title: provider.tieneFiltrosActivos
                                ? 'No hay resultados con esos filtros'
                                : 'Aún no hay incidentes reportados',
                            message: provider.tieneFiltrosActivos
                                ? 'Prueba ajustando la categoría o la búsqueda para encontrar incidentes.'
                                : 'Cuando se registre un nuevo incidente aparecerá aquí con su estado y prioridad.',
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
                          child: IncidenteCard(
                            incidente: incidente,
                            onTap: () => context.push('/incidentes/${incidente.id}'),
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
    );
  }
}

class _IncidentCardSkeleton extends StatelessWidget {
  const _IncidentCardSkeleton();

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: const Color(0xFFE2E8F0),
      highlightColor: const Color(0xFFF8FAFC),
      child: Container(
        height: 168,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
        ),
      ),
    );
  }
}
