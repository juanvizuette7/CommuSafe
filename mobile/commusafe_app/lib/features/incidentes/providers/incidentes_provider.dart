import 'package:flutter/foundation.dart';

import '../models/incidente_model.dart';

class IncidentesProvider extends ChangeNotifier {
  bool _loading = false;
  final List<IncidenteModel> _incidentes = <IncidenteModel>[];

  bool get loading => _loading;
  List<IncidenteModel> get incidentes => List<IncidenteModel>.unmodifiable(_incidentes);

  void setLoading(bool value) {
    _loading = value;
    notifyListeners();
  }

  void replaceAll(List<IncidenteModel> nuevosIncidentes) {
    _incidentes
      ..clear()
      ..addAll(nuevosIncidentes);
    notifyListeners();
  }

  void reset() {
    _loading = false;
    _incidentes.clear();
    notifyListeners();
  }
}
