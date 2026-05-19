import 'dart:ui';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/services/api_service.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/commusafe_animated_background.dart';

class ResetConfirmarScreen extends StatefulWidget {
  const ResetConfirmarScreen({required this.token, super.key});

  final String token;

  @override
  State<ResetConfirmarScreen> createState() => _ResetConfirmarScreenState();
}

class _ResetConfirmarScreenState extends State<ResetConfirmarScreen> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _password2Controller = TextEditingController();
  bool _obscurePassword = true;
  bool _obscurePassword2 = true;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _passwordController.dispose();
    _password2Controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    FocusScope.of(context).unfocus();
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await ApiService.post<Map<String, dynamic>>(
        AppConstants.resetConfirmEndpoint,
        data: <String, dynamic>{
          'token': widget.token,
          'password': _passwordController.text,
          'password2': _password2Controller.text,
        },
        options: Options(extra: <String, dynamic>{'omitAuth': true}),
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Contraseña actualizada. Inicia sesión nuevamente.'),
          backgroundColor: AppColors.success,
          behavior: SnackBarBehavior.floating,
        ),
      );
      context.go('/login');
    } on DioException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _errorMessage = _extractErrorMessage(error));
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  String _extractErrorMessage(DioException error) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.trim().isNotEmpty) {
        return detail;
      }
      final password = data['password'];
      if (password is List && password.isNotEmpty) {
        return password.first.toString();
      }
      final password2 = data['password2'];
      if (password2 is List && password2.isNotEmpty) {
        return password2.first.toString();
      }
      final token = data['token'];
      if (token is List && token.isNotEmpty) {
        return token.first.toString();
      }
    }
    return 'No se pudo actualizar la contraseña. Solicita un enlace nuevo e intenta nuevamente.';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CommuSafeAnimatedBackground(
        dark: true,
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 28),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(30),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
                  child: Container(
                    constraints: const BoxConstraints(maxWidth: 450),
                    padding: const EdgeInsets.fromLTRB(26, 28, 26, 26),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.93),
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
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: <Widget>[
                          IconButton.filledTonal(
                            onPressed: _isLoading
                                ? null
                                : () => context.go('/login'),
                            icon: const Icon(Icons.arrow_back_rounded),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Nueva contraseña',
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Define una contraseña segura para recuperar tu acceso a CommuSafe.',
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: AppColors.textSecondary,
                                  height: 1.45,
                                ),
                          ),
                          const SizedBox(height: 24),
                          TextFormField(
                            controller: _passwordController,
                            obscureText: _obscurePassword,
                            enabled: !_isLoading,
                            decoration: InputDecoration(
                              labelText: 'Nueva contraseña',
                              prefixIcon: const Icon(Icons.lock_outline),
                              suffixIcon: IconButton(
                                onPressed: _isLoading
                                    ? null
                                    : () {
                                        setState(() {
                                          _obscurePassword = !_obscurePassword;
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
                              final password = value ?? '';
                              if (password.isEmpty) {
                                return 'Ingresa la contraseña nueva.';
                              }
                              if (password.length < 8) {
                                return 'La contraseña debe tener mínimo 8 caracteres.';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _password2Controller,
                            obscureText: _obscurePassword2,
                            enabled: !_isLoading,
                            decoration: InputDecoration(
                              labelText: 'Confirmar contraseña',
                              prefixIcon: const Icon(Icons.lock_reset_rounded),
                              suffixIcon: IconButton(
                                onPressed: _isLoading
                                    ? null
                                    : () {
                                        setState(() {
                                          _obscurePassword2 =
                                              !_obscurePassword2;
                                        });
                                      },
                                icon: Icon(
                                  _obscurePassword2
                                      ? Icons.visibility_outlined
                                      : Icons.visibility_off_outlined,
                                ),
                              ),
                            ),
                            validator: (String? value) {
                              final password2 = value ?? '';
                              if (password2.isEmpty) {
                                return 'Confirma la contraseña nueva.';
                              }
                              if (password2 != _passwordController.text) {
                                return 'Las contraseñas no coinciden.';
                              }
                              return null;
                            },
                          ),
                          if (_errorMessage != null) ...<Widget>[
                            const SizedBox(height: 18),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: AppColors.danger.withValues(alpha: 0.10),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: AppColors.danger.withValues(
                                    alpha: 0.20,
                                  ),
                                ),
                              ),
                              child: Text(
                                _errorMessage!,
                                style: Theme.of(context).textTheme.bodyMedium
                                    ?.copyWith(
                                      color: AppColors.danger,
                                      fontWeight: FontWeight.w700,
                                      height: 1.45,
                                    ),
                              ),
                            ),
                          ],
                          const SizedBox(height: 24),
                          FilledButton.icon(
                            onPressed: _isLoading ? null : _submit,
                            style: FilledButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              minimumSize: const Size.fromHeight(56),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                            icon: _isLoading
                                ? const SizedBox(
                                    height: 18,
                                    width: 18,
                                    child: CircularProgressIndicator(
                                      color: Colors.white,
                                      strokeWidth: 2.3,
                                    ),
                                  )
                                : const Icon(Icons.check_rounded),
                            label: Text(
                              _isLoading
                                  ? 'Actualizando...'
                                  : 'Actualizar contraseña',
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
    );
  }
}
