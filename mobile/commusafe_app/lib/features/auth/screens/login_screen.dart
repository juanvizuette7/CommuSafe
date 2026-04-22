import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
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

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 850),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCubic,
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.16),
      end: Offset.zero,
    ).animate(
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
    final titleStyle = Theme.of(context).textTheme.headlineMedium?.copyWith(
          color: AppColors.primary,
          fontWeight: FontWeight.w800,
          letterSpacing: -0.8,
        );

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: <Color>[
              AppColors.primary,
              AppColors.accent,
            ],
          ),
        ),
        child: Stack(
          children: <Widget>[
            Positioned(
              top: -90,
              right: -30,
              child: _GlowCircle(
                size: 220,
                color: Colors.white.withValues(alpha: 0.08),
              ),
            ),
            Positioned(
              bottom: -100,
              left: -20,
              child: _GlowCircle(
                size: 260,
                color: Colors.white.withValues(alpha: 0.06),
              ),
            ),
            SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 32,
                  ),
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: SlideTransition(
                      position: _slideAnimation,
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(28),
                        child: BackdropFilter(
                          filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
                          child: Container(
                            constraints: const BoxConstraints(maxWidth: 440),
                            padding: const EdgeInsets.all(28),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.90),
                              borderRadius: BorderRadius.circular(28),
                              border: Border.all(
                                color: Colors.white.withValues(alpha: 0.45),
                              ),
                              boxShadow: <BoxShadow>[
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.10),
                                  blurRadius: 36,
                                  offset: const Offset(0, 24),
                                ),
                              ],
                            ),
                            child: AutofillGroup(
                              child: Form(
                                key: _formKey,
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: <Widget>[
                                    Container(
                                      height: 72,
                                      width: 72,
                                      decoration: BoxDecoration(
                                        borderRadius: BorderRadius.circular(22),
                                        gradient: const LinearGradient(
                                          colors: <Color>[
                                            AppColors.primary,
                                            AppColors.accent,
                                          ],
                                        ),
                                        boxShadow: <BoxShadow>[
                                          BoxShadow(
                                            color: AppColors.primary.withValues(
                                              alpha: 0.24,
                                            ),
                                            blurRadius: 22,
                                            offset: const Offset(0, 14),
                                          ),
                                        ],
                                      ),
                                      child: const Icon(
                                        Icons.shield_rounded,
                                        color: Colors.white,
                                        size: 34,
                                      ),
                                    ),
                                    const SizedBox(height: 24),
                                    Text(
                                      AppConstants.appName,
                                      style: titleStyle,
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      AppConstants.residentialComplexName,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium
                                          ?.copyWith(
                                            color: AppColors.textSecondary,
                                            fontWeight: FontWeight.w500,
                                          ),
                                    ),
                                    const SizedBox(height: 18),
                                    Container(
                                      height: 1,
                                      width: double.infinity,
                                      color: AppColors.muted,
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
                                      onChanged: (_) => authProvider.clearError(),
                                      decoration: const InputDecoration(
                                        labelText: 'Correo electrónico',
                                        prefixIcon: Icon(
                                          Icons.email_outlined,
                                        ),
                                      ),
                                      validator: (String? value) {
                                        final text = value?.trim() ?? '';
                                        if (text.isEmpty) {
                                          return 'Ingresa tu correo electrónico.';
                                        }
                                        final emailRegex = RegExp(
                                          r'^[\w\.\-]+@([\w\-]+\.)+[a-zA-Z]{2,}$',
                                        );
                                        if (!emailRegex.hasMatch(text)) {
                                          return 'Escribe un correo electrónico válido.';
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
                                      onChanged: (_) => authProvider.clearError(),
                                      decoration: InputDecoration(
                                        labelText: 'Contraseña',
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
                                        if (value == null || value.trim().isEmpty) {
                                          return 'Ingresa tu contraseña.';
                                        }
                                        return null;
                                      },
                                      onFieldSubmitted: (_) => _submit(),
                                    ),
                                    if (errorMessage != null &&
                                        errorMessage.trim().isNotEmpty) ...<Widget>[
                                      const SizedBox(height: 18),
                                      Container(
                                        width: double.infinity,
                                        padding: const EdgeInsets.all(14),
                                        decoration: BoxDecoration(
                                          color: AppColors.danger.withValues(
                                            alpha: 0.10,
                                          ),
                                          borderRadius: BorderRadius.circular(16),
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
                                    const SizedBox(height: 24),
                                    DecoratedBox(
                                      decoration: BoxDecoration(
                                        borderRadius: BorderRadius.circular(14),
                                        gradient: const LinearGradient(
                                          colors: <Color>[
                                            AppColors.primary,
                                            AppColors.accent,
                                          ],
                                        ),
                                        boxShadow: <BoxShadow>[
                                          BoxShadow(
                                            color: AppColors.primary.withValues(
                                              alpha: 0.26,
                                            ),
                                            blurRadius: 18,
                                            offset: const Offset(0, 12),
                                          ),
                                        ],
                                      ),
                                      child: Material(
                                        color: Colors.transparent,
                                        child: InkWell(
                                          borderRadius:
                                              BorderRadius.circular(14),
                                          onTap: isLoading ? null : _submit,
                                          child: SizedBox(
                                            height: 56,
                                            width: double.infinity,
                                            child: Center(
                                              child: AnimatedSwitcher(
                                                duration: const Duration(
                                                  milliseconds: 200,
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
                                                          color: Colors.white,
                                                        ),
                                                      )
                                                    : Text(
                                                        'Ingresar',
                                                        key: const ValueKey<String>(
                                                          'label',
                                                        ),
                                                        style: Theme.of(context)
                                                            .textTheme
                                                            .titleSmall
                                                            ?.copyWith(
                                                              color:
                                                                  Colors.white,
                                                              fontWeight:
                                                                  FontWeight
                                                                      .w700,
                                                            ),
                                                      ),
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
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GlowCircle extends StatelessWidget {
  const _GlowCircle({
    required this.size,
    required this.color,
  });

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: size,
      width: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: <Color>[
            color,
            Colors.transparent,
          ],
        ),
      ),
    );
  }
}
