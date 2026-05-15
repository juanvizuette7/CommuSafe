import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/app_settings_provider.dart';

class AjustesScreen extends StatelessWidget {
  const AjustesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<AppSettingsProvider>();
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: <Widget>[
          _HeroPreview(settings: settings),
          const SizedBox(height: 18),
          _SettingsSection(
            icon: Icons.palette_rounded,
            title: l10n.tr('Color de la aplicacion', 'App color'),
            subtitle: l10n.tr(
              'Personaliza la identidad visual sin perder legibilidad.',
              'Customize the visual identity without losing readability.',
            ),
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
            title: l10n.tr('Tamano de letra', 'Text size'),
            subtitle: l10n.tr(
              'Ajusta el texto para lectura comoda en celular.',
              'Adjust text for comfortable reading on mobile.',
            ),
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
                          label: Text(_textSizeLabel(preset, l10n)),
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
                  child: Text(
                    l10n.tr(
                      'Vista previa: reportar un incidente debe sentirse claro y rapido.',
                      'Preview: reporting an incident should feel clear and fast.',
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _SettingsSection(
            icon: Icons.contrast_rounded,
            title: l10n.tr('Accesibilidad visual', 'Visual accessibility'),
            subtitle: l10n.tr(
              'Mejora contraste, reduce movimiento y ajusta espacios.',
              'Improve contrast, reduce motion and tune spacing.',
            ),
            child: Column(
              children: <Widget>[
                _SettingsSwitchTile(
                  icon: Icons.visibility_rounded,
                  title: l10n.tr('Alto contraste', 'High contrast'),
                  subtitle: l10n.tr(
                    'Texto mas fuerte, bordes mas claros y mayor lectura.',
                    'Stronger text, clearer borders and better readability.',
                  ),
                  value: settings.highContrast,
                  onChanged: settings.setHighContrast,
                ),
                const Divider(),
                _SettingsSwitchTile(
                  icon: Icons.motion_photos_pause_rounded,
                  title: l10n.tr('Reducir animaciones', 'Reduce animations'),
                  subtitle: l10n.tr(
                    'Minimiza transiciones para una experiencia estable.',
                    'Minimize transitions for a steadier experience.',
                  ),
                  value: settings.reduceMotion,
                  onChanged: settings.setReduceMotion,
                ),
                const Divider(),
                _SettingsSwitchTile(
                  icon: Icons.space_bar_rounded,
                  title: l10n.tr('Modo comodo', 'Comfort mode'),
                  subtitle: l10n.tr(
                    'Mas aire visual en tarjetas y controles importantes.',
                    'More breathing room in cards and important controls.',
                  ),
                  value: settings.comfortableMode,
                  onChanged: settings.setComfortableMode,
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _SettingsSection(
            icon: Icons.language_rounded,
            title: l10n.tr('Idioma', 'Language'),
            subtitle: l10n.tr(
              'Cambia entre espanol e ingles para la interfaz principal.',
              'Switch the main interface between Spanish and English.',
            ),
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
            title: l10n.tr('Experiencia inteligente', 'Smart experience'),
            subtitle: l10n.tr(
              'Ajustes pensados para una app comunitaria mas amable.',
              'Settings designed for a friendlier community app.',
            ),
            child: Column(
              children: <Widget>[
                _InsightTile(
                  icon: Icons.bolt_rounded,
                  title: l10n.tr('Modo operativo', 'Operational mode'),
                  description: l10n.tr(
                    'Las emergencias conservan color rojo para no perder alertas criticas.',
                    'Emergencies stay red so critical alerts remain clear.',
                  ),
                ),
                _InsightTile(
                  icon: Icons.security_rounded,
                  title: l10n.tr(
                    'Preferencias privadas',
                    'Private preferences',
                  ),
                  description: l10n.tr(
                    'Estos ajustes viven solo en tu dispositivo y no afectan a otros usuarios.',
                    'These settings live only on your device and do not affect other users.',
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          OutlinedButton.icon(
            onPressed: settings.reset,
            icon: const Icon(Icons.restart_alt_rounded),
            label: Text(l10n.tr('Restablecer diseno original', 'Reset design')),
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
    final l10n = AppLocalizations.of(context);

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
                        l10n.tr(
                          'Ajustes de experiencia',
                          'Experience settings',
                        ),
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        l10n.tr(
                          'Haz que CommuSafe se adapte a ti.',
                          'Make CommuSafe adapt to you.',
                        ),
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
                      l10n.tr(
                        'Vista previa: tarjeta clara, botones grandes y alertas visibles.',
                        'Preview: clear card, large buttons and visible alerts.',
                      ),
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

String _textSizeLabel(TextSizePreset preset, AppLocalizations l10n) {
  switch (preset) {
    case TextSizePreset.compacto:
      return l10n.tr('Compacto', 'Compact');
    case TextSizePreset.normal:
      return l10n.tr('Normal', 'Normal');
    case TextSizePreset.grande:
      return l10n.tr('Grande', 'Large');
    case TextSizePreset.extraGrande:
      return l10n.tr('Muy grande', 'Extra large');
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
    final l10n = AppLocalizations.of(context);

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
              _label(l10n),
              style: Theme.of(
                context,
              ).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 4),
            Text(
              _description(l10n),
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

  String _label(AppLocalizations l10n) {
    switch (preset) {
      case ColorPreset.remansos:
        return l10n.tr('Azul Remansos', 'Remansos blue');
      case ColorPreset.esmeralda:
        return l10n.tr('Verde seguro', 'Safe green');
      case ColorPreset.atardecer:
        return l10n.tr('Alerta calida', 'Warm alert');
      case ColorPreset.carbono:
        return l10n.tr('Carbono elegante', 'Elegant carbon');
    }
  }

  String _description(AppLocalizations l10n) {
    switch (preset) {
      case ColorPreset.remansos:
        return l10n.tr(
          'Identidad original de CommuSafe.',
          'Original CommuSafe identity.',
        );
      case ColorPreset.esmeralda:
        return l10n.tr(
          'Mas fresco y amable para lectura diaria.',
          'Fresher and friendlier for daily reading.',
        );
      case ColorPreset.atardecer:
        return l10n.tr(
          'Mayor energia visual para alertas.',
          'More visual energy for alerts.',
        );
      case ColorPreset.carbono:
        return l10n.tr(
          'Sobrio, fuerte y de alto contraste.',
          'Clean, strong and high contrast.',
        );
    }
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
    final l10n = AppLocalizations.of(context);

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
                          ? l10n.tr(
                              'Formato y fechas para Colombia.',
                              'Colombian date and format settings.',
                            )
                          : l10n.tr(
                              'Formato regional en ingles.',
                              'English regional format.',
                            ),
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
