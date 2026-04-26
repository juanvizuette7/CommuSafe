import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/notificacion_provider.dart';

class CrearAvisoScreen extends StatefulWidget {
  const CrearAvisoScreen({super.key});

  @override
  State<CrearAvisoScreen> createState() => _CrearAvisoScreenState();
}

class _CrearAvisoScreenState extends State<CrearAvisoScreen> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _tituloController = TextEditingController();
  final TextEditingController _cuerpoController = TextEditingController();

  String _tipo = 'AVISO_ADMIN';
  String _audiencia = 'RESIDENTES';

  static const List<_NoticeOption> _tipos = <_NoticeOption>[
    _NoticeOption(
      value: 'AVISO_ADMIN',
      label: 'Aviso informativo',
      icon: Icons.campaign_rounded,
      description: 'Comunicado operativo o administrativo.',
    ),
    _NoticeOption(
      value: 'EMERGENCIA',
      label: 'Alerta de emergencia',
      icon: Icons.warning_amber_rounded,
      description: 'Situación que requiere atención inmediata.',
    ),
  ];

  static const List<_NoticeOption> _audienciasAdmin = <_NoticeOption>[
    _NoticeOption(
      value: 'TODOS',
      label: 'Todos',
      icon: Icons.groups_rounded,
      description: 'Residentes, vigilancia y administración.',
    ),
    _NoticeOption(
      value: 'RESIDENTES',
      label: 'Residentes',
      icon: Icons.apartment_rounded,
      description: 'Usuarios residentes activos.',
    ),
    _NoticeOption(
      value: 'VIGILANTES',
      label: 'Vigilantes',
      icon: Icons.security_rounded,
      description: 'Personal operativo activo.',
    ),
    _NoticeOption(
      value: 'ADMINISTRADORES',
      label: 'Administradores',
      icon: Icons.admin_panel_settings_rounded,
      description: 'Equipo administrativo activo.',
    ),
  ];

  @override
  void dispose() {
    _tituloController.dispose();
    _cuerpoController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final provider = context.read<NotificacionProvider>();
    final total = await provider.crearAviso(
      titulo: _tituloController.text,
      cuerpo: _cuerpoController.text,
      audiencia: _audiencia,
      tipo: _tipo,
    );

    if (!mounted) {
      return;
    }

    if (total == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            provider.errorMessage ?? 'No fue posible enviar el aviso.',
          ),
          backgroundColor: AppColors.danger,
        ),
      );
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Aviso enviado a $total usuario(s).'),
        backgroundColor: AppColors.success,
      ),
    );
    context.pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final usuario = context.watch<AuthProvider>().usuarioActual;
    final provider = context.watch<NotificacionProvider>();
    final puedeCrear = usuario?.esAdmin == true || usuario?.esVigilante == true;
    final audiencias = usuario?.esAdmin == true
        ? _audienciasAdmin
        : _audienciasAdmin.where((item) => item.value == 'RESIDENTES').toList();

    if (!puedeCrear) {
      return Scaffold(
        appBar: AppBar(title: const Text('Crear aviso')),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text(
              'Solo administradores y vigilantes pueden crear avisos comunitarios.',
              textAlign: TextAlign.center,
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Crear aviso'),
        actions: <Widget>[
          IconButton(
            onPressed: provider.isCreatingNotice ? null : _submit,
            icon: const Icon(Icons.send_rounded),
            tooltip: 'Enviar aviso',
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          physics: const BouncingScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 120),
          children: <Widget>[
            _HeroHeader(tipo: _tipo),
            const SizedBox(height: 22),
            _SectionTitle(
              title: 'Tipo de comunicación',
              subtitle: 'Define cómo se mostrará el aviso en Alertas.',
            ),
            const SizedBox(height: 12),
            ..._tipos.map(
              (option) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _OptionCard(
                  option: option,
                  selected: _tipo == option.value,
                  danger: option.value == 'EMERGENCIA',
                  onTap: () => setState(() => _tipo = option.value),
                ),
              ),
            ),
            if (_tipo == 'EMERGENCIA') ...<Widget>[
              const SizedBox(height: 2),
              _EmergencyBanner(),
            ],
            const SizedBox(height: 24),
            _SectionTitle(
              title: 'Destinatarios',
              subtitle: usuario?.esVigilante == true
                  ? 'Vigilancia envía avisos únicamente a residentes.'
                  : 'Selecciona el grupo que recibirá la notificación.',
            ),
            const SizedBox(height: 12),
            ...audiencias.map(
              (option) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _OptionCard(
                  option: option,
                  selected: _audiencia == option.value,
                  onTap: () => setState(() => _audiencia = option.value),
                ),
              ),
            ),
            const SizedBox(height: 20),
            TextFormField(
              controller: _tituloController,
              textCapitalization: TextCapitalization.sentences,
              maxLength: 150,
              decoration: const InputDecoration(
                labelText: 'Título',
                hintText: 'Ej. Mantenimiento programado',
                prefixIcon: Icon(Icons.title_rounded),
              ),
              validator: (String? value) {
                final text = value?.trim() ?? '';
                if (text.length < 5) {
                  return 'El título debe tener al menos 5 caracteres.';
                }
                return null;
              },
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _cuerpoController,
              minLines: 5,
              maxLines: 8,
              maxLength: 1200,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Mensaje',
                hintText:
                    'Escribe un mensaje claro para que los residentes sepan qué hacer.',
                alignLabelWithHint: true,
                prefixIcon: Padding(
                  padding: EdgeInsets.only(bottom: 92),
                  child: Icon(Icons.notes_rounded),
                ),
              ),
              validator: (String? value) {
                final text = value?.trim() ?? '';
                if (text.length < 10) {
                  return 'El mensaje debe tener al menos 10 caracteres.';
                }
                return null;
              },
            ),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 18),
          child: FilledButton.icon(
            onPressed: provider.isCreatingNotice ? null : _submit,
            icon: provider.isCreatingNotice
                ? const SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.send_rounded),
            label: Text(
              provider.isCreatingNotice ? 'Enviando aviso...' : 'Enviar aviso',
            ),
            style: FilledButton.styleFrom(
              backgroundColor: _tipo == 'EMERGENCIA'
                  ? AppColors.danger
                  : AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(18),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _HeroHeader extends StatelessWidget {
  const _HeroHeader({required this.tipo});

  final String tipo;

  @override
  Widget build(BuildContext context) {
    final isEmergency = tipo == 'EMERGENCIA';
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isEmergency
              ? const <Color>[AppColors.danger, Color(0xFF7F1D1D)]
              : const <Color>[AppColors.primary, AppColors.accent],
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: (isEmergency ? AppColors.danger : AppColors.primary)
                .withValues(alpha: 0.26),
            blurRadius: 26,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: Stack(
        children: <Widget>[
          Positioned(
            right: -34,
            top: -34,
            child: Container(
              height: 120,
              width: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withValues(alpha: 0.10),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(22),
            child: Row(
              children: <Widget>[
                Container(
                  height: 58,
                  width: 58,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.16),
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.16),
                    ),
                  ),
                  child: Icon(
                    isEmergency
                        ? Icons.warning_amber_rounded
                        : Icons.campaign_rounded,
                    color: Colors.white,
                    size: 30,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        'Aviso comunitario',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'El mensaje aparecerá en Alertas de la app móvil.',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.white.withValues(alpha: 0.82),
                          height: 1.45,
                        ),
                      ),
                    ],
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

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 4),
        Text(
          subtitle,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: AppColors.textSecondary,
            height: 1.45,
          ),
        ),
      ],
    );
  }
}

class _OptionCard extends StatelessWidget {
  const _OptionCard({
    required this.option,
    required this.selected,
    required this.onTap,
    this.danger = false,
  });

  final _NoticeOption option;
  final bool selected;
  final bool danger;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = danger ? AppColors.danger : AppColors.primary;
    return Material(
      color: selected ? color.withValues(alpha: 0.08) : Colors.white,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: selected ? color : const Color(0xFFE2E8F0),
              width: selected ? 1.6 : 1,
            ),
          ),
          child: Row(
            children: <Widget>[
              Container(
                height: 46,
                width: 46,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: selected ? 0.16 : 0.09),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(option.icon, color: color),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      option.label,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      option.description,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 160),
                child: selected
                    ? Icon(
                        Icons.check_circle_rounded,
                        key: ValueKey(option.value),
                        color: color,
                      )
                    : Icon(
                        Icons.radio_button_unchecked_rounded,
                        key: ValueKey('${option.value}-off'),
                        color: AppColors.textSecondary.withValues(alpha: 0.55),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmergencyBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.danger.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.danger.withValues(alpha: 0.18)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(Icons.priority_high_rounded, color: AppColors.danger),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'Usa esta opción solo para situaciones urgentes. Los residentes verán la alerta con prioridad visual alta.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.danger,
                fontWeight: FontWeight.w700,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NoticeOption {
  const _NoticeOption({
    required this.value,
    required this.label,
    required this.icon,
    required this.description,
  });

  final String value;
  final String label;
  final IconData icon;
  final String description;
}
