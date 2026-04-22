import 'package:flutter/foundation.dart';

import '../models/notificacion_model.dart';

class NotificacionesProvider extends ChangeNotifier {
  bool _loading = false;
  int _noLeidasCount = 0;
  final List<NotificacionModel> _items = <NotificacionModel>[];

  bool get loading => _loading;
  int get noLeidasCount => _noLeidasCount;
  List<NotificacionModel> get items => List<NotificacionModel>.unmodifiable(_items);

  void setLoading(bool value) {
    _loading = value;
    notifyListeners();
  }

  void setNoLeidasCount(int value) {
    _noLeidasCount = value;
    notifyListeners();
  }

  void replaceAll(List<NotificacionModel> notifications) {
    _items
      ..clear()
      ..addAll(notifications);
    _noLeidasCount = notifications.where((item) => !item.leida).length;
    notifyListeners();
  }

  void markAllAsRead() {
    final updated = _items
        .map(
          (item) => NotificacionModel(
            id: item.id,
            titulo: item.titulo,
            cuerpo: item.cuerpo,
            tipo: item.tipo,
            leida: true,
            fechaEnvio: item.fechaEnvio,
            tituloIncidente: item.tituloIncidente,
          ),
        )
        .toList();
    replaceAll(updated);
  }

  void reset() {
    _loading = false;
    _noLeidasCount = 0;
    _items.clear();
    notifyListeners();
  }
}
