import 'dart:ui';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/services/api_service.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/commusafe_animated_background.dart';

class ResetSolicitarScreen extends StatefulWidget {
  const ResetSolicitarScreen({super.key});

  @override
  State<ResetSolicitarScreen> createState() => _ResetSolicitarScreenState();
}

class _ResetSolicitarScreenState extends State<ResetSolicitarScreen>
    with SingleTickerProviderStateMixin {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _emailController = TextEditingController();
  bool _isLoading = false;
  String? _message;
  bool _success = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    FocusScope.of(context).unfocus();
    setState(() {
      _isLoading = true;
      _message = null;
      _success = false;
    });

    try {
      await ApiService.post<Map<String, dynamic>>(
        AppConstants.resetRequestEndpoint,
        data: <String, dynamic>{
          'email': _emailController.text.trim().toLowerCase(),
        },
        options: Options(extra: <String, dynamic>{'omitAuth': true}),
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _success = true;
        _message = 'Si el correo existe, recibirás un enlace de recuperación.';
      });
    } on DioException {
      if (!mounted) {
        return;
      }
      setState(() {
        _success = false;
        _message =
            'No se pudo procesar la solicitud. Verifica tu conexión e intenta nuevamente.';
      });
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
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
                            'Recuperar contraseña',
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Ingresa tu correo y enviaremos un enlace seguro para restablecer tu acceso.',
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: AppColors.textSecondary,
                                  height: 1.45,
                                ),
                          ),
                          const SizedBox(height: 24),
                          TextFormField(
                            controller: _emailController,
                            keyboardType: TextInputType.emailAddress,
                            enabled: !_isLoading,
                            decoration: const InputDecoration(
                              labelText: 'Correo electrónico',
                              prefixIcon: Icon(Icons.email_outlined),
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
                          if (_message != null) ...<Widget>[
                            const SizedBox(height: 18),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color:
                                    (_success
                                            ? AppColors.success
                                            : AppColors.danger)
                                        .withValues(alpha: 0.10),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color:
                                      (_success
                                              ? AppColors.success
                                              : AppColors.danger)
                                          .withValues(alpha: 0.20),
                                ),
                              ),
                              child: Text(
                                _message!,
                                style: Theme.of(context).textTheme.bodyMedium
                                    ?.copyWith(
                                      color: _success
                                          ? AppColors.success
                                          : AppColors.danger,
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
                                : const Icon(Icons.send_rounded),
                            label: Text(
                              _isLoading
                                  ? 'Enviando...'
                                  : 'Enviar enlace de recuperación',
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
