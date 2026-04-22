import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/services/api_service.dart';
import '../models/incidente_model.dart';

class IncidenteProvider extends ChangeNotifier {
  final List<IncidenteModel> _incidentes = <IncidenteModel>[];
  final Map<String, IncidenteModel> _detalleCache = <String, IncidenteModel>{};
  final Set<String> _detallesEnCarga = <String>{};

  bool _isLoading = false;
  bool _isLoadingMore = false;
  bool _isCreating = false;
  bool _isUpdatingState = false;
  int _paginaActual = 1;
  bool _hasMore = true;
  String? _categoriaActiva;
  String _busquedaActiva = '';
  String? _errorMessage;

  List<IncidenteModel> get incidentes =>
      List<IncidenteModel>.unmodifiable(_incidentes);
  bool get isLoading => _isLoading;
  bool get isLoadingMore => _isLoadingMore;
  bool get isCreating => _isCreating;
  bool get isUpdatingState => _isUpdatingState;
  int get paginaActual => _paginaActual;
  bool get hasMore => _hasMore;
  String? get categoriaActiva => _categoriaActiva;
  String get busquedaActiva => _busquedaActiva;
  String? get errorMessage => _errorMessage;
  bool get tieneFiltrosActivos =>
      (_categoriaActiva?.isNotEmpty ?? false) || _busquedaActiva.isNotEmpty;

  IncidenteModel? incidentePorId(String incidenteId) {
    final cached = _detalleCache[incidenteId];
    if (cached != null) {
      return cached;
    }
    for (final incidente in _incidentes) {
      if (incidente.id == incidenteId) {
        return incidente;
      }
    }
    return null;
  }

  bool detalleEstaCargando(String incidenteId) {
    return _detallesEnCarga.contains(incidenteId);
  }

  Future<void> cargarIncidentes({bool refresh = false}) async {
    if (_isLoading || _isLoadingMore) {
      return;
    }

    final targetPage = refresh ? 1 : _paginaActual;
    await _fetchIncidentes(
      page: targetPage,
      reset: refresh || targetPage == 1,
    );
  }

  Future<void> cargarMas() async {
    if (_isLoading || _isLoadingMore || !_hasMore) {
      return;
    }

    await _fetchIncidentes(page: _paginaActual + 1, reset: false);
  }

  Future<void> aplicarFiltro({
    String? categoria,
    String? busqueda,
  }) async {
    _categoriaActiva = categoria?.trim().isEmpty ?? true
        ? null
        : categoria?.trim().toUpperCase();
    _busquedaActiva = (busqueda ?? _busquedaActiva).trim();
    _paginaActual = 1;
    _hasMore = true;
    await _fetchIncidentes(page: 1, reset: true);
  }

  Future<IncidenteModel?> cargarDetalle(
    String incidenteId, {
    bool forceRefresh = false,
  }) async {
    final cached = incidentePorId(incidenteId);
    if (!forceRefresh && cached?.detalleCompleto == true) {
      return cached;
    }

    _detallesEnCarga.add(incidenteId);
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.get<Map<String, dynamic>>(
        '${AppConstants.incidentsEndpoint}$incidenteId/',
      );
      final incidente = IncidenteModel.fromJson(_normalizeMap(response.data));
      _upsertIncidente(incidente);
      _detalleCache[incidente.id] = incidente;
      _errorMessage = null;
      return incidente;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
      return cached;
    } catch (_) {
      _errorMessage = 'No fue posible cargar el detalle del incidente.';
      return cached;
    } finally {
      _detallesEnCarga.remove(incidenteId);
      notifyListeners();
    }
  }

  Future<IncidenteModel?> crearIncidente({
    required String titulo,
    required String descripcion,
    required String categoria,
    String? ubicacionReferencia,
    List<XFile> imagenes = const <XFile>[],
  }) async {
    _isCreating = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final multipartFiles = <MultipartFile>[];
      for (final imagen in imagenes.take(3)) {
        multipartFiles.add(
          await MultipartFile.fromFile(
            imagen.path,
            filename: imagen.name,
          ),
        );
      }

      final response = await ApiService.postMultipart<Map<String, dynamic>>(
        AppConstants.incidentsEndpoint,
        data: <String, dynamic>{
          'titulo': titulo.trim(),
          'descripcion': descripcion.trim(),
          'categoria': categoria.trim().toUpperCase(),
          'ubicacion_referencia': ubicacionReferencia?.trim() ?? '',
        },
        files: multipartFiles,
      );

      final incidente = IncidenteModel.fromJson(_normalizeMap(response.data));
      _detalleCache[incidente.id] = incidente;

      if (_coincideConFiltros(incidente)) {
        _incidentes.insert(0, incidente);
      }

      _errorMessage = null;
      notifyListeners();
      return incidente;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
      notifyListeners();
      return null;
    } catch (_) {
      _errorMessage = 'No fue posible reportar el incidente.';
      notifyListeners();
      return null;
    } finally {
      _isCreating = false;
      notifyListeners();
    }
  }

  Future<IncidenteModel?> cambiarEstado({
    required String incidenteId,
    required String estadoNuevo,
    required String comentario,
  }) async {
    _isUpdatingState = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.post<Map<String, dynamic>>(
        '${AppConstants.incidentsEndpoint}$incidenteId/cambiar-estado/',
        data: <String, dynamic>{
          'estado_nuevo': estadoNuevo.trim().toUpperCase(),
          'comentario': comentario.trim(),
        },
      );
      final payload = _normalizeMap(response.data);
      final incidente = IncidenteModel.fromJson(
        _normalizeMap(payload['incidente']),
      );
      _upsertIncidente(incidente);
      _detalleCache[incidente.id] = incidente;
      _errorMessage = null;
      notifyListeners();
      return incidente;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
      notifyListeners();
      return null;
    } catch (_) {
      _errorMessage = 'No fue posible actualizar el estado del incidente.';
      notifyListeners();
      return null;
    } finally {
      _isUpdatingState = false;
      notifyListeners();
    }
  }

  void reset() {
    _incidentes.clear();
    _detalleCache.clear();
    _detallesEnCarga.clear();
    _isLoading = false;
    _isLoadingMore = false;
    _isCreating = false;
    _isUpdatingState = false;
    _paginaActual = 1;
    _hasMore = true;
    _categoriaActiva = null;
    _busquedaActiva = '';
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> _fetchIncidentes({
    required int page,
    required bool reset,
  }) async {
    if (reset) {
      _isLoading = true;
      if (page == 1) {
        _paginaActual = 1;
      }
    } else {
      _isLoadingMore = true;
    }
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.get<Map<String, dynamic>>(
        AppConstants.incidentsEndpoint,
        queryParameters: <String, dynamic>{
          'page': page,
          'ordering': '-fecha_reporte',
          if ((_categoriaActiva ?? '').isNotEmpty) 'categoria': _categoriaActiva,
          if (_busquedaActiva.isNotEmpty) 'q': _busquedaActiva,
        },
      );
      final payload = _normalizeMap(response.data);
      final rawResults = payload['results'];
      final results = rawResults is List ? rawResults : <dynamic>[];
      final nuevosIncidentes = results
          .map(
            (dynamic item) => IncidenteModel.fromJson(_normalizeMap(item)),
          )
          .toList();

      if (reset) {
        _incidentes
          ..clear()
          ..addAll(nuevosIncidentes);
      } else {
        for (final incidente in nuevosIncidentes) {
          _upsertIncidente(incidente);
        }
      }

      for (final incidente in nuevosIncidentes) {
        final cached = _detalleCache[incidente.id];
        if (cached == null || !cached.detalleCompleto) {
          _detalleCache[incidente.id] = incidente;
        }
      }

      _paginaActual = page;
      final count = _toInt(payload['count']) ?? _incidentes.length;
      final next = payload['next'];
      _hasMore = next != null ||
          (_incidentes.length < count && nuevosIncidentes.isNotEmpty);
      _errorMessage = null;
    } on DioException catch (error) {
      _errorMessage = _extractErrorMessage(error);
    } catch (_) {
      _errorMessage = 'No fue posible cargar los incidentes.';
    } finally {
      _isLoading = false;
      _isLoadingMore = false;
      notifyListeners();
    }
  }

  void _upsertIncidente(IncidenteModel incidente) {
    final index = _incidentes.indexWhere((item) => item.id == incidente.id);
    if (index >= 0) {
      _incidentes[index] = incidente;
      return;
    }

    if (_coincideConFiltros(incidente)) {
      _incidentes.insert(0, incidente);
    }
  }

  bool _coincideConFiltros(IncidenteModel incidente) {
    final sameCategory = _categoriaActiva == null ||
        incidente.categoria.toUpperCase() == _categoriaActiva;
    final query = _busquedaActiva.toLowerCase();
    final matchesQuery = query.isEmpty ||
        incidente.titulo.toLowerCase().contains(query) ||
        incidente.descripcion.toLowerCase().contains(query);
    return sameCategory && matchesQuery;
  }

  Map<String, dynamic> _normalizeMap(dynamic value) {
    if (value is Map<String, dynamic>) {
      return value;
    }
    if (value is Map) {
      return value.map(
        (dynamic key, dynamic val) => MapEntry(key.toString(), val),
      );
    }
    return <String, dynamic>{};
  }

  int? _toInt(dynamic value) {
    if (value is int) {
      return value;
    }
    return int.tryParse(value?.toString() ?? '');
  }

  String _extractErrorMessage(DioException error) {
    final data = error.response?.data;

    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.trim().isNotEmpty) {
        return detail;
      }

      final mensaje = data['mensaje'];
      if (mensaje is String && mensaje.trim().isNotEmpty) {
        return mensaje;
      }

      for (final value in data.values) {
        if (value is List && value.isNotEmpty) {
          return value.first.toString();
        }
        if (value is String && value.trim().isNotEmpty) {
          return value;
        }
      }
    }

    if (data is String && data.trim().isNotEmpty) {
      return data;
    }

    return 'No fue posible completar la operación con incidentes.';
  }
}
