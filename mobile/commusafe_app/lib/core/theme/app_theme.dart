import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  const AppColors._();

  static const Color primary = Color(0xFF1A1A2E);
  static const Color secondary = Color(0xFF16213E);
  static const Color accent = Color(0xFF0F3460);
  static const Color danger = Color(0xFFE94560);
  static const Color success = Color(0xFF10B981);
  static const Color background = Color(0xFFF8FAFC);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color muted = Color(0xFFE2E8F0);
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF475569);
  static const Color warning = Color(0xFFF59E0B);
  static const Color registered = Color(0xFF94A3B8);
  static const Color inProgress = Color(0xFF3B82F6);
  static const Color closed = Color(0xFF111827);

  static Color priorityColor(String prioridad) {
    switch (prioridad.toUpperCase()) {
      case 'ALTA':
        return danger;
      case 'MEDIA':
        return warning;
      case 'BAJA':
        return success;
      default:
        return textSecondary;
    }
  }

  static Color incidentStateColor(String estado) {
    switch (estado.toUpperCase()) {
      case 'REGISTRADO':
        return registered;
      case 'EN_PROCESO':
        return inProgress;
      case 'RESUELTO':
        return success;
      case 'CERRADO':
        return closed;
      default:
        return textSecondary;
    }
  }
}

class AppTheme {
  const AppTheme._();

  static ThemeData lightTheme({
    Color primary = AppColors.primary,
    Color secondary = AppColors.secondary,
    Color accent = AppColors.accent,
    bool highContrast = false,
    bool comfortableMode = true,
  }) {
    final background = highContrast ? Colors.white : AppColors.background;
    final surface = highContrast ? Colors.white : AppColors.surface;
    final textPrimary = highContrast
        ? const Color(0xFF020617)
        : AppColors.textPrimary;
    final textSecondary = highContrast
        ? const Color(0xFF1E293B)
        : AppColors.textSecondary;
    final muted = highContrast ? const Color(0xFFCBD5E1) : AppColors.muted;

    final colorScheme = ColorScheme.fromSeed(
      seedColor: primary,
      primary: primary,
      secondary: accent,
      tertiary: secondary,
      error: AppColors.danger,
      surface: surface,
      brightness: Brightness.light,
    );
    final baseTextTheme = GoogleFonts.poppinsTextTheme();

    return ThemeData(
      useMaterial3: true,
      visualDensity: comfortableMode
          ? VisualDensity.standard
          : VisualDensity.compact,
      materialTapTargetSize: comfortableMode
          ? MaterialTapTargetSize.padded
          : MaterialTapTargetSize.shrinkWrap,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: background,
      primaryColor: primary,
      textTheme: baseTextTheme.apply(
        bodyColor: textPrimary,
        displayColor: textPrimary,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: primary,
        foregroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: highContrast ? 1 : 0,
        shadowColor: Colors.black.withValues(alpha: highContrast ? 0.12 : 0.08),
        margin: EdgeInsets.zero,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size.fromHeight(52),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: baseTextTheme.labelLarge?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primary,
          side: BorderSide(color: primary),
          minimumSize: const Size.fromHeight(50),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: highContrast ? Colors.white : const Color(0xFFF1F5F9),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: muted),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: accent, width: highContrast ? 1.8 : 1.4),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.danger),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.danger, width: 1.4),
        ),
      ),
      drawerTheme: DrawerThemeData(backgroundColor: surface),
      listTileTheme: ListTileThemeData(
        minVerticalPadding: comfortableMode ? 10 : 4,
        iconColor: primary,
        textColor: textPrimary,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        selectedItemColor: primary,
        unselectedItemColor: textSecondary,
        backgroundColor: surface,
        type: BottomNavigationBarType.fixed,
        selectedLabelStyle: baseTextTheme.labelSmall?.copyWith(
          fontWeight: FontWeight.w800,
        ),
      ),
      chipTheme: ChipThemeData(
        selectedColor: primary,
        disabledColor: muted,
        backgroundColor: highContrast ? Colors.white : const Color(0xFFF1F5F9),
        labelStyle: baseTextTheme.labelMedium?.copyWith(
          color: textPrimary,
          fontWeight: FontWeight.w700,
        ),
        secondaryLabelStyle: baseTextTheme.labelMedium?.copyWith(
          color: Colors.white,
          fontWeight: FontWeight.w800,
        ),
        side: BorderSide(color: muted),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected) ? Colors.white : muted;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected)
              ? primary
              : muted.withValues(alpha: 0.88);
        }),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: primary,
        contentTextStyle: baseTextTheme.bodyMedium?.copyWith(
          color: Colors.white,
          fontWeight: FontWeight.w600,
        ),
      ),
      dividerColor: muted,
      extensions: <ThemeExtension<dynamic>>[
        CommuSafeThemeExtension(
          primary: primary,
          secondary: secondary,
          accent: accent,
          background: background,
          surface: surface,
          textPrimary: textPrimary,
          textSecondary: textSecondary,
          highContrast: highContrast,
        ),
      ],
    );
  }
}

@immutable
class CommuSafeThemeExtension extends ThemeExtension<CommuSafeThemeExtension> {
  const CommuSafeThemeExtension({
    required this.primary,
    required this.secondary,
    required this.accent,
    required this.background,
    required this.surface,
    required this.textPrimary,
    required this.textSecondary,
    required this.highContrast,
  });

  final Color primary;
  final Color secondary;
  final Color accent;
  final Color background;
  final Color surface;
  final Color textPrimary;
  final Color textSecondary;
  final bool highContrast;

  static CommuSafeThemeExtension of(BuildContext context) {
    return Theme.of(context).extension<CommuSafeThemeExtension>() ??
        const CommuSafeThemeExtension(
          primary: AppColors.primary,
          secondary: AppColors.secondary,
          accent: AppColors.accent,
          background: AppColors.background,
          surface: AppColors.surface,
          textPrimary: AppColors.textPrimary,
          textSecondary: AppColors.textSecondary,
          highContrast: false,
        );
  }

  @override
  CommuSafeThemeExtension copyWith({
    Color? primary,
    Color? secondary,
    Color? accent,
    Color? background,
    Color? surface,
    Color? textPrimary,
    Color? textSecondary,
    bool? highContrast,
  }) {
    return CommuSafeThemeExtension(
      primary: primary ?? this.primary,
      secondary: secondary ?? this.secondary,
      accent: accent ?? this.accent,
      background: background ?? this.background,
      surface: surface ?? this.surface,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      highContrast: highContrast ?? this.highContrast,
    );
  }

  @override
  CommuSafeThemeExtension lerp(
    ThemeExtension<CommuSafeThemeExtension>? other,
    double t,
  ) {
    if (other is! CommuSafeThemeExtension) {
      return this;
    }
    return CommuSafeThemeExtension(
      primary: Color.lerp(primary, other.primary, t) ?? primary,
      secondary: Color.lerp(secondary, other.secondary, t) ?? secondary,
      accent: Color.lerp(accent, other.accent, t) ?? accent,
      background: Color.lerp(background, other.background, t) ?? background,
      surface: Color.lerp(surface, other.surface, t) ?? surface,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t) ?? textPrimary,
      textSecondary:
          Color.lerp(textSecondary, other.textSecondary, t) ?? textSecondary,
      highContrast: t < 0.5 ? highContrast : other.highContrast,
    );
  }
}
