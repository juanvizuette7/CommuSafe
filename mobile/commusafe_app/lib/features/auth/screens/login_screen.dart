import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/commusafe_animated_background.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  late final AnimationController _animationController;
  late final Animation<double> _fadeAnimation;
  late final Animation<Offset> _slideAnimation;

  bool _obscurePassword = true;
  bool _aceptaPoliticaPrivacidad = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCubic,
    );
    _slideAnimation =
        Tween<Offset>(begin: const Offset(0, 0.12), end: Offset.zero).animate(
          CurvedAnimation(
            parent: _animationController,
            curve: Curves.easeOutQuart,
          ),
        );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final authProvider = context.read<AuthProvider>();
    authProvider.clearError();

    if (!_formKey.currentState!.validate()) {
      return;
    }

    FocusScope.of(context).unfocus();

    final success = await authProvider.login(
      email: _emailController.text,
      password: _passwordController.text,
      aceptaPoliticaPrivacidad: _aceptaPoliticaPrivacidad,
    );

    if (!mounted) {
      return;
    }

    if (success) {
      context.go('/incidentes');
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final isLoading = authProvider.isLoading;
    final errorMessage = authProvider.errorMessage;
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      body: CommuSafeAnimatedBackground(
        dark: true,
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 28),
              child: FadeTransition(
                opacity: _fadeAnimation,
                child: SlideTransition(
                  position: _slideAnimation,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      _LoginSignalHeader(animation: _animationController),
                      const SizedBox(height: 24),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(30),
                        child: BackdropFilter(
                          filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
                          child: Container(
                            constraints: const BoxConstraints(maxWidth: 450),
                            padding: const EdgeInsets.fromLTRB(26, 28, 26, 26),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.91),
                              borderRadius: BorderRadius.circular(30),
                              border: Border.all(
                                color: Colors.white.withValues(alpha: 0.55),
                              ),
                              boxShadow: <BoxShadow>[
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.22),
                                  blurRadius: 42,
                                  offset: const Offset(0, 26),
                                ),
                              ],
                            ),
                            child: AutofillGroup(
                              child: Form(
                                key: _formKey,
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: <Widget>[
                                    Row(
                                      children: <Widget>[
                                        Container(
                                          height: 58,
                                          width: 58,
                                          decoration: BoxDecoration(
                                            borderRadius: BorderRadius.circular(
                                              20,
                                            ),
                                            gradient: LinearGradient(
                                              colors: <Color>[
                                                theme.primary,
                                                AppColors.danger,
                                              ],
                                            ),
                                            boxShadow: <BoxShadow>[
                                              BoxShadow(
                                                color: AppColors.danger
                                                    .withValues(alpha: 0.28),
                                                blurRadius: 20,
                                                offset: const Offset(0, 12),
                                              ),
                                            ],
                                          ),
                                          child: Padding(
                                            padding: const EdgeInsets.all(7),
                                            child: Image.asset(
                                              AppConstants.appLogoAsset,
                                              fit: BoxFit.contain,
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
                                                AppConstants.appName,
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .headlineSmall
                                                    ?.copyWith(
                                                      color: theme.primary,
                                                      fontWeight:
                                                          FontWeight.w900,
                                                    ),
                                              ),
                                              const SizedBox(height: 3),
                                              Text(
                                                AppConstants
                                                    .residentialComplexName,
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .bodyMedium
                                                    ?.copyWith(
                                                      color: AppColors
                                                          .textSecondary,
                                                      fontWeight:
                                                          FontWeight.w600,
                                                    ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 22),
                                    Row(
                                      children: <Widget>[
                                        _SignalBadge(
                                          icon: Icons.lock_outline_rounded,
                                          label: l10n.tr(
                                            'Acceso seguro',
                                            'Secure access',
                                          ),
                                          color: theme.primary,
                                        ),
                                        const SizedBox(width: 10),
                                        _SignalBadge(
                                          icon: Icons
                                              .notifications_active_outlined,
                                          label: l10n.tr('Alertas', 'Alerts'),
                                          color: theme.accent,
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 24),
                                    TextFormField(
                                      controller: _emailController,
                                      keyboardType: TextInputType.emailAddress,
                                      autofillHints: const <String>[
                                        AutofillHints.username,
                                        AutofillHints.email,
                                      ],
                                      enabled: !isLoading,
                                      onChanged: (_) =>
                                          authProvider.clearError(),
                                      decoration: InputDecoration(
                                        labelText: l10n.tr(
                                          'Correo electronico',
                                          'Email',
                                        ),
                                        prefixIcon: const Icon(
                                          Icons.email_outlined,
                                        ),
                                      ),
                                      validator: (String? value) {
                                        final text = value?.trim() ?? '';
                                        if (text.isEmpty) {
                                          return l10n.tr(
                                            'Ingresa tu correo electronico.',
                                            'Enter your email.',
                                          );
                                        }
                                        final emailRegex = RegExp(
                                          r'^[\w\.\-]+@([\w\-]+\.)+[a-zA-Z]{2,}$',
                                        );
                                        if (!emailRegex.hasMatch(text)) {
                                          return l10n.tr(
                                            'Escribe un correo electronico valido.',
                                            'Enter a valid email.',
                                          );
                                        }
                                        return null;
                                      },
                                    ),
                                    const SizedBox(height: 16),
                                    TextFormField(
                                      controller: _passwordController,
                                      obscureText: _obscurePassword,
                                      autofillHints: const <String>[
                                        AutofillHints.password,
                                      ],
                                      enabled: !isLoading,
                                      onChanged: (_) =>
                                          authProvider.clearError(),
                                      decoration: InputDecoration(
                                        labelText: l10n.tr(
                                          'Contrasena',
                                          'Password',
                                        ),
                                        prefixIcon: const Icon(
                                          Icons.lock_outline_rounded,
                                        ),
                                        suffixIcon: IconButton(
                                          onPressed: isLoading
                                              ? null
                                              : () {
                                                  setState(() {
                                                    _obscurePassword =
                                                        !_obscurePassword;
                                                  });
                                                },
                                          icon: Icon(
                                            _obscurePassword
                                                ? Icons.visibility_outlined
                                                : Icons.visibility_off_outlined,
                                          ),
                                        ),
                                      ),
                                      validator: (String? value) {
                                        if (value == null ||
                                            value.trim().isEmpty) {
                                          return l10n.tr(
                                            'Ingresa tu contrasena.',
                                            'Enter your password.',
                                          );
                                        }
                                        return null;
                                      },
                                      onFieldSubmitted: (_) => _submit(),
                                    ),
                                    if (errorMessage != null &&
                                        errorMessage
                                            .trim()
                                            .isNotEmpty) ...<Widget>[
                                      const SizedBox(height: 18),
                                      Container(
                                        width: double.infinity,
                                        padding: const EdgeInsets.all(14),
                                        decoration: BoxDecoration(
                                          color: AppColors.danger.withValues(
                                            alpha: 0.10,
                                          ),
                                          borderRadius: BorderRadius.circular(
                                            16,
                                          ),
                                          border: Border.all(
                                            color: AppColors.danger.withValues(
                                              alpha: 0.20,
                                            ),
                                          ),
                                        ),
                                        child: Row(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: <Widget>[
                                            const Padding(
                                              padding: EdgeInsets.only(top: 2),
                                              child: Icon(
                                                Icons.error_outline_rounded,
                                                color: AppColors.danger,
                                                size: 20,
                                              ),
                                            ),
                                            const SizedBox(width: 10),
                                            Expanded(
                                              child: Text(
                                                errorMessage,
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .bodyMedium
                                                    ?.copyWith(
                                                      color: AppColors.danger,
                                                      fontWeight:
                                                          FontWeight.w600,
                                                      height: 1.45,
                                                    ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                    const SizedBox(height: 18),
                                    _PrivacyPolicyAcceptance(
                                      value: _aceptaPoliticaPrivacidad,
                                      enabled: !isLoading,
                                      onChanged: (bool? value) {
                                        setState(() {
                                          _aceptaPoliticaPrivacidad =
                                              value ?? false;
                                        });
                                        authProvider.clearError();
                                      },
                                    ),
                                    const SizedBox(height: 24),
                                    DecoratedBox(
                                      decoration: BoxDecoration(
                                        borderRadius: BorderRadius.circular(16),
                                        gradient: LinearGradient(
                                          colors: <Color>[
                                            theme.primary,
                                            theme.accent,
                                            AppColors.danger,
                                          ],
                                        ),
                                        boxShadow: <BoxShadow>[
                                          BoxShadow(
                                            color: theme.primary.withValues(
                                              alpha: 0.30,
                                            ),
                                            blurRadius: 22,
                                            offset: const Offset(0, 13),
                                          ),
                                        ],
                                      ),
                                      child: Material(
                                        color: Colors.transparent,
                                        child: InkWell(
                                          borderRadius: BorderRadius.circular(
                                            16,
                                          ),
                                          onTap: isLoading ? null : _submit,
                                          child: SizedBox(
                                            height: 58,
                                            width: double.infinity,
                                            child: Center(
                                              child: AnimatedSwitcher(
                                                duration: const Duration(
                                                  milliseconds: 220,
                                                ),
                                                child: isLoading
                                                    ? const SizedBox(
                                                        key: ValueKey<String>(
                                                          'loader',
                                                        ),
                                                        height: 22,
                                                        width: 22,
                                                        child:
                                                            CircularProgressIndicator(
                                                              strokeWidth: 2.4,
                                                              color:
                                                                  Colors.white,
                                                            ),
                                                      )
                                                    : Text(
                                                        l10n.tr(
                                                          'Ingresar',
                                                          'Sign in',
                                                        ),
                                                        key:
                                                            const ValueKey<
                                                              String
                                                            >('label'),
                                                        style: Theme.of(context)
                                                            .textTheme
                                                            .titleSmall
                                                            ?.copyWith(
                                                              color:
                                                                  Colors.white,
                                                              fontWeight:
                                                                  FontWeight
                                                                      .w800,
                                                            ),
                                                      ),
                                              ),
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 14),
                                    Center(
                                      child: TextButton(
                                        onPressed: isLoading
                                            ? null
                                            : () => context.go('/reset'),
                                        child: Text(
                                          l10n.tr(
                                            '¿Olvidaste tu contraseña?',
                                            'Forgot your password?',
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PrivacyPolicyAcceptance extends StatelessWidget {
  const _PrivacyPolicyAcceptance({
    required this.value,
    required this.enabled,
    required this.onChanged,
  });

  final bool value;
  final bool enabled;
  final ValueChanged<bool?> onChanged;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);

    return Container(
      decoration: BoxDecoration(
        color: theme.primary.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: theme.primary.withValues(alpha: 0.10)),
      ),
      child: CheckboxListTile(
        value: value,
        onChanged: enabled ? onChanged : null,
        controlAffinity: ListTileControlAffinity.leading,
        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        activeColor: theme.primary,
        title: Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          children: <Widget>[
            Text(
              l10n.tr(
                'Confirmo que he leido y acepto la ',
                'I confirm that I have read and accept the ',
              ),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
                height: 1.35,
                fontWeight: FontWeight.w600,
              ),
            ),
            InkWell(
              onTap: () => _showPrivacyPolicy(context),
              child: Text(
                l10n.tr(
                  'politica de recoleccion y tratamiento de datos personales',
                  'personal data collection and processing policy',
                ),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: theme.accent,
                  height: 1.35,
                  fontWeight: FontWeight.w900,
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
            Text(
              '.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
                height: 1.35,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  static Future<void> _showPrivacyPolicy(BuildContext context) {
    return showDialog<void>(
      context: context,
      builder: (BuildContext dialogContext) {
        final l10n = AppLocalizations.of(dialogContext);
        return AlertDialog(
          title: Text(
            l10n.tr('Politica de datos personales', 'Personal data policy'),
          ),
          content: const SizedBox(
            width: double.maxFinite,
            child: SingleChildScrollView(
              child: Text(_privacyPolicyText, style: TextStyle(height: 1.45)),
            ),
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: Text(l10n.tr('Cerrar', 'Close')),
            ),
          ],
        );
      },
    );
  }
}

const String _privacyPolicyText = '''
Fecha de entrada en vigencia: 12 de mayo de 2026

CommuSafe fortalece la seguridad comunitaria mediante herramientas de comunicación, reporte de incidentes, alertas y gestión de información dentro de conjuntos residenciales o comunidades. Para funcionar correctamente recopila ciertos datos personales de los usuarios.

Responsables del tratamiento:
Anderson David Ojeda Zambrano, anderson.ojeda@campusucc.edu.co.
Juan Manuel Vizuette Fajardo, juan.vizuette@campusucc.edu.co.
Ubicación: Pasto, Nariño, Colombia.

Información recopilada:
Nombre completo o alias, correo electrónico, número telefónico, ubicación cuando sea necesaria para reportes o emergencias, información ingresada en formularios, fotografías o evidencias relacionadas con incidentes y datos técnicos básicos del dispositivo.

Finalidades:
Crear y administrar cuentas, permitir reportes de incidentes, facilitar alertas comunitarias, mejorar la seguridad y estabilidad de la aplicación, atender solicitudes, prevenir accesos no autorizados y cumplir obligaciones legales cuando sea requerido por autoridades competentes.

Compartición:
CommuSafe no venderá ni comercializará datos personales. La información podrá compartirse con proveedores tecnológicos necesarios, autoridades competentes, situaciones necesarias para proteger la seguridad de usuarios o casos autorizados por el titular.

Derechos del titular:
Conocer, actualizar y rectificar datos personales, solicitar prueba de autorización, ser informado sobre el uso de la información, revocar la autorización y solicitar eliminación cuando sea procedente, presentar quejas ante la Superintendencia de Industria y Comercio y acceder gratuitamente a sus datos.

Contacto:
Las solicitudes pueden enviarse a anderson.ojeda@campusucc.edu.co o juan.vizuette@campusucc.edu.co, indicando nombre del titular, petición, medio de contacto e información para validar identidad.
''';

class _LoginSignalHeader extends StatelessWidget {
  const _LoginSignalHeader({required this.animation});

  final Animation<double> animation;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: animation,
      builder: (BuildContext context, Widget? child) {
        final pulse = 0.92 + (animation.value * 0.08);
        return Transform.scale(scale: pulse, child: child);
      },
      child: SizedBox(
        height: 164,
        width: 164,
        child: Stack(
          alignment: Alignment.center,
          children: <Widget>[
            _Ring(size: 164, opacity: 0.10),
            _Ring(size: 126, opacity: 0.16),
            _Ring(size: 88, opacity: 0.22),
            Container(
              height: 72,
              width: 72,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(26),
                border: Border.all(color: Colors.white.withValues(alpha: 0.28)),
              ),
              child: const Icon(
                Icons.security_rounded,
                color: Colors.white,
                size: 36,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Ring extends StatelessWidget {
  const _Ring({required this.size, required this.opacity});

  final double size;
  final double opacity;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: size,
      width: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: Colors.white.withValues(alpha: opacity),
          width: 1.4,
        ),
      ),
    );
  }
}

class _SignalBadge extends StatelessWidget {
  const _SignalBadge({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withValues(alpha: 0.12)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(icon, color: color, size: 17),
            const SizedBox(width: 7),
            Flexible(
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: color,
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
