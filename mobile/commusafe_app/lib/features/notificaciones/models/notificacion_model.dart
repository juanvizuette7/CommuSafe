import 'package:flutter/material.dart';

class NotificacionModel {
  const NotificacionModel({
    required this.id,
    required this.titulo,
    required this.cuerpo,
    required this.tipo,
    required this.tipoLabel,
    required this.leida,
    required this.fechaEnvio,
    this.incidenteRelacionado,
    this.incidenteTitulo,
  });

  final String id;
  final String titulo;
  final String cuerpo;
  final String tipo;
  final String tipoLabel;
  final bool leida;
  final DateTime fechaEnvio;
  final String? incidenteRelacionado;
  final String? incidenteTitulo;

  IconData iconoPorTipo() {
    switch (tipo.toUpperCase()) {
      case 'INCIDENTE_NUEVO':
        return Icons.add_alert_rounded;
      case 'CAMBIO_ESTADO':
        return Icons.sync_alt_rounded;
      case 'AVISO_ADMIN':
        return Icons.campaign_rounded;
      case 'EMERGENCIA':
        return Icons.emergency_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  String get tiempoRelativo {
    final diff = DateTime.now().difference(fechaEnvio);
    if (diff.inSeconds < 60) {
      return 'Ahora';
    }
    if (diff.inMinutes < 60) {
      return '${diff.inMinutes} min';
    }
    if (diff.inHours < 24) {
      return '${diff.inHours} h';
    }
    if (diff.inDays == 1) {
      return 'Ayer';
    }
    if (diff.inDays < 7) {
      return '${diff.inDays} d';
    }
    final weeks = (diff.inDays / 7).floor();
    return '${weeks == 0 ? 1 : weeks} sem';
  }

  NotificacionModel copyWith({
    String? id,
    String? titulo,
    String? cuerpo,
    String? tipo,
    String? tipoLabel,
    bool? leida,
    DateTime? fechaEnvio,
    String? incidenteRelacionado,
    String? incidenteTitulo,
  }) {
    return NotificacionModel(
      id: id ?? this.id,
      titulo: titulo ?? this.titulo,
      cuerpo: cuerpo ?? this.cuerpo,
      tipo: tipo ?? this.tipo,
      tipoLabel: tipoLabel ?? this.tipoLabel,
      leida: leida ?? this.leida,
      fechaEnvio: fechaEnvio ?? this.fechaEnvio,
      incidenteRelacionado: incidenteRelacionado ?? this.incidenteRelacionado,
      incidenteTitulo: incidenteTitulo ?? this.incidenteTitulo,
    );
  }

  factory NotificacionModel.fromJson(Map<String, dynamic>? json) {
    final data = json ?? <String, dynamic>{};
    final tipo = data['tipo']?.toString().trim() ?? '';

    return NotificacionModel(
      id: data['id']?.toString() ?? '',
      titulo: data['titulo']?.toString().trim() ?? '',
      cuerpo: data['cuerpo']?.toString().trim() ?? '',
      tipo: tipo,
      tipoLabel: data['tipo_label']?.toString().trim().isNotEmpty == true
          ? data['tipo_label'].toString().trim()
          : _tipoLabel(tipo),
      leida: data['leida'] == true,
      fechaEnvio: DateTime.tryParse(data['fecha_envio']?.toString() ?? '') ??
          DateTime.now(),
      incidenteRelacionado:
          data['incidente_relacionado']?.toString().trim().isNotEmpty == true
              ? data['incidente_relacionado'].toString().trim()
              : null,
      incidenteTitulo:
          data['incidente_titulo']?.toString().trim().isNotEmpty == true
              ? data['incidente_titulo'].toString().trim()
              : null,
    );
  }

  static String _tipoLabel(String tipo) {
    switch (tipo.toUpperCase()) {
      case 'INCIDENTE_NUEVO':
        return 'Incidente nuevo';
      case 'CAMBIO_ESTADO':
        return 'Cambio de estado';
      case 'AVISO_ADMIN':
        return 'Aviso administrativo';
      case 'EMERGENCIA':
        return 'Emergencia';
      default:
        return tipo.replaceAll('_', ' ');
    }
  }
}
