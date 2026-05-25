import 'package:flutter/material.dart';

import '../../../core/services/storage_service.dart';
import '../../../core/theme/app_theme.dart';

enum ColorPreset {
  remansos,
  esmeralda,
  atardecer,
  carbono;

  String get storageValue => name;

  String get label {
    switch (this) {
      case ColorPreset.remansos:
        return 'Azul Remansos';
      case ColorPreset.esmeralda:
        return 'Verde seguro';
      case ColorPreset.atardecer:
        return 'Alerta cálida';
      case ColorPreset.carbono:
        return 'Carbono elegante';
    }
  }

  Color get primary {
    switch (this) {
      case ColorPreset.remansos:
        return AppColors.primary;
      case ColorPreset.esmeralda:
        return const Color(0xFF064E3B);
      case ColorPreset.atardecer:
        return const Color(0xFF7C2D12);
      case ColorPreset.carbono:
        return const Color(0xFF111827);
    }
  }

  Color get secondary {
    switch (this) {
      case ColorPreset.remansos:
        return AppColors.secondary;
      case ColorPreset.esmeralda:
        return const Color(0xFF047857);
      case ColorPreset.atardecer:
        return const Color(0xFFC2410C);
      case ColorPreset.carbono:
        return const Color(0xFF374151);
    }
  }

  Color get accent {
    switch (this) {
      case ColorPreset.remansos:
        return AppColors.accent;
      case ColorPreset.esmeralda:
        return const Color(0xFF10B981);
      case ColorPreset.atardecer:
        return const Color(0xFFF97316);
      case ColorPreset.carbono:
        return const Color(0xFF0F172A);
    }
  }
}

enum TextSizePreset {
  compacto,
  normal,
  grande,
  extraGrande;

  String get storageValue => name;

  String get label {
    switch (this) {
      case TextSizePreset.compacto:
        return 'Compacto';
      case TextSizePreset.normal:
        return 'Normal';
      case TextSizePreset.grande:
        return 'Grande';
      case TextSizePreset.extraGrande:
        return 'Muy grande';
    }
  }

  double get scale {
    switch (this) {
      case TextSizePreset.compacto:
        return 0.94;
      case TextSizePreset.normal:
        return 1;
      case TextSizePreset.grande:
        return 1.12;
      case TextSizePreset.extraGrande:
        return 1.24;
    }
  }
}

enum LanguagePreset {
  esCo,
  en;

  String get storageValue => name;

  String get label {
    switch (this) {
      case LanguagePreset.esCo:
        return 'Español';
      case LanguagePreset.en:
        return 'English';
    }
  }

  Locale get locale {
    switch (this) {
      case LanguagePreset.esCo:
        return const Locale('es', 'CO');
      case LanguagePreset.en:
        return const Locale('en');
    }
  }
}

class AppSettingsProvider extends ChangeNotifier {
  static const String _colorKey = 'color_preset';
  static const String _textSizeKey = 'text_size_preset';
  static const String _languageKey = 'language_preset';
  static const String _highContrastKey = 'high_contrast';
  static const String _reduceMotionKey = 'reduce_motion';
  static const String _comfortableModeKey = 'comfortable_mode';

  ColorPreset _colorPreset = ColorPreset.remansos;
  TextSizePreset _textSizePreset = TextSizePreset.normal;
  LanguagePreset _languagePreset = LanguagePreset.esCo;
  bool _highContrast = false;
  bool _reduceMotion = false;
  bool _comfortableMode = true;
  bool _isLoading = true;

  ColorPreset get colorPreset => _colorPreset;
  TextSizePreset get textSizePreset => _textSizePreset;
  LanguagePreset get languagePreset => _languagePreset;
  bool get highContrast => _highContrast;
  bool get reduceMotion => _reduceMotion;
  bool get comfortableMode => _comfortableMode;
  bool get isLoading => _isLoading;

  double get textScaleFactor => _textSizePreset.scale;
  Locale get locale => _languagePreset.locale;

  ThemeData get theme => AppTheme.lightTheme(
    primary: _colorPreset.primary,
    secondary: _colorPreset.secondary,
    accent: _colorPreset.accent,
    highContrast: _highContrast,
    comfortableMode: _comfortableMode,
  );

  Future<void> load() async {
    final values = await Future.wait<String?>(<Future<String?>>[
      StorageService.readSetting(_colorKey),
      StorageService.readSetting(_textSizeKey),
      StorageService.readSetting(_languageKey),
      StorageService.readSetting(_highContrastKey),
      StorageService.readSetting(_reduceMotionKey),
      StorageService.readSetting(_comfortableModeKey),
    ]);

    _colorPreset = _parseEnum(values[0], ColorPreset.values, ColorPreset.remansos);
    _textSizePreset = _parseEnum(
      values[1],
      TextSizePreset.values,
      TextSizePreset.normal,
    );
    _languagePreset = _parseEnum(
      values[2],
      LanguagePreset.values,
      LanguagePreset.esCo,
    );
    _highContrast = values[3] == 'true';
    _reduceMotion = values[4] == 'true';
    _comfortableMode = values[5] != 'false';
    _isLoading = false;
    notifyListeners();
  }

  Future<void> setColorPreset(ColorPreset value) async {
    _colorPreset = value;
    notifyListeners();
    await StorageService.saveSetting(_colorKey, value.storageValue);
  }

  Future<void> setTextSizePreset(TextSizePreset value) async {
    _textSizePreset = value;
    notifyListeners();
    await StorageService.saveSetting(_textSizeKey, value.storageValue);
  }

  Future<void> setLanguagePreset(LanguagePreset value) async {
    _languagePreset = value;
    notifyListeners();
    await StorageService.saveSetting(_languageKey, value.storageValue);
  }

  Future<void> setHighContrast(bool value) async {
    _highContrast = value;
    notifyListeners();
    await StorageService.saveSetting(_highContrastKey, value.toString());
  }

  Future<void> setReduceMotion(bool value) async {
    _reduceMotion = value;
    notifyListeners();
    await StorageService.saveSetting(_reduceMotionKey, value.toString());
  }

  Future<void> setComfortableMode(bool value) async {
    _comfortableMode = value;
    notifyListeners();
    await StorageService.saveSetting(_comfortableModeKey, value.toString());
  }

  Future<void> reset() async {
    _colorPreset = ColorPreset.remansos;
    _textSizePreset = TextSizePreset.normal;
    _languagePreset = LanguagePreset.esCo;
    _highContrast = false;
    _reduceMotion = false;
    _comfortableMode = true;
    notifyListeners();
    await Future.wait(<Future<void>>[
      StorageService.deleteSetting(_colorKey),
      StorageService.deleteSetting(_textSizeKey),
      StorageService.deleteSetting(_languageKey),
      StorageService.deleteSetting(_highContrastKey),
      StorageService.deleteSetting(_reduceMotionKey),
      StorageService.deleteSetting(_comfortableModeKey),
    ]);
  }

  T _parseEnum<T extends Enum>(String? rawValue, List<T> values, T fallback) {
    if (rawValue == null || rawValue.isEmpty) {
      return fallback;
    }
    for (final value in values) {
      if (value.name == rawValue) {
        return value;
      }
    }
    return fallback;
  }
}
