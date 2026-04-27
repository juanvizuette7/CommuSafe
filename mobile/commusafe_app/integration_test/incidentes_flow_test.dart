import 'dart:convert';
import 'dart:io';

import 'package:commusafe_app/core/services/storage_service.dart';
import 'package:commusafe_app/features/incidentes/providers/incidente_provider.dart';
import 'package:commusafe_app/features/incidentes/screens/detalle_incidente_screen.dart';
import 'package:commusafe_app/features/incidentes/screens/lista_incidentes_screen.dart';
import 'package:commusafe_app/main.dart' as app;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';
import 'package:integration_test/integration_test.dart';
import 'package:provider/provider.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Flujo de incidentes móvil', () {
    testWidgets(
      'residente crea incidente con evidencia y vigilante actualiza su estado',
      (WidgetTester tester) async {
        await tester.runAsync(StorageService.clearSession);

        await app.main();
        await tester.pump(const Duration(seconds: 2));

        await _login(
          tester,
          email: 'residente1@remansos.com',
          password: 'Commu2026*',
        );
        await _pumpUntilVisible(
          tester,
          find.text('Centro de incidentes'),
          debugLabel: 'lista de incidentes del residente',
        );

        final uniqueSuffix = DateTime.now().millisecondsSinceEpoch;
        final incidentTitle = 'Prueba S7 $uniqueSuffix';

        final residentContext = tester.element(
          find.byType(ListaIncidentesScreen),
        );
        final incidentProvider = Provider.of<IncidenteProvider>(
          residentContext,
          listen: false,
        );

        var createdIncident = await tester.runAsync(() async {
          final imageFile = await _createTempImage(uniqueSuffix);
          final created = await incidentProvider.crearIncidente(
            titulo: incidentTitle,
            descripcion:
                'Incidente creado desde la prueba de integración del sprint 7.',
            categoria: 'SEGURIDAD',
            ubicacionReferencia: 'Torre A - pasillo 3',
            imagenes: <XFile>[imageFile],
          );
          await incidentProvider.cargarIncidentes(refresh: true);
          return created;
        });
        if (createdIncident == null) {
          for (final incidente in incidentProvider.incidentes) {
            if (incidente.titulo == incidentTitle) {
              createdIncident = incidente;
              break;
            }
          }
        }

        expect(
          createdIncident,
          isNotNull,
          reason:
              incidentProvider.errorMessage ??
              'La creación del incidente devolvió null.',
        );
        expect(createdIncident!.tieneEvidencias, isTrue);

        await tester.pump(const Duration(seconds: 2));
        await _pumpUntilVisible(
          tester,
          find.text(incidentTitle),
          debugLabel: 'incidente creado por el residente',
        );

        await tester.tap(find.text(incidentTitle).first);
        await tester.pump(const Duration(seconds: 2));

        await _pumpUntilVisible(
          tester,
          find.text('Timeline de historial'),
          debugLabel: 'detalle del incidente creado',
        );
        expect(find.text('Evidencias fotográficas'), findsOneWidget);

        await _logout(tester);

        await _login(
          tester,
          email: 'vigilante1@remansos.com',
          password: 'Commu2026*',
        );
        await _pumpUntilVisible(
          tester,
          find.text('Centro de incidentes'),
          debugLabel: 'lista de incidentes del vigilante',
        );

        await _pumpUntilVisible(
          tester,
          find.text(incidentTitle),
          debugLabel: 'incidente visible para el vigilante',
        );

        await tester.tap(find.text(incidentTitle).first);
        await tester.pump(const Duration(seconds: 2));

        await _pumpUntilVisible(
          tester,
          find.text('Actualizar estado'),
          debugLabel: 'formulario de actualización',
        );

        await tester.enterText(
          find.byType(TextFormField).last,
          'Atendido desde la app móvil durante la validación del sprint 7.',
        );
        await tester.ensureVisible(find.text('Actualizar'));
        await tester.pump(const Duration(milliseconds: 400));
        await tester.tap(find.text('Actualizar'));
        await tester.pump(const Duration(seconds: 1));
        await _pumpUntilVisible(
          tester,
          find.text('Confirmar'),
          debugLabel: 'diálogo de confirmación',
        );

        await tester.tap(find.text('Confirmar'));
        await tester.pump();
        await _pumpUntilVisible(
          tester,
          find.text('Estado actualizado correctamente.'),
          debugLabel: 'confirmación de cambio de estado',
        );

        final detailContext = tester.element(
          find.byType(DetalleIncidenteScreen),
        );
        final updatedProvider = Provider.of<IncidenteProvider>(
          detailContext,
          listen: false,
        );
        final updatedIncident = updatedProvider.incidentePorId(
          createdIncident.id,
        );

        expect(updatedIncident, isNotNull);
        expect(updatedIncident!.estado, 'EN_PROCESO');
        expect(
          updatedIncident.historial.any(
            (item) =>
                item.estadoNuevo == 'EN_PROCESO' &&
                item.comentario.contains('sprint 7'),
          ),
          isTrue,
        );
      },
    );
  });
}

Future<void> _login(
  WidgetTester tester, {
  required String email,
  required String password,
}) async {
  await _pumpUntilVisible(
    tester,
    find.text('CommuSafe'),
    debugLabel: 'pantalla de login',
  );

  await tester.enterText(find.byType(TextFormField).at(0), email);
  await tester.enterText(find.byType(TextFormField).at(1), password);
  await tester.tap(find.text('Ingresar'));
  await tester.pump();
}

Future<void> _logout(WidgetTester tester) async {
  await tester.tap(find.text('Perfil'));
  await tester.pump(const Duration(seconds: 2));
  await _pumpUntilVisible(
    tester,
    find.text('Cerrar sesión'),
    debugLabel: 'pantalla de perfil',
  );
  await tester.tap(find.text('Cerrar sesión'));
  await tester.pump();
  await _pumpUntilVisible(
    tester,
    find.text('CommuSafe'),
    debugLabel: 'retorno al login',
  );
}

Future<XFile> _createTempImage(int suffix) async {
  final bytes = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAFUlEQVR4nGN86ZrAgBsw4ZFjGLnSAOzCAaIcCmXWAAAAAElFTkSuQmCC',
  );
  final file = File(
    '${Directory.systemTemp.path}${Platform.pathSeparator}commusafe_s7_$suffix.png',
  );
  await file.writeAsBytes(bytes, flush: true);
  return XFile(file.path, name: 'commusafe_s7_$suffix.png');
}

Future<void> _pumpUntilVisible(
  WidgetTester tester,
  Finder finder, {
  Duration step = const Duration(milliseconds: 300),
  int maxAttempts = 80,
  String? debugLabel,
}) async {
  for (var attempt = 0; attempt < maxAttempts; attempt++) {
    await tester.pump(step);
    if (finder.evaluate().isNotEmpty) {
      return;
    }
  }

  final texts = tester
      .widgetList<Text>(find.byType(Text))
      .map((widget) => widget.data ?? widget.textSpan?.toPlainText() ?? '')
      .where((value) => value.trim().isNotEmpty)
      .toList();

  throw TestFailure(
    'No se encontró ${debugLabel ?? 'el widget esperado'} durante la espera. '
    'Textos visibles: ${texts.join(' | ')}',
  );
}
