import 'package:flutter/widgets.dart';

class AppLocalizations {
  const AppLocalizations(this.locale);

  final Locale locale;

  static AppLocalizations of(BuildContext context) {
    return AppLocalizations(Localizations.localeOf(context));
  }

  bool get isEnglish => locale.languageCode.toLowerCase() == 'en';

  String tr(String spanish, String english) {
    return isEnglish ? english : spanish;
  }
}
