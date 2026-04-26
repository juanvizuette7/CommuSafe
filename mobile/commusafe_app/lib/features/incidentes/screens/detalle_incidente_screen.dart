import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/incident_badges.dart';
import '../../auth/models/usuario_model.dart';
import '../../auth/providers/auth_provider.dart';
import '../models/evidencia_model.dart';
import '../models/historial_model.dart';
import '../models/incidente_model.dart';
import '../providers/incidente_provider.dart';

class DetalleIncidenteScreen extends StatefulWidget {
  const DetalleIncidenteScreen({super.key, required this.incidenteId});

  final String incidenteId;

  @override
  State<DetalleIncidenteScreen> createState() => _DetalleIncidenteScreenState();
}

class _DetalleIncidenteScreenState extends State<DetalleIncidenteScreen> {
  final TextEditingController _comentarioController = TextEditingController();
  final PageController _pageController = PageController();
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  bool _requested = false;
  int _currentEvidencePage = 0;
  String? _selectedState;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_requested) {
      return;
    }
    _requested = true;
    final incidenteProvider = context.read<IncidenteProvider>();
    Future<void>.microtask(
      () => incidenteProvider.cargarDetalle(widget.incidenteId),
    );
  }

  @override
  void dispose() {
    _comentarioController.dispose();
    _pageController.dispose();
    super.dispose();
  }

  List<String> _availableStates(
    IncidenteModel incidente,
    UsuarioModel? usuario,
  ) {
    if (usuario == null || (!usuario.esAdmin && !usuario.esVigilante)) {
      return <String>[];
    }

    switch (incidente.estado.toUpperCase()) {
      case 'REGISTRADO':
        return <String>['EN_PROCESO'];
      case 'EN_PROCESO':
        return <String>['RESUELTO'];
      case 'RESUELTO':
        return usuario.esAdmin ? <String>['CERRADO'] : <String>[];
      default:
        return <String>[];
    }
  }

  Future<void> _submitStatusUpdate(
    IncidenteModel incidente,
    UsuarioModel? usuario,
  ) async {
    final form = _formKey.currentState;
    if (form == null || !form.validate() || _selectedState == null) {
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Confirmar actualización'),
          content: Text(
            '¿Deseas cambiar el estado del incidente a '
            '${IncidenteModel.estadoDisplayForCode(_selectedState!)}?',
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('Confirmar'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) {
      return;
    }

    final provider = context.read<IncidenteProvider>();
    final updated = await provider.cambiarEstado(
      incidenteId: incidente.id,
      estadoNuevo: _selectedState!,
      comentario: _comentarioController.text.trim(),
    );

    if (!mounted) {
      return;
    }

    if (updated == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            provider.errorMessage ?? 'No fue posible actualizar el incidente.',
          ),
          backgroundColor: AppColors.danger,
        ),
      );
      return;
    }

    final remainingStates = _availableStates(updated, usuario);
    setState(() {
      _comentarioController.clear();
      _selectedState = remainingStates.isEmpty ? null : remainingStates.first;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Estado actualizado correctamente.'),
        backgroundColor: AppColors.success,
      ),
    );
  }

  Future<void> _openEvidenceGallery(
    List<EvidenciaModel> evidencias,
    int initialPage,
  ) async {
    await showDialog<void>(
      context: context,
      barrierColor: Colors.black87,
      builder: (BuildContext context) {
        return _EvidenceGalleryDialog(
          evidencias: evidencias,
          initialPage: initialPage,
        );
      },
    );
  }

  Color _headerColor(IncidenteModel? incidente) {
    return incidente?.prioridadColor ?? AppColors.primary;
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<IncidenteProvider>();
    final authProvider = context.watch<AuthProvider>();
    final usuario = authProvider.usuarioActual;
    final incidente = provider.incidentePorId(widget.incidenteId);
    final availableStates = incidente == null
        ? <String>[]
        : _availableStates(incidente, usuario);

    if (_selectedState == null && availableStates.isNotEmpty) {
      _selectedState = availableStates.first;
    } else if (_selectedState != null &&
        !availableStates.contains(_selectedState)) {
      _selectedState = availableStates.isEmpty ? null : availableStates.first;
    }

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: RefreshIndicator(
        onRefresh: () => context.read<IncidenteProvider>().cargarDetalle(
          widget.incidenteId,
          forceRefresh: true,
        ),
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(
            parent: BouncingScrollPhysics(),
          ),
          slivers: <Widget>[
            SliverAppBar(
              pinned: true,
              expandedHeight: 220,
              backgroundColor: _headerColor(incidente),
              foregroundColor: Colors.white,
              leading: IconButton(
                icon: const Icon(Icons.arrow_back_rounded),
                onPressed: () => context.pop(),
              ),
              flexibleSpace: FlexibleSpaceBar(
                titlePadding: const EdgeInsetsDirectional.only(
                  start: 72,
                  bottom: 20,
                  end: 20,
                ),
                title: Text(
                  incidente?.titulo ?? 'Detalle del incidente',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                background: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: <Color>[
                        _headerColor(incidente),
                        AppColors.primary,
                      ],
                    ),
                  ),
                  child: SafeArea(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 28, 20, 72),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: <Widget>[
                          if (incidente != null)
                            Wrap(
                              spacing: 10,
                              runSpacing: 10,
                              children: <Widget>[
                                PriorityBadge(
                                  priority: incidente.prioridad,
                                  label: incidente.prioridadLabel,
                                ),
                                IncidentStatusBadge(
                                  status: incidente.estado,
                                  label: incidente.estadoLabel,
                                ),
                              ],
                            ),
                          const SizedBox(height: 12),
                          Text(
                            incidente?.categoriaLabel ??
                                'Cargando incidente...',
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(
                                  color: Colors.white.withValues(alpha: 0.9),
                                  fontWeight: FontWeight.w700,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 32),
                child: incidente == null
                    ? _DetailLoadingState(
                        loading: provider.detalleEstaCargando(
                          widget.incidenteId,
                        ),
                        errorMessage: provider.errorMessage,
                        onRetry: () =>
                            context.read<IncidenteProvider>().cargarDetalle(
                              widget.incidenteId,
                              forceRefresh: true,
                            ),
                      )
                    : Column(
                        children: <Widget>[
                          _SectionCard(
                            title: 'Información del incidente',
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Row(
                                  children: <Widget>[
                                    _CategoryIcon(
                                      categoria: incidente.categoria,
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Text(
                                        incidente.categoriaLabel,
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleMedium
                                            ?.copyWith(
                                              fontWeight: FontWeight.w800,
                                            ),
                                      ),
                                    ),
                                    _LargeStateBadge(
                                      label: incidente.estadoLabel,
                                      color: incidente.estadoColor,
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 18),
                                _DetailRow(
                                  icon: Icons.calendar_month_rounded,
                                  label: 'Fecha de reporte',
                                  value: incidente.fechaReporte == null
                                      ? 'No disponible'
                                      : DateFormat(
                                          'd MMM yyyy, hh:mm a',
                                          'es_CO',
                                        ).format(incidente.fechaReporte!),
                                ),
                                if (incidente.ubicacionReferencia
                                    .trim()
                                    .isNotEmpty)
                                  _DetailRow(
                                    icon: Icons.place_outlined,
                                    label: 'Ubicación',
                                    value: incidente.ubicacionReferencia,
                                  ),
                                const SizedBox(height: 10),
                                Text(
                                  'Descripción',
                                  style: Theme.of(context).textTheme.titleSmall
                                      ?.copyWith(fontWeight: FontWeight.w800),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  incidente.descripcion,
                                  style: Theme.of(context).textTheme.bodyMedium
                                      ?.copyWith(
                                        color: AppColors.textSecondary,
                                        height: 1.6,
                                      ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 18),
                          _SectionCard(
                            title: 'Datos del reportante',
                            child: Row(
                              children: <Widget>[
                                CircleAvatar(
                                  radius: 28,
                                  backgroundColor: AppColors.primary.withValues(
                                    alpha: 0.12,
                                  ),
                                  child: Text(
                                    incidente.inicialesReportante,
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleMedium
                                        ?.copyWith(
                                          color: AppColors.primary,
                                          fontWeight: FontWeight.w800,
                                        ),
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: <Widget>[
                                      Text(
                                        incidente.reportadoPorNombre,
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleMedium
                                            ?.copyWith(
                                              fontWeight: FontWeight.w800,
                                            ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        incidente.reportadoPorEmail
                                                .trim()
                                                .isEmpty
                                            ? 'Sin correo disponible'
                                            : incidente.reportadoPorEmail,
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall
                                            ?.copyWith(
                                              color: AppColors.textSecondary,
                                            ),
                                      ),
                                      if (incidente.reportadoPorUnidad
                                          .trim()
                                          .isNotEmpty)
                                        Padding(
                                          padding: const EdgeInsets.only(
                                            top: 4,
                                          ),
                                          child: Text(
                                            incidente.reportadoPorUnidad,
                                            style: Theme.of(context)
                                                .textTheme
                                                .bodySmall
                                                ?.copyWith(
                                                  color:
                                                      AppColors.textSecondary,
                                                ),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                          if (incidente.evidencias.isNotEmpty) ...<Widget>[
                            const SizedBox(height: 18),
                            _SectionCard(
                              title: 'Evidencias fotográficas',
                              child: Column(
                                children: <Widget>[
                                  SizedBox(
                                    height: 220,
                                    child: PageView.builder(
                                      controller: _pageController,
                                      itemCount: incidente.evidencias.length,
                                      onPageChanged: (int value) {
                                        setState(() {
                                          _currentEvidencePage = value;
                                        });
                                      },
                                      itemBuilder: (BuildContext context, int index) {
                                        final evidencia =
                                            incidente.evidencias[index];
                                        return GestureDetector(
                                          onTap: () => _openEvidenceGallery(
                                            incidente.evidencias,
                                            index,
                                          ),
                                          child: Padding(
                                            padding: const EdgeInsets.only(
                                              right: 12,
                                            ),
                                            child: ClipRRect(
                                              borderRadius:
                                                  BorderRadius.circular(22),
                                              child: Stack(
                                                fit: StackFit.expand,
                                                children: <Widget>[
                                                  CachedNetworkImage(
                                                    imageUrl:
                                                        evidencia.imagenUrl,
                                                    fit: BoxFit.cover,
                                                    placeholder:
                                                        (
                                                          BuildContext context,
                                                          String url,
                                                        ) {
                                                          return Container(
                                                            color: const Color(
                                                              0xFFF1F5F9,
                                                            ),
                                                            child: const Center(
                                                              child:
                                                                  CircularProgressIndicator(),
                                                            ),
                                                          );
                                                        },
                                                    errorWidget:
                                                        (
                                                          BuildContext context,
                                                          String url,
                                                          Object error,
                                                        ) {
                                                          return Container(
                                                            color: const Color(
                                                              0xFFF1F5F9,
                                                            ),
                                                            child: const Icon(
                                                              Icons
                                                                  .broken_image_outlined,
                                                              color: AppColors
                                                                  .textSecondary,
                                                            ),
                                                          );
                                                        },
                                                  ),
                                                  if (evidencia
                                                      .descripcion
                                                      .isNotEmpty)
                                                    Positioned(
                                                      left: 12,
                                                      right: 12,
                                                      bottom: 12,
                                                      child: Container(
                                                        padding:
                                                            const EdgeInsets.all(
                                                              12,
                                                            ),
                                                        decoration: BoxDecoration(
                                                          color: Colors.black
                                                              .withValues(
                                                                alpha: 0.45,
                                                              ),
                                                          borderRadius:
                                                              BorderRadius.circular(
                                                                16,
                                                              ),
                                                        ),
                                                        child: Text(
                                                          evidencia.descripcion,
                                                          style: Theme.of(context)
                                                              .textTheme
                                                              .bodySmall
                                                              ?.copyWith(
                                                                color: Colors
                                                                    .white,
                                                                fontWeight:
                                                                    FontWeight
                                                                        .w600,
                                                              ),
                                                        ),
                                                      ),
                                                    ),
                                                ],
                                              ),
                                            ),
                                          ),
                                        );
                                      },
                                    ),
                                  ),
                                  const SizedBox(height: 14),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: List<Widget>.generate(
                                      incidente.evidencias.length,
                                      (int index) {
                                        final isActive =
                                            _currentEvidencePage == index;
                                        return AnimatedContainer(
                                          duration: const Duration(
                                            milliseconds: 220,
                                          ),
                                          width: isActive ? 22 : 8,
                                          height: 8,
                                          margin: const EdgeInsets.symmetric(
                                            horizontal: 4,
                                          ),
                                          decoration: BoxDecoration(
                                            color: isActive
                                                ? AppColors.primary
                                                : AppColors.muted,
                                            borderRadius: BorderRadius.circular(
                                              999,
                                            ),
                                          ),
                                        );
                                      },
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                          const SizedBox(height: 18),
                          _SectionCard(
                            title: 'Timeline de historial',
                            child: incidente.historial.isEmpty
                                ? Text(
                                    'Este incidente aún no tiene cambios de estado registrados.',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(
                                          color: AppColors.textSecondary,
                                        ),
                                  )
                                : Column(
                                    children: List<Widget>.generate(
                                      incidente.historial.length,
                                      (int index) {
                                        final item = incidente.historial[index];
                                        return _TimelineItem(
                                          item: item,
                                          isLast:
                                              index ==
                                              incidente.historial.length - 1,
                                        );
                                      },
                                    ),
                                  ),
                          ),
                          if (availableStates.isNotEmpty) ...<Widget>[
                            const SizedBox(height: 18),
                            _SectionCard(
                              title: 'Actualizar estado',
                              child: Form(
                                key: _formKey,
                                child: Column(
                                  children: <Widget>[
                                    DropdownButtonFormField<String>(
                                      key: ValueKey<String?>(
                                        '${incidente.id}-${_selectedState ?? ''}',
                                      ),
                                      initialValue: _selectedState,
                                      decoration: const InputDecoration(
                                        labelText: 'Nuevo estado',
                                      ),
                                      items: availableStates
                                          .map(
                                            (
                                              String state,
                                            ) => DropdownMenuItem<String>(
                                              value: state,
                                              child: Text(
                                                IncidenteModel.estadoDisplayForCode(
                                                  state,
                                                ),
                                              ),
                                            ),
                                          )
                                          .toList(),
                                      onChanged: (String? value) {
                                        setState(() {
                                          _selectedState = value;
                                        });
                                      },
                                    ),
                                    const SizedBox(height: 16),
                                    TextFormField(
                                      controller: _comentarioController,
                                      minLines: 3,
                                      maxLines: 5,
                                      decoration: const InputDecoration(
                                        labelText: 'Comentario',
                                        hintText:
                                            'Explica qué acción se realizó o por qué cambia el estado.',
                                        alignLabelWithHint: true,
                                      ),
                                      validator: (String? value) {
                                        if ((value ?? '').trim().length < 5) {
                                          return 'El comentario debe tener al menos 5 caracteres.';
                                        }
                                        return null;
                                      },
                                    ),
                                    const SizedBox(height: 18),
                                    SizedBox(
                                      width: double.infinity,
                                      child: ElevatedButton(
                                        onPressed: provider.isUpdatingState
                                            ? null
                                            : () => _submitStatusUpdate(
                                                incidente,
                                                usuario,
                                              ),
                                        child: provider.isUpdatingState
                                            ? const SizedBox(
                                                height: 22,
                                                width: 22,
                                                child:
                                                    CircularProgressIndicator(
                                                      color: Colors.white,
                                                      strokeWidth: 2.4,
                                                    ),
                                              )
                                            : const Text('Actualizar'),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 22,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 18),
          child,
        ],
      ),
    );
  }
}

class _CategoryIcon extends StatelessWidget {
  const _CategoryIcon({required this.categoria});

  final String categoria;

  @override
  Widget build(BuildContext context) {
    late final IconData icon;
    late final Color color;

    switch (categoria.toUpperCase()) {
      case 'SEGURIDAD':
        icon = Icons.lock_rounded;
        color = AppColors.danger;
        break;
      case 'CONVIVENCIA':
        icon = Icons.groups_rounded;
        color = const Color(0xFF2563EB);
        break;
      case 'INFRAESTRUCTURA':
        icon = Icons.settings_suggest_rounded;
        color = const Color(0xFF0F766E);
        break;
      case 'EMERGENCIA':
        icon = Icons.warning_amber_rounded;
        color = AppColors.warning;
        break;
      default:
        icon = Icons.info_outline_rounded;
        color = AppColors.primary;
    }

    return Container(
      height: 52,
      width: 52,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Icon(icon, color: color),
    );
  }
}

class _LargeStateBadge extends StatelessWidget {
  const _LargeStateBadge({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, size: 18, color: AppColors.textSecondary),
          const SizedBox(width: 10),
          Expanded(
            child: RichText(
              text: TextSpan(
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
                children: <InlineSpan>[
                  TextSpan(
                    text: '$label: ',
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  TextSpan(text: value),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TimelineItem extends StatelessWidget {
  const _TimelineItem({required this.item, required this.isLast});

  final HistorialModel item;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.incidentStateColor(item.estadoNuevo);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Column(
          children: <Widget>[
            Container(
              width: 16,
              height: 16,
              decoration: BoxDecoration(shape: BoxShape.circle, color: color),
            ),
            if (!isLast)
              Container(width: 2, height: 74, color: AppColors.muted),
          ],
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(bottom: 20),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Expanded(
                        child: Text(
                          item.cambiadoPorNombre,
                          style: Theme.of(context).textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                      ),
                      Text(
                        item.fechaCambio == null
                            ? 'Sin fecha'
                            : DateFormat(
                                'd MMM yyyy, hh:mm a',
                                'es_CO',
                              ).format(item.fechaCambio!),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    item.transicionLegible,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: color,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  if (item.comentario.trim().isNotEmpty) ...<Widget>[
                    const SizedBox(height: 8),
                    Text(
                      item.comentario,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                        height: 1.5,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _DetailLoadingState extends StatelessWidget {
  const _DetailLoadingState({
    required this.loading,
    required this.errorMessage,
    required this.onRetry,
  });

  final bool loading;
  final String? errorMessage;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 48),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 48),
      child: Column(
        children: <Widget>[
          Text(
            errorMessage ?? 'No fue posible cargar el incidente.',
            textAlign: TextAlign.center,
            style: Theme.of(
              context,
            ).textTheme.bodyLarge?.copyWith(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}

class _EvidenceGalleryDialog extends StatefulWidget {
  const _EvidenceGalleryDialog({
    required this.evidencias,
    required this.initialPage,
  });

  final List<EvidenciaModel> evidencias;
  final int initialPage;

  @override
  State<_EvidenceGalleryDialog> createState() => _EvidenceGalleryDialogState();
}

class _EvidenceGalleryDialogState extends State<_EvidenceGalleryDialog> {
  late final PageController _controller;
  late int _currentPage;

  @override
  void initState() {
    super.initState();
    _currentPage = widget.initialPage;
    _controller = PageController(initialPage: widget.initialPage);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog.fullscreen(
      backgroundColor: Colors.black,
      child: SafeArea(
        child: Stack(
          children: <Widget>[
            PageView.builder(
              controller: _controller,
              itemCount: widget.evidencias.length,
              onPageChanged: (int value) {
                setState(() {
                  _currentPage = value;
                });
              },
              itemBuilder: (BuildContext context, int index) {
                final evidencia = widget.evidencias[index];
                return InteractiveViewer(
                  minScale: 1,
                  maxScale: 4,
                  child: Center(
                    child: CachedNetworkImage(
                      imageUrl: evidencia.imagenUrl,
                      fit: BoxFit.contain,
                      placeholder: (BuildContext context, String url) {
                        return const CircularProgressIndicator(
                          color: Colors.white,
                        );
                      },
                      errorWidget:
                          (BuildContext context, String url, Object error) {
                            return const Icon(
                              Icons.broken_image_outlined,
                              color: Colors.white70,
                              size: 48,
                            );
                          },
                    ),
                  ),
                );
              },
            ),
            Positioned(
              top: 16,
              left: 16,
              child: IconButton.filled(
                onPressed: () => Navigator.of(context).pop(),
                style: IconButton.styleFrom(backgroundColor: Colors.black54),
                icon: const Icon(Icons.close_rounded),
              ),
            ),
            Positioned(
              top: 24,
              right: 20,
              child: Text(
                '${_currentPage + 1}/${widget.evidencias.length}',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
