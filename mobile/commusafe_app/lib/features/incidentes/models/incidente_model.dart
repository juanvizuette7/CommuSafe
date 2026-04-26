import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import 'evidencia_model.dart';
import 'historial_model.dart';

class IncidenteModel {
  const IncidenteModel({
    required this.id,
    required this.titulo,
    required this.descripcion,
    required this.categoria,
    required this.categoriaLabel,
    required this.prioridad,
    required this.prioridadLabel,
    required this.estado,
    required this.estadoLabel,
    required this.ubicacionReferencia,
    required this.reportadoPorNombre,
    required this.fechaReporte,
    required this.totalEvidencias,
    required this.evidencias,
    required this.historial,
    required this.reportadoPorEmail,
    required this.reportadoPorUnidad,
    required this.atendidoPorNombre,
    required this.observacionesCierre,
    required this.fechaActualizacion,
    required this.fechaCierre,
    required this.detalleCompleto,
  });

  final String id;
  final String titulo;
  final String descripcion;
  final String categoria;
  final String categoriaLabel;
  final String prioridad;
  final String prioridadLabel;
  final String estado;
  final String estadoLabel;
  final String ubicacionReferencia;
  final String reportadoPorNombre;
  final DateTime? fechaReporte;
  final int totalEvidencias;
  final List<EvidenciaModel> evidencias;
  final List<HistorialModel> historial;
  final String reportadoPorEmail;
  final String reportadoPorUnidad;
  final String atendidoPorNombre;
  final String observacionesCierre;
  final DateTime? fechaActualizacion;
  final DateTime? fechaCierre;
  final bool detalleCompleto;

  Color get prioridadColor => AppColors.priorityColor(prioridad);

  Color get estadoColor => AppColors.incidentStateColor(estado);

  bool get tieneEvidencias => totalEvidencias > 0 || evidencias.isNotEmpty;

  String get tiempoRelativo => _relativeTimeFrom(fechaReporte);

  String get inicialesReportante {
    final words = reportadoPorNombre
        .split(RegExp(r'\s+'))
        .where((word) => word.trim().isNotEmpty)
        .toList();
    if (words.isEmpty) {
      return 'CS';
    }
    if (words.length == 1) {
      return words.first.substring(0, 1).toUpperCase();
    }
    return (words.first.substring(0, 1) + words.last.substring(0, 1))
        .toUpperCase();
  }

  IncidenteModel copyWith({
    String? id,
    String? titulo,
    String? descripcion,
    String? categoria,
    String? categoriaLabel,
    String? prioridad,
    String? prioridadLabel,
    String? estado,
    String? estadoLabel,
    String? ubicacionReferencia,
    String? reportadoPorNombre,
    DateTime? fechaReporte,
    int? totalEvidencias,
    List<EvidenciaModel>? evidencias,
    List<HistorialModel>? historial,
    String? reportadoPorEmail,
    String? reportadoPorUnidad,
    String? atendidoPorNombre,
    String? observacionesCierre,
    DateTime? fechaActualizacion,
    DateTime? fechaCierre,
    bool? detalleCompleto,
  }) {
    return IncidenteModel(
      id: id ?? this.id,
      titulo: titulo ?? this.titulo,
      descripcion: descripcion ?? this.descripcion,
      categoria: categoria ?? this.categoria,
      categoriaLabel: categoriaLabel ?? this.categoriaLabel,
      prioridad: prioridad ?? this.prioridad,
      prioridadLabel: prioridadLabel ?? this.prioridadLabel,
      estado: estado ?? this.estado,
      estadoLabel: estadoLabel ?? this.estadoLabel,
      ubicacionReferencia: ubicacionReferencia ?? this.ubicacionReferencia,
      reportadoPorNombre: reportadoPorNombre ?? this.reportadoPorNombre,
      fechaReporte: fechaReporte ?? this.fechaReporte,
      totalEvidencias: totalEvidencias ?? this.totalEvidencias,
      evidencias: evidencias ?? this.evidencias,
      historial: historial ?? this.historial,
      reportadoPorEmail: reportadoPorEmail ?? this.reportadoPorEmail,
      reportadoPorUnidad: reportadoPorUnidad ?? this.reportadoPorUnidad,
      atendidoPorNombre: atendidoPorNombre ?? this.atendidoPorNombre,
      observacionesCierre: observacionesCierre ?? this.observacionesCierre,
      fechaActualizacion: fechaActualizacion ?? this.fechaActualizacion,
      fechaCierre: fechaCierre ?? this.fechaCierre,
      detalleCompleto: detalleCompleto ?? this.detalleCompleto,
    );
  }

  factory IncidenteModel.fromJson(Map<String, dynamic>? json) {
    final data = json ?? <String, dynamic>{};
    final reportadoPor = _readMap(data['reportado_por']);
    final atendidoPor = _readMap(data['atendido_por']);
    final evidenciasRaw = _readList(data['evidencias']);
    final historialRaw = _readList(data['historial']);
    final categoria = data['categoria']?.toString().trim() ?? '';
    final prioridad = data['prioridad']?.toString().trim() ?? '';
    final estado = data['estado']?.toString().trim() ?? '';
    final reportadoPorNombre =
        data['reportado_por_nombre']?.toString().trim().isNotEmpty == true
        ? data['reportado_por_nombre'].toString().trim()
        : reportadoPor['nombre_completo']?.toString().trim() ?? 'Sin autor';

    return IncidenteModel(
      id: data['id']?.toString() ?? '',
      titulo: data['titulo']?.toString().trim() ?? '',
      descripcion: data['descripcion']?.toString().trim() ?? '',
      categoria: categoria,
      categoriaLabel:
          data['categoria_label']?.toString().trim().isNotEmpty == true
          ? data['categoria_label'].toString().trim()
          : _categoriaLabel(categoria),
      prioridad: prioridad,
      prioridadLabel:
          data['prioridad_label']?.toString().trim().isNotEmpty == true
          ? data['prioridad_label'].toString().trim()
          : _prioridadLabel(prioridad),
      estado: estado,
      estadoLabel: data['estado_label']?.toString().trim().isNotEmpty == true
          ? data['estado_label'].toString().trim()
          : estadoDisplayForCode(estado),
      ubicacionReferencia:
          data['ubicacion_referencia']?.toString().trim() ?? '',
      reportadoPorNombre: reportadoPorNombre,
      fechaReporte: DateTime.tryParse(data['fecha_reporte']?.toString() ?? ''),
      totalEvidencias: _asInt(data['total_evidencias']) ?? evidenciasRaw.length,
      evidencias: evidenciasRaw
          .map((item) => EvidenciaModel.fromJson(_readMap(item)))
          .toList(),
      historial: historialRaw
          .map((item) => HistorialModel.fromJson(_readMap(item)))
          .toList(),
      reportadoPorEmail: reportadoPor['email']?.toString().trim() ?? '',
      reportadoPorUnidad:
          reportadoPor['unidad_residencial']?.toString().trim() ?? '',
      atendidoPorNombre:
          data['atendido_por_nombre']?.toString().trim().isNotEmpty == true
          ? data['atendido_por_nombre'].toString().trim()
          : atendidoPor['nombre_completo']?.toString().trim() ?? '',
      observacionesCierre:
          data['observaciones_cierre']?.toString().trim() ?? '',
      fechaActualizacion: DateTime.tryParse(
        data['fecha_actualizacion']?.toString() ?? '',
      ),
      fechaCierre: DateTime.tryParse(data['fecha_cierre']?.toString() ?? ''),
      detalleCompleto:
          data.containsKey('historial') ||
          data.containsKey('evidencias') ||
          data.containsKey('reportado_por') ||
          data.containsKey('observaciones_cierre'),
    );
  }

  static String estadoDisplayForCode(String code) {
    switch (code.toUpperCase()) {
      case 'REGISTRADO':
        return 'Registrado';
      case 'EN_PROCESO':
        return 'En proceso';
      case 'RESUELTO':
        return 'Resuelto';
      case 'CERRADO':
        return 'Cerrado';
      default:
        return code.replaceAll('_', ' ').trim();
    }
  }

  static Map<String, dynamic> _readMap(dynamic value) {
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

  static List<dynamic> _readList(dynamic value) {
    if (value is List) {
      return value;
    }
    return <dynamic>[];
  }

  static int? _asInt(dynamic value) {
    if (value is int) {
      return value;
    }
    if (value is String) {
      return int.tryParse(value);
    }
    return null;
  }

  static String _categoriaLabel(String categoria) {
    switch (categoria.toUpperCase()) {
      case 'SEGURIDAD':
        return 'Seguridad';
      case 'CONVIVENCIA':
        return 'Convivencia';
      case 'INFRAESTRUCTURA':
        return 'Infraestructura';
      case 'EMERGENCIA':
        return 'Emergencia';
      default:
        return categoria;
    }
  }

  static String _prioridadLabel(String prioridad) {
    switch (prioridad.toUpperCase()) {
      case 'ALTA':
        return 'Alta';
      case 'MEDIA':
        return 'Media';
      case 'BAJA':
        return 'Baja';
      default:
        return prioridad;
    }
  }

  static String _relativeTimeFrom(DateTime? dateTime) {
    if (dateTime == null) {
      return 'Sin fecha';
    }

    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inSeconds < 60) {
      return 'Hace un momento';
    }
    if (difference.inMinutes < 60) {
      final minutes = difference.inMinutes;
      return 'Hace $minutes min';
    }
    if (difference.inHours < 24) {
      final hours = difference.inHours;
      return 'Hace $hours h';
    }
    if (difference.inDays == 1) {
      return 'Ayer';
    }
    if (difference.inDays < 7) {
      return 'Hace ${difference.inDays} días';
    }
    if (difference.inDays < 30) {
      final weeks = (difference.inDays / 7).floor();
      return 'Hace ${weeks == 0 ? 1 : weeks} semanas';
    }
    if (difference.inDays < 365) {
      final months = (difference.inDays / 30).floor();
      return 'Hace ${months == 0 ? 1 : months} meses';
    }
    final years = (difference.inDays / 365).floor();
    return 'Hace ${years == 0 ? 1 : years} años';
  }
}
