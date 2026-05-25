import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../incidentes/providers/incidente_provider.dart';
import '../../notificaciones/providers/notificacion_provider.dart';
import '../models/usuario_model.dart';
import '../providers/auth_provider.dart';

class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  final ImagePicker _imagePicker = ImagePicker();
  bool _subiendoFoto = false;

  Future<void> _logout(BuildContext context) async {
    final authProvider = context.read<AuthProvider>();
    final incidenteProvider = context.read<IncidenteProvider>();
    final notificacionProvider = context.read<NotificacionProvider>();

    await authProvider.logout();
    incidenteProvider.reset();
    notificacionProvider.reset();
    if (!context.mounted) {
      return;
    }
    context.go('/login');
  }

  Future<void> _abrirSelectorFoto() async {
    final theme = CommuSafeThemeExtension.of(context);
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      backgroundColor: theme.surface,
      showDragHandle: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
      ),
      builder: (BuildContext context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(18, 4, 18, 18),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor: theme.primary,
                    foregroundColor: Colors.white,
                    child: const Icon(Icons.photo_camera_rounded),
                  ),
                  title: const Text(
                    'Tomar foto',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  onTap: () => Navigator.of(context).pop(ImageSource.camera),
                ),
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor: theme.accent,
                    foregroundColor: Colors.white,
                    child: const Icon(Icons.photo_library_rounded),
                  ),
                  title: const Text(
                    'Elegir de galería',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  onTap: () => Navigator.of(context).pop(ImageSource.gallery),
                ),
              ],
            ),
          ),
        );
      },
    );

    if (source == null || !mounted) {
      return;
    }

    try {
      final picked = await _imagePicker.pickImage(
        source: source,
        imageQuality: 82,
        maxWidth: 1200,
      );
      if (picked == null || !mounted) {
        return;
      }

      setState(() => _subiendoFoto = true);
      final ok = await context.read<AuthProvider>().actualizarFotoPerfil(
        File(picked.path),
      );
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(ok ? 'Foto actualizada' : 'No se pudo subir la foto'),
          backgroundColor: ok ? AppColors.success : AppColors.danger,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (_) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo subir la foto'),
          backgroundColor: AppColors.danger,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _subiendoFoto = false);
      }
    }
  }

  Future<void> _abrirEditorPerfil(UsuarioModel usuario) async {
    final actualizado = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (BuildContext context) {
        return _EditProfileSheet(usuario: usuario);
      },
    );

    if (!mounted || actualizado != true) {
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Perfil actualizado correctamente'),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final usuario = authProvider.usuarioActual;

    if (usuario == null && authProvider.isInitializing) {
      return const Center(child: CircularProgressIndicator());
    }

    if (usuario == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'No fue posible cargar la información del perfil.',
            style: Theme.of(context).textTheme.titleMedium,
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => context.read<AuthProvider>().cargarPerfil(),
      child: ListView(
        padding: EdgeInsets.zero,
        children: <Widget>[
          _ProfileHeader(
            usuario: usuario,
            subiendoFoto: _subiendoFoto,
            onAvatarTap: _abrirSelectorFoto,
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
            child: Column(
              children: <Widget>[
                _ProfileStatusPanel(usuario: usuario),
                const SizedBox(height: 14),
                _EditProfileCta(
                  usuario: usuario,
                  onTap: () => _abrirEditorPerfil(usuario),
                ),
                const SizedBox(height: 14),
                _ProfileQuickActions(usuario: usuario),
                const SizedBox(height: 18),
                _ProfileInfoCard(
                  icon: Icons.alternate_email_rounded,
                  title: 'Correo electrónico',
                  value: usuario.email,
                ),
                const SizedBox(height: 14),
                _ProfileInfoCard(
                  icon: usuario.esResidente
                      ? Icons.home_work_outlined
                      : Icons.apartment_rounded,
                  title: usuario.esResidente
                      ? 'Unidad residencial'
                      : 'Referencia operativa',
                  value: _referenciaUsuario(usuario),
                ),
                const SizedBox(height: 14),
                _ProfileInfoCard(
                  icon: Icons.phone_outlined,
                  title: 'Teléfono',
                  value: usuario.telefono?.trim().isNotEmpty == true
                      ? usuario.telefono!
                      : 'No registrado',
                ),
                const SizedBox(height: 14),
                _ProfileInfoCard(
                  icon: Icons.tune_rounded,
                  title: 'Ajustes de experiencia',
                  value: 'Contraste, color, letra e idioma',
                  onTap: () => context.push('/ajustes'),
                ),
                const SizedBox(height: 14),
                _RoleCapabilitiesCard(usuario: usuario),
                const SizedBox(height: 28),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _logout(context),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.danger,
                      foregroundColor: Colors.white,
                      minimumSize: const Size.fromHeight(54),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    icon: const Icon(Icons.logout_rounded),
                    label: const Text('Cerrar sesión'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

String _referenciaUsuario(UsuarioModel usuario) {
  final unidad = usuario.unidadResidencial?.trim();
  if (usuario.esResidente) {
    return unidad?.isNotEmpty == true ? unidad! : 'No registrada';
  }
  if (usuario.esAdmin) {
    return 'Administración';
  }
  if (usuario.esVigilante) {
    return unidad?.isNotEmpty == true ? unidad! : 'Portería Remansos';
  }
  return unidad?.isNotEmpty == true ? unidad! : 'Remansos del Norte';
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({
    required this.usuario,
    required this.subiendoFoto,
    required this.onAvatarTap,
  });

  final UsuarioModel usuario;
  final bool subiendoFoto;
  final VoidCallback onAvatarTap;

  Color _badgeColor(CommuSafeThemeExtension theme) {
    if (usuario.esAdmin) {
      return theme.primary;
    }
    if (usuario.esVigilante) {
      return theme.accent;
    }
    return AppColors.success;
  }

  IconData _roleIcon() {
    if (usuario.esAdmin) {
      return Icons.admin_panel_settings_rounded;
    }
    if (usuario.esVigilante) {
      return Icons.security_rounded;
    }
    return Icons.home_rounded;
  }

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Container(
      padding: const EdgeInsets.fromLTRB(24, 30, 24, 32),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[theme.primary, theme.secondary, theme.accent],
        ),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(34),
          bottomRight: Radius.circular(34),
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: theme.primary.withValues(alpha: 0.32),
            blurRadius: 26,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: Column(
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.16),
                  ),
                ),
                child: const Text(
                  'CommuSafe ID',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 12,
                  ),
                ),
              ),
              const Spacer(),
              Icon(_roleIcon(), color: Colors.white, size: 28),
            ],
          ),
          const SizedBox(height: 18),
          GestureDetector(
            onTap: subiendoFoto ? null : onAvatarTap,
            child: Stack(
              alignment: Alignment.center,
              children: <Widget>[
                Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.38),
                      width: 2,
                    ),
                    boxShadow: <BoxShadow>[
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.22),
                        blurRadius: 18,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: CircleAvatar(
                    radius: 46,
                    backgroundColor: Colors.white.withValues(alpha: 0.14),
                    backgroundImage: usuario.fotoPerfilUrl != null
                        ? CachedNetworkImageProvider(usuario.fotoPerfilUrl!)
                        : null,
                    child: usuario.fotoPerfilUrl == null
                        ? Text(
                            usuario.iniciales,
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w900,
                                ),
                          )
                        : null,
                  ),
                ),
                Positioned(
                  right: 0,
                  bottom: 0,
                  child: Container(
                    height: 32,
                    width: 32,
                    decoration: BoxDecoration(
                      color: _badgeColor(theme),
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                    child: const Icon(
                      Icons.camera_alt_rounded,
                      color: Colors.white,
                      size: 17,
                    ),
                  ),
                ),
                if (subiendoFoto)
                  Container(
                    height: 94,
                    width: 94,
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.48),
                      shape: BoxShape.circle,
                    ),
                    child: const Padding(
                      padding: EdgeInsets.all(28),
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2.6,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Text(
            usuario.nombreCompleto,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _referenciaUsuario(usuario),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.white.withValues(alpha: 0.78),
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 8),
            decoration: BoxDecoration(
              color: _badgeColor(theme).withValues(alpha: 0.28),
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: Colors.white.withValues(alpha: 0.16)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(_roleIcon(), size: 16, color: Colors.white),
                const SizedBox(width: 7),
                Text(
                  usuario.rolLegible,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EditProfileCta extends StatelessWidget {
  const _EditProfileCta({required this.usuario, required this.onTap});

  final UsuarioModel usuario;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    final phoneReady = usuario.telefono?.trim().isNotEmpty == true;

    return Material(
      color: theme.primary.withValues(alpha: 0.08),
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: <Widget>[
              Container(
                height: 48,
                width: 48,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: <Color>[theme.primary, theme.accent],
                  ),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Icon(Icons.edit_rounded, color: Colors.white),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Editar datos personales',
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      phoneReady
                          ? 'Nombre y celular listos para contacto.'
                          : 'Agrega tu celular para mejorar el contacto.',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: theme.textSecondary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: theme.primary),
            ],
          ),
        ),
      ),
    );
  }
}

class _EditProfileSheet extends StatefulWidget {
  const _EditProfileSheet({required this.usuario});

  final UsuarioModel usuario;

  @override
  State<_EditProfileSheet> createState() => _EditProfileSheetState();
}

class _EditProfileSheetState extends State<_EditProfileSheet> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreController;
  late final TextEditingController _apellidoController;
  late final TextEditingController _telefonoController;
  late final TextEditingController _unidadController;

  @override
  void initState() {
    super.initState();
    _nombreController = TextEditingController(text: widget.usuario.nombre);
    _apellidoController = TextEditingController(text: widget.usuario.apellido);
    _telefonoController = TextEditingController(
      text: widget.usuario.telefono ?? '',
    );
    _unidadController = TextEditingController(
      text: widget.usuario.unidadResidencial ?? '',
    );
  }

  @override
  void dispose() {
    _nombreController.dispose();
    _apellidoController.dispose();
    _telefonoController.dispose();
    _unidadController.dispose();
    super.dispose();
  }

  Future<void> _guardar() async {
    final form = _formKey.currentState;
    if (form == null || !form.validate()) {
      return;
    }

    final ok = await context.read<AuthProvider>().actualizarPerfil(
      nombre: _nombreController.text,
      apellido: _apellidoController.text,
      telefono: _telefonoController.text,
      unidadResidencial: _unidadController.text,
    );

    if (!mounted) {
      return;
    }

    if (ok) {
      Navigator.of(context).pop(true);
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          context.read<AuthProvider>().errorMessage ??
              'No se pudo actualizar el perfil.',
        ),
        backgroundColor: AppColors.danger,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    final isLoading = context.watch<AuthProvider>().isLoading;

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 14,
          right: 14,
          bottom: MediaQuery.of(context).viewInsets.bottom + 14,
          top: 14,
        ),
        child: Container(
          padding: const EdgeInsets.fromLTRB(20, 14, 20, 20),
          decoration: BoxDecoration(
            color: theme.surface,
            borderRadius: BorderRadius.circular(28),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: theme.primary.withValues(alpha: 0.18),
                blurRadius: 28,
                offset: const Offset(0, 14),
              ),
            ],
          ),
          child: Form(
            key: _formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Center(
                    child: Container(
                      width: 46,
                      height: 5,
                      decoration: BoxDecoration(
                        color: AppColors.muted,
                        borderRadius: BorderRadius.circular(999),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: <Widget>[
                      Container(
                        height: 48,
                        width: 48,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: <Color>[theme.primary, theme.accent],
                          ),
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: const Icon(
                          Icons.manage_accounts_rounded,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Text(
                              'Actualizar perfil',
                              style: Theme.of(context).textTheme.titleLarge
                                  ?.copyWith(fontWeight: FontWeight.w900),
                            ),
                            Text(
                              'Estos datos ayudan a contactarte rápido.',
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(
                                    color: theme.textSecondary,
                                    fontWeight: FontWeight.w700,
                                  ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  TextFormField(
                    controller: _nombreController,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(
                      labelText: 'Nombre',
                      prefixIcon: Icon(Icons.person_outline_rounded),
                    ),
                    validator: (String? value) {
                      if ((value ?? '').trim().length < 2) {
                        return 'Escribe un nombre válido.';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _apellidoController,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(
                      labelText: 'Apellido',
                      prefixIcon: Icon(Icons.badge_outlined),
                    ),
                    validator: (String? value) {
                      if ((value ?? '').trim().length < 2) {
                        return 'Escribe un apellido válido.';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _telefonoController,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      labelText: 'Celular colombiano',
                      hintText: 'Ej. 3001234567',
                      prefixIcon: Icon(Icons.phone_iphone_rounded),
                    ),
                    validator: (String? value) {
                      final text = (value ?? '').replaceAll(RegExp(r'\s+'), '');
                      if (text.isEmpty) {
                        return null;
                      }
                      if (!RegExp(r'^(\+57)?3\d{9}$').hasMatch(text)) {
                        return 'Usa un celular colombiano válido.';
                      }
                      return null;
                    },
                  ),
                  if (widget.usuario.esResidente) ...<Widget>[
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _unidadController,
                      textCapitalization: TextCapitalization.words,
                      decoration: const InputDecoration(
                        labelText: 'Unidad residencial',
                        hintText: 'Ej. Apto 301 Torre A',
                        prefixIcon: Icon(Icons.home_work_outlined),
                      ),
                      validator: (String? value) {
                        if ((value ?? '').trim().isEmpty) {
                          return 'La unidad es obligatoria para residentes.';
                        }
                        return null;
                      },
                    ),
                  ],
                  const SizedBox(height: 18),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: isLoading ? null : _guardar,
                      icon: isLoading
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.save_rounded),
                      label: Text(isLoading ? 'Guardando...' : 'Guardar datos'),
                      style: FilledButton.styleFrom(
                        backgroundColor: theme.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 15),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
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
    );
  }
}

class _ProfileStatusPanel extends StatelessWidget {
  const _ProfileStatusPanel({required this.usuario});

  final UsuarioModel usuario;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: theme.surface,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: theme.primary.withValues(alpha: 0.10)),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: theme.primary.withValues(alpha: 0.08),
            blurRadius: 22,
            offset: const Offset(0, 14),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Container(
                height: 46,
                width: 46,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: <Color>[theme.primary, theme.accent],
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(
                  Icons.verified_user_rounded,
                  color: Colors.white,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Cuenta protegida',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Sesión segura con JWT y acceso por rol.',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: theme.textSecondary,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 7,
                ),
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: const Text(
                  'Activo',
                  style: TextStyle(
                    color: AppColors.success,
                    fontWeight: FontWeight.w900,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: <Widget>[
              Expanded(
                child: _MiniProfileMetric(
                  label: 'Rol',
                  value: usuario.rolLegible,
                  icon: Icons.badge_rounded,
                  color: theme.primary,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MiniProfileMetric(
                  label: usuario.esResidente ? 'Unidad' : 'Referencia',
                  value: _referenciaUsuario(usuario),
                  icon: usuario.esResidente
                      ? Icons.home_work_rounded
                      : Icons.apartment_rounded,
                  color: theme.accent,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MiniProfileMetric extends StatelessWidget {
  const _MiniProfileMetric({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w900),
          ),
        ],
      ),
    );
  }
}

class _ProfileQuickActions extends StatelessWidget {
  const _ProfileQuickActions({required this.usuario});

  final UsuarioModel usuario;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    final actions = <_ProfileAction>[
      _ProfileAction(
        title: 'Ajustes',
        subtitle: 'Color y letra',
        icon: Icons.tune_rounded,
        route: '/ajustes',
        color: theme.primary,
      ),
      _ProfileAction(
        title: 'Alertas',
        subtitle: 'Notificaciones',
        icon: Icons.notifications_active_rounded,
        route: '/notificaciones',
        color: AppColors.danger,
      ),
      _ProfileAction(
        title: 'Emergencias',
        subtitle: 'Llamadas',
        icon: Icons.local_police_rounded,
        route: '/emergencias',
        color: const Color(0xFFEA580C),
      ),
      _ProfileAction(
        title: usuario.esResidente ? 'Mis reportes' : 'Incidentes',
        subtitle: usuario.esResidente ? 'Seguimiento' : 'Operación',
        icon: Icons.assignment_rounded,
        route: '/incidentes',
        color: theme.accent,
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          children: <Widget>[
            Text(
              'Accesos rápidos',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
            ),
            const Spacer(),
            Text(
              'Perfil',
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: theme.textSecondary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: actions.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.55,
          ),
          itemBuilder: (BuildContext context, int index) {
            return _ProfileActionCard(action: actions[index]);
          },
        ),
      ],
    );
  }
}

class _ProfileAction {
  const _ProfileAction({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.route,
    required this.color,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final String route;
  final Color color;
}

class _ProfileActionCard extends StatelessWidget {
  const _ProfileActionCard({required this.action});

  final _ProfileAction action;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: action.color.withValues(alpha: 0.09),
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: () => context.push(action.route),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              Container(
                height: 36,
                width: 36,
                decoration: BoxDecoration(
                  color: action.color.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(action.icon, color: action.color, size: 20),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    action.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    action.subtitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RoleCapabilitiesCard extends StatelessWidget {
  const _RoleCapabilitiesCard({required this.usuario});

  final UsuarioModel usuario;

  List<String> get _capabilities {
    if (usuario.esAdmin) {
      return const <String>[
        'Gestionar usuarios y roles',
        'Cerrar o eliminar incidentes con trazabilidad',
        'Enviar avisos comunitarios segmentados',
      ];
    }
    if (usuario.esVigilante) {
      return const <String>[
        'Ver incidentes de toda la comunidad',
        'Actualizar estados con comentario',
        'Enviar avisos operativos a residentes',
      ];
    }
    return const <String>[
      'Reportar incidentes con evidencia',
      'Consultar el avance de tus reportes',
      'Recibir avisos y alertas importantes',
    ];
  }

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[
            theme.primary.withValues(alpha: 0.10),
            theme.accent.withValues(alpha: 0.08),
          ],
        ),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: theme.primary.withValues(alpha: 0.10)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(Icons.auto_awesome_rounded, color: theme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Tu acceso en CommuSafe',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ..._capabilities.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Icon(
                    Icons.check_circle_rounded,
                    color: theme.accent,
                    size: 18,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      item,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w700,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileInfoCard extends StatelessWidget {
  const _ProfileInfoCard({
    required this.icon,
    required this.title,
    required this.value,
    this.onTap,
  });

  final IconData icon;
  final String title;
  final String value;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: <Widget>[
              Container(
                height: 48,
                width: 48,
                decoration: BoxDecoration(
                  color: theme.primary.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(icon, color: theme.primary),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      title,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      value,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              if (onTap != null)
                Icon(Icons.chevron_right_rounded, color: theme.primary),
            ],
          ),
        ),
      ),
    );
  }
}
