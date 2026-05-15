import 'package:commusafe_app/features/auth/providers/auth_provider.dart';
import 'package:commusafe_app/features/auth/screens/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

const _delegates = <LocalizationsDelegate<dynamic>>[
  GlobalMaterialLocalizations.delegate,
  GlobalWidgetsLocalizations.delegate,
  GlobalCupertinoLocalizations.delegate,
];

void main() {
  testWidgets('La pantalla de login renderiza sus textos base', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>(
        create: (_) => AuthProvider(),
        child: const MaterialApp(
          locale: Locale('es', 'CO'),
          supportedLocales: <Locale>[Locale('es', 'CO'), Locale('en')],
          localizationsDelegates: _delegates,
          home: LoginScreen(),
        ),
      ),
    );

    await tester.pump(const Duration(milliseconds: 1200));

    expect(find.text('CommuSafe'), findsOneWidget);
    expect(find.text('Ingresar'), findsOneWidget);
    expect(find.text('Correo electronico'), findsOneWidget);
  });

  testWidgets('La pantalla de login cambia textos base a ingles', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>(
        create: (_) => AuthProvider(),
        child: const MaterialApp(
          locale: Locale('en'),
          supportedLocales: <Locale>[Locale('es', 'CO'), Locale('en')],
          localizationsDelegates: _delegates,
          home: LoginScreen(),
        ),
      ),
    );

    await tester.pump(const Duration(milliseconds: 1200));

    expect(find.text('CommuSafe'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.text('Email'), findsOneWidget);
  });
}
