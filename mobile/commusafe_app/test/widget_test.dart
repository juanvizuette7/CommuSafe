import 'package:commusafe_app/features/auth/providers/auth_provider.dart';
import 'package:commusafe_app/features/auth/screens/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  testWidgets('La pantalla de login renderiza sus textos base', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>(
        create: (_) => AuthProvider(),
        child: const MaterialApp(home: LoginScreen()),
      ),
    );

    await tester.pump(const Duration(milliseconds: 1200));

    expect(find.text('CommuSafe'), findsOneWidget);
    expect(find.text('Ingresar'), findsOneWidget);
    expect(find.text('Correo electrónico'), findsOneWidget);
  });
}
