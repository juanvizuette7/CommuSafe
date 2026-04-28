import 'package:go_router/go_router.dart';

class AppNavigationService {
  AppNavigationService._();

  static GoRouter? _router;
  static String? _pendingIncidentId;

  static void setRouter(GoRouter router) {
    _router = router;
    final incidentePendiente = _pendingIncidentId;
    if (incidentePendiente != null) {
      _pendingIncidentId = null;
      abrirIncidente(incidentePendiente);
    }
  }

  static void abrirIncidente(String incidenteId) {
    final id = incidenteId.trim();
    if (id.isEmpty) {
      return;
    }
    final router = _router;
    if (router == null) {
      _pendingIncidentId = id;
      return;
    }
    router.go('/incidentes/$id');
  }
}
