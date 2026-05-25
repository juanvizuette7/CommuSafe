import 'package:commusafe_app/features/auth/models/usuario_model.dart';
import 'package:commusafe_app/features/incidentes/models/incidente_model.dart';
import 'package:commusafe_app/features/notificaciones/models/notificacion_model.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('UsuarioModel', () {
    test('normaliza datos del residente autenticado', () {
      final usuario = UsuarioModel.fromJson(<String, dynamic>{
        'id': 7,
        'email': 'residente1@remansos.com',
        'nombre': 'Maria',
        'apellido': 'Lopez',
        'rol': 'RESIDENTE',
        'unidad_residencial': 'Apto 101 Torre A',
        'telefono': '3001234567',
        'politica_privacidad_aceptada': true,
        'activo': true,
      });

      expect(usuario.id, '7');
      expect(usuario.email, 'residente1@remansos.com');
      expect(usuario.nombreCompleto, 'Maria Lopez');
      expect(usuario.iniciales, 'ML');
      expect(usuario.esResidente, isTrue);
      expect(usuario.esAdmin, isFalse);
      expect(usuario.rolLegible, 'Residente');
      expect(usuario.unidadResidencial, 'Apto 101 Torre A');
      expect(usuario.politicaPrivacidadAceptada, isTrue);
    });

    test('serializa los datos necesarios para persistir sesion local', () {
      final usuario = UsuarioModel.fromJson(<String, dynamic>{
        'id': '9',
        'email': 'vigilante1@remansos.com',
        'nombre': 'Pedro',
        'apellido': 'Garcia',
        'rol': 'VIGILANTE',
      });

      final json = usuario.toJson();

      expect(json['id'], '9');
      expect(json['email'], 'vigilante1@remansos.com');
      expect(json['nombre_completo'], 'Pedro Garcia');
      expect(json['rol'], 'VIGILANTE');
      expect(json['activo'], isTrue);
    });
  });

  group('IncidenteModel', () {
    test('parsea incidente de residente con evidencia e historial', () {
      final incidente = IncidenteModel.fromJson(<String, dynamic>{
        'id': 'inc-001',
        'titulo': 'Alerta en porteria',
        'descripcion': 'Movimiento sospechoso reportado por residente.',
        'categoria': 'SEGURIDAD',
        'prioridad': 'ALTA',
        'estado': 'EN_PROCESO',
        'ubicacion_referencia': 'Porteria principal',
        'reportado_por': <String, dynamic>{
          'id': 'user-001',
          'nombre_completo': 'Maria Lopez',
          'email': 'residente1@remansos.com',
          'unidad_residencial': 'Apto 101 Torre A',
          'telefono': '3001234567',
        },
        'fecha_reporte': '2026-05-12T08:30:00Z',
        'total_evidencias': 1,
        'evidencias': <Map<String, dynamic>>[
          <String, dynamic>{
            'id': 'ev-001',
            'imagen': '/media/incidentes/evidencia.png',
            'descripcion': 'Foto enviada por residente',
            'fecha_subida': '2026-05-12T08:31:00Z',
          },
        ],
        'historial': <Map<String, dynamic>>[
          <String, dynamic>{
            'id': 'hist-001',
            'estado_anterior': 'REGISTRADO',
            'estado_anterior_label': 'Registrado',
            'estado_nuevo': 'EN_PROCESO',
            'estado_nuevo_label': 'En proceso',
            'cambiado_por': <String, dynamic>{
              'nombre_completo': 'Pedro Garcia',
            },
            'comentario': 'Vigilancia atiende el caso.',
            'fecha_cambio': '2026-05-12T08:40:00Z',
          },
        ],
      });

      expect(incidente.id, 'inc-001');
      expect(incidente.categoriaLabel, 'Seguridad');
      expect(incidente.prioridadLabel, 'Alta');
      expect(incidente.estadoLabel, 'En proceso');
      expect(incidente.reportadoPorNombre, 'Maria Lopez');
      expect(incidente.reportadoPorUnidad, 'Apto 101 Torre A');
      expect(incidente.tieneEvidencias, isTrue);
      expect(incidente.evidencias, hasLength(1));
      expect(incidente.historial, hasLength(1));
      expect(incidente.historial.single.cambiadoPorNombre, 'Pedro Garcia');
      expect(incidente.detalleCompleto, isTrue);
    });

    test('calcula valores de respaldo cuando el backend omite etiquetas', () {
      final incidente = IncidenteModel.fromJson(<String, dynamic>{
        'id': 'inc-002',
        'titulo': 'Daño en ascensor',
        'descripcion': 'Falla reportada por residente.',
        'categoria': 'INFRAESTRUCTURA',
        'prioridad': 'BAJA',
        'estado': 'REGISTRADO',
        'reportado_por_nombre': 'Juan Perez',
        'total_evidencias': '0',
      });

      expect(incidente.categoriaLabel, 'Infraestructura');
      expect(incidente.prioridadLabel, 'Baja');
      expect(incidente.estadoLabel, 'Registrado');
      expect(incidente.inicialesReportante, 'JP');
      expect(incidente.tieneEvidencias, isFalse);
    });
  });

  group('NotificacionModel', () {
    test('identifica notificacion critica de emergencia para residente', () {
      final notificacion = NotificacionModel.fromJson(<String, dynamic>{
        'id': 'not-001',
        'titulo': 'Emergencia comunitaria',
        'cuerpo': 'Se genero una alerta de seguridad.',
        'tipo': 'EMERGENCIA',
        'leida': false,
        'fecha_envio': DateTime.now().toIso8601String(),
        'incidente_relacionado': 'inc-001',
        'incidente_titulo': 'Alerta en porteria',
      });

      expect(notificacion.tipoLabel, 'Emergencia');
      expect(notificacion.esCritica, isTrue);
      expect(notificacion.leida, isFalse);
      expect(notificacion.incidenteRelacionado, 'inc-001');
      expect(notificacion.incidenteTitulo, 'Alerta en porteria');
    });

    test('copyWith permite marcar notificacion como leida', () {
      final notificacion = NotificacionModel.fromJson(<String, dynamic>{
        'id': 'not-002',
        'titulo': 'Cambio de estado',
        'cuerpo': 'Tu incidente fue actualizado.',
        'tipo': 'CAMBIO_ESTADO',
        'leida': false,
        'fecha_envio': DateTime.now().toIso8601String(),
      });

      final actualizada = notificacion.copyWith(leida: true);

      expect(actualizada.id, notificacion.id);
      expect(actualizada.tipoLabel, 'Cambio de estado');
      expect(actualizada.leida, isTrue);
      expect(notificacion.leida, isFalse);
    });
  });
}
