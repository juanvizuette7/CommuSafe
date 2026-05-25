import 'package:commusafe_app/features/auth/providers/auth_provider.dart';
import 'package:commusafe_app/features/auth/screens/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  testWidgets('La pantalla de login renderiza sus textos base', (
    WidgetTester tester,
  ) async {
    await _pumpLogin(tester);

    expect(find.text('CommuSafe'), findsOneWidget);
    expect(find.text('Ingresar'), findsOneWidget);
    expect(find.textContaining('Correo'), findsOneWidget);
    expect(
      find.textContaining('Tratamiento de Datos Personales'),
      findsOneWidget,
    );
  });

  testWidgets('La pantalla de login permite aceptar politica de datos', (
    WidgetTester tester,
  ) async {
    await _pumpLogin(tester);

    final checkboxFinder = find.byType(Checkbox);
    expect(checkboxFinder, findsOneWidget);

    var checkbox = tester.widget<Checkbox>(checkboxFinder);
    expect(checkbox.value, isFalse);

    await tester.ensureVisible(checkboxFinder);
    await tester.pump();
    await tester.tap(checkboxFinder);
    await tester.pump();

    checkbox = tester.widget<Checkbox>(checkboxFinder);
    expect(checkbox.value, isTrue);
  });
}

Future<void> _pumpLogin(WidgetTester tester) async {
  await tester.pumpWidget(
    ChangeNotifierProvider<AuthProvider>(
      create: (_) => AuthProvider(),
      child: const MaterialApp(home: LoginScreen()),
    ),
  );

  await tester.pump(const Duration(milliseconds: 1200));
}
