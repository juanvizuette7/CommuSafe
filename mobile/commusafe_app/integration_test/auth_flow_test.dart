import 'package:commusafe_app/main.dart' as app;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Flujo de autenticación móvil', () {
    testWidgets('inicia sesión, abre perfil y cierra sesión', (
      WidgetTester tester,
    ) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 4));

      expect(find.text('CommuSafe'), findsOneWidget);
      expect(find.text('Remansos del Norte'), findsOneWidget);

      await tester.enterText(
        find.byType(TextFormField).at(0),
        'residente1@remansos.com',
      );
      await tester.enterText(find.byType(TextFormField).at(1), 'Commu2026*');
      await tester.tap(find.text('Ingresar'));
      await tester.pump();
      await _pumpUntilVisible(
        tester,
        find.text('Centro de incidentes'),
        debugLabel: 'pantalla principal de incidentes',
      );

      expect(find.text('Centro de incidentes'), findsOneWidget);

      await tester.tap(find.text('Perfil'));
      await tester.pumpAndSettle(const Duration(seconds: 2));

      await _pumpUntilVisible(tester, find.text('María López'));

      expect(find.text('María López'), findsWidgets);
      expect(find.text('residente1@remansos.com'), findsOneWidget);
      expect(find.text('Apto 101 Torre A'), findsOneWidget);

      await tester.tap(find.text('Cerrar sesión'));
      await tester.pump();
      await _pumpUntilVisible(
        tester,
        find.text('Remansos del Norte'),
        debugLabel: 'pantalla de login',
      );

      expect(find.text('CommuSafe'), findsOneWidget);
      expect(find.text('Remansos del Norte'), findsOneWidget);
    });
  });
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
