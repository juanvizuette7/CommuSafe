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
            title: l10n.tr('Color de la aplicación', 'App color'),
            subtitle: l10n.tr(
              'Cambia la identidad visual de toda la app.',
              'Change the visual identity across the app.',
            ),
            child: Wrap(
              spacing: 10,
              runSpacing: 10,
              children: ColorPreset.values.map((preset) {
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
            title: l10n.tr('Tamaño de letra', 'Text size'),
            subtitle: l10n.tr(
              'Ajusta el texto para leer mejor en el celular.',
              'Adjust text for better reading on mobile.',
            ),
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: TextSizePreset.values.map((preset) {
                return ChoiceChip(
                  selected: preset == settings.textSizePreset,
                  label: Text(_textSizeLabel(preset, l10n)),
                  onSelected: (_) => settings.setTextSizePreset(preset),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 14),
          _SettingsSection(
            icon: Icons.contrast_rounded,
            title: l10n.tr('Accesibilidad visual', 'Visual accessibility'),
            subtitle: l10n.tr(
              'Contraste, movimiento y espacio visual.',
              'Contrast, motion and visual spacing.',
            ),
            child: Column(
              children: <Widget>[
                _SettingsSwitchTile(
                  icon: Icons.visibility_rounded,
                  title: l10n.tr('Alto contraste', 'High contrast'),
                  subtitle: l10n.tr(
                    'Texto más fuerte y bordes más claros.',
                    'Stronger text and clearer borders.',
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
                  title: l10n.tr('Modo cómodo', 'Comfort mode'),
                  subtitle: l10n.tr(
                    'Más aire visual en tarjetas y controles.',
                    'More breathing room in cards and controls.',
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
              'Cambia la interfaz principal entre español e inglés.',
              'Switch the main interface between Spanish and English.',
            ),
            child: Column(
              children: LanguagePreset.values.map((preset) {
                final selected = preset == settings.languagePreset;
                return ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(
                    selected
                        ? Icons.radio_button_checked_rounded
                        : Icons.radio_button_off_rounded,
                    color: selected ? theme.primary : theme.textSecondary,
                  ),
                  title: Text(preset.label),
                  subtitle: Text(
                    preset == LanguagePreset.esCo
                        ? l10n.tr(
                            'Formato y textos en español.',
                            'Spanish text and format.',
                          )
                        : l10n.tr(
                            'Interfaz principal en inglés.',
                            'Main interface in English.',
                          ),
                  ),
                  onTap: () => settings.setLanguagePreset(preset),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 18),
          OutlinedButton.icon(
            onPressed: settings.reset,
            icon: const Icon(Icons.restart_alt_rounded),
            label: Text(l10n.tr('Restablecer diseño original', 'Reset design')),
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

    return AnimatedContainer(
      duration: settings.reduceMotion
          ? Duration.zero
          : const Duration(milliseconds: 360),
      padding: EdgeInsets.all(settings.comfortableMode ? 22 : 18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(30),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[theme.primary, theme.accent, theme.secondary],
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
                child: const Icon(Icons.auto_awesome_rounded, color: Colors.white),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  l10n.tr('Ajustes de experiencia', 'Experience settings'),
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            l10n.tr(
              'Color, contraste, letra e idioma se aplican a la app principal.',
              'Color, contrast, text and language apply to the main app.',
            ),
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.white.withValues(alpha: 0.88),
              fontWeight: FontWeight.w700,
              height: 1.45,
            ),
          ),
        ],
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
                  Icon(Icons.check_circle_rounded, color: preset.primary, size: 19),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              preset.label,
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w900,
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
