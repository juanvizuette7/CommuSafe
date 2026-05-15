import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/app_settings_provider.dart';

class AjustesScreen extends StatelessWidget {
  const AjustesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<AppSettingsProvider>();
    final theme = CommuSafeThemeExtension.of(context);

    return Scaffold(
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: <Widget>[
          _HeroPreview(settings: settings),
          const SizedBox(height: 18),
          _SettingsSection(
            icon: Icons.palette_rounded,
            title: 'Color de la aplicación',
            subtitle: 'Personaliza la identidad visual sin perder legibilidad.',
            child: Wrap(
              spacing: 10,
              runSpacing: 10,
              children: ColorPreset.values.map((ColorPreset preset) {
                return _ColorPresetChip(
                  preset: preset,
                  selected: preset == settings.colorPreset,
                  onTap: () => settings.setColorPreset(preset),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 14),
          _SettingsSection(
            icon: Icons.text_fields_rounded,
            title: 'Tamaño de letra',
            subtitle: 'Ajusta el texto para lectura cómoda en celular.',
            child: Column(
              children: <Widget>[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: TextSizePreset.values.map((TextSizePreset preset) {
                    final selected = preset == settings.textSizePreset;
                    return Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 3),
                        child: ChoiceChip(
                          selected: selected,
                          label: Text(preset.label),
                          onSelected: (_) => settings.setTextSizePreset(preset),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 16),
                AnimatedDefaultTextStyle(
                  duration: settings.reduceMotion
                      ? Duration.zero
                      : const Duration(milliseconds: 260),
                  style: Theme.of(context).textTheme.titleMedium!.copyWith(
                    color: theme.textPrimary,
                    fontWeight: FontWeight.w800,
                    fontSize: 16 * settings.textScaleFactor,
                  ),
                  child: const Text(
                    'Vista previa: reportar un incidente debe sentirse claro y rápido.',
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _SettingsSection(
            icon: Icons.contrast_rounded,
            title: 'Accesibilidad visual',
            subtitle: 'Mejora contraste, reduce movimiento y ajusta espacios.',
            child: Column(
              children: <Widget>[
                _SettingsSwitchTile(
                  icon: Icons.visibility_rounded,
                  title: 'Alto contraste',
                  subtitle:
                      'Texto más fuerte, bordes más claros y mayor lectura.',
                  value: settings.highContrast,
                  onChanged: settings.setHighContrast,
                ),
                const Divider(),
                _SettingsSwitchTile(
                  icon: Icons.motion_photos_pause_rounded,
                  title: 'Reducir animaciones',
                  subtitle:
                      'Minimiza transiciones para una experiencia estable.',
                  value: settings.reduceMotion,
                  onChanged: settings.setReduceMotion,
                ),
                const Divider(),
                _SettingsSwitchTile(
                  icon: Icons.space_bar_rounded,
                  title: 'Modo cómodo',
                  subtitle:
                      'Más aire visual en tarjetas y controles importantes.',
                  value: settings.comfortableMode,
                  onChanged: settings.setComfortableMode,
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _SettingsSection(
            icon: Icons.language_rounded,
            title: 'Idioma y formato regional',
            subtitle:
                'Define cómo se muestran fechas, textos del sistema y región.',
            child: Column(
              children: LanguagePreset.values.map((LanguagePreset preset) {
                return _LanguageOptionTile(
                  preset: preset,
                  selected: preset == settings.languagePreset,
                  onTap: () => settings.setLanguagePreset(preset),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 14),
          _SettingsSection(
            icon: Icons.tune_rounded,
            title: 'Experiencia inteligente',
            subtitle: 'Ajustes pensados para una app comunitaria más amable.',
            child: Column(
              children: <Widget>[
                _InsightTile(
                  icon: Icons.bolt_rounded,
                  title: 'Modo operativo',
                  description:
                      'Los colores de prioridad y estado se mantienen para no perder alertas críticas.',
                ),
                _InsightTile(
                  icon: Icons.security_rounded,
                  title: 'Preferencias privadas',
                  description:
                      'Estos ajustes viven solo en tu dispositivo y no afectan a otros usuarios.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          OutlinedButton.icon(
            onPressed: settings.reset,
            icon: const Icon(Icons.restart_alt_rounded),
            label: const Text('Restablecer diseño original'),
          ),
          const SizedBox(height: 10),
          Text(
            '${AppConstants.appName} · ${AppConstants.residentialComplexName}',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: theme.textSecondary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroPreview extends StatelessWidget {
  const _HeroPreview({required this.settings});

  final AppSettingsProvider settings;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return TweenAnimationBuilder<double>(
      duration: settings.reduceMotion
          ? Duration.zero
          : const Duration(milliseconds: 720),
      tween: Tween<double>(begin: 0.92, end: 1),
      curve: Curves.easeOutCubic,
      builder: (BuildContext context, double value, Widget? child) {
        return Transform.scale(scale: value, child: child);
      },
      child: AnimatedContainer(
        duration: settings.reduceMotion
            ? Duration.zero
            : const Duration(milliseconds: 360),
        padding: EdgeInsets.all(settings.comfortableMode ? 22 : 18),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(30),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[
              theme.primary,
              theme.accent,
              theme.secondary.withValues(alpha: 0.92),
            ],
          ),
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: theme.primary.withValues(alpha: 0.24),
              blurRadius: 28,
              offset: const Offset(0, 16),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Container(
                  height: 54,
                  width: 54,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.28),
                    ),
                  ),
                  child: const Icon(
                    Icons.auto_awesome_rounded,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        'Ajustes de experiencia',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Haz que CommuSafe se adapte a ti.',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.white.withValues(alpha: 0.82),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
              ),
              child: Row(
                children: <Widget>[
                  const Icon(
                    Icons.warning_amber_rounded,
                    color: Colors.white,
                    size: 30,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Vista previa: tarjeta clara, botones grandes y alertas visibles.',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SettingsSection extends StatelessWidget {
  const _SettingsSection({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.child,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Container(
                  height: 46,
                  width: 46,
                  decoration: BoxDecoration(
                    color: theme.primary.withValues(alpha: 0.1),
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
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: theme.textSecondary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            child,
          ],
        ),
      ),
    );
  }
}

class _ColorPresetChip extends StatelessWidget {
  const _ColorPresetChip({
    required this.preset,
    required this.selected,
    required this.onTap,
  });

  final ColorPreset preset;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(22),
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        width: 148,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: selected
              ? preset.primary.withValues(alpha: 0.08)
              : const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: selected ? preset.primary : const Color(0xFFE2E8F0),
            width: selected ? 1.6 : 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                _ColorDot(color: preset.primary),
                _ColorDot(color: preset.secondary),
                _ColorDot(color: preset.accent),
                const Spacer(),
                if (selected)
                  Icon(
                    Icons.check_circle_rounded,
                    color: preset.primary,
                    size: 19,
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              preset.label,
              style: Theme.of(
                context,
              ).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 4),
            Text(
              preset.description,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ColorDot extends StatelessWidget {
  const _ColorDot({required this.color});

  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 16,
      width: 16,
      margin: const EdgeInsets.only(right: 4),
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}

class _SettingsSwitchTile extends StatelessWidget {
  const _SettingsSwitchTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return SwitchListTile(
      contentPadding: EdgeInsets.zero,
      value: value,
      onChanged: onChanged,
      secondary: Icon(icon, color: theme.primary),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
      subtitle: Text(subtitle),
    );
  }
}

class _LanguageOptionTile extends StatelessWidget {
  const _LanguageOptionTile({
    required this.preset,
    required this.selected,
    required this.onTap,
  });

  final LanguagePreset preset;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: selected
                ? theme.primary.withValues(alpha: 0.08)
                : const Color(0xFFF8FAFC),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: selected ? theme.primary : const Color(0xFFE2E8F0),
              width: selected ? 1.5 : 1,
            ),
          ),
          child: Row(
            children: <Widget>[
              Icon(
                selected
                    ? Icons.radio_button_checked_rounded
                    : Icons.radio_button_off_rounded,
                color: selected ? theme.primary : AppColors.textSecondary,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      preset.label,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      preset == LanguagePreset.esCo
                          ? 'Formato y fechas para Colombia.'
                          : 'English regional format.',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: theme.textSecondary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InsightTile extends StatelessWidget {
  const _InsightTile({
    required this.icon,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            height: 38,
            width: 38,
            decoration: BoxDecoration(
              color: theme.accent.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: theme.accent, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: Theme.of(
                    context,
                  ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 3),
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: theme.textSecondary,
                    fontWeight: FontWeight.w600,
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
