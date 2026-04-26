# CommuSafe

CommuSafe es una plataforma integral de gestion de seguridad y organizacion comunitaria para el conjunto residencial Remansos del Norte. El sistema integra backend Django REST, panel web administrativo y aplicacion movil Flutter para residentes, vigilantes y administradores.

## Modelo de desarrollo

El proyecto se desarrolla bajo el modelo incremental.

Esto significa que CommuSafe se construye por incrementos funcionales acumulativos. Cada sprint entrega una parte real del sistema, integrada con las funcionalidades anteriores y lista para ser verificada antes de avanzar al siguiente modulo.

La ruta incremental del proyecto es:

- Sprint 0: arquitectura, documentacion base, modelo de datos y diseno visual.
- Sprint 1: backend Django, usuario personalizado y autenticacion JWT.
- Sprint 2: modulo central de incidentes en backend.
- Sprint 3: notificaciones push y asistente virtual con IA.
- Sprint 4: panel web administrativo.
- Sprint 5: estructura base de la app Flutter.
- Sprint 6: autenticacion y perfil en Flutter.
- Sprint 7: lista, creacion y detalle de incidentes en Flutter.
- Sprint 8: notificaciones, chat IA y contactos de emergencia en Flutter.
- Sprint 9: pruebas, datos demo y preparacion de sustentacion.
- Sprint 10: despliegue, README final y checklist de entrega.

El detalle metodologico esta documentado en `docs/MODELO_INCREMENTAL.md`.

## Estructura principal

- `backend/`: API REST Django, reglas de negocio y panel administrativo.
- `frontend/`: plantillas y estaticos del panel web.
- `mobile/`: aplicacion Flutter Android.
- `docs/`: documentacion tecnica, arquitectura, modelo de datos y plan de desarrollo.
