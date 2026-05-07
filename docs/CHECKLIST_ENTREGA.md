# Checklist de Entrega CommuSafe

Este documento resume el cumplimiento funcional y no funcional del sistema CommuSafe para la sustentación del trabajo de grado.

## Requerimientos funcionales

| Código | Requerimiento | Estado | Evidencia verificable |
| --- | --- | --- | --- |
| RF-01 | Registro de usuarios por administrador | Cumplido | Panel web `Usuarios`, API `/api/auth/usuarios/`, formularios de creación y edición. |
| RF-02 | Autenticación con email y contraseña | Cumplido | Login JWT en `/api/auth/login/`, login web y login móvil. |
| RF-03 | Registro de incidentes con categoría, descripción, ubicación y evidencia | Cumplido | API `/api/incidentes/`, app Flutter en `Crear incidente`, soporte multipart. |
| RF-04 | Clasificación automática de prioridad por categoría | Cumplido | Método `save()` del modelo `Incidente` y pruebas parametrizadas backend. |
| RF-05 | Seguimiento de incidentes con cambio de estado y comentario | Cumplido | Acción `cambiar_estado`, historial inmutable y timeline en panel/app. |
| RF-06 | Notificaciones segmentadas por rol | Cumplido | Servicio `notificaciones/services.py`, bandeja de notificaciones y avisos por audiencia. |
| RF-07 | Gestión de usuarios por administrador | Cumplido | Panel web con crear, editar, cambiar rol, activar/desactivar y eliminar. |
| RF-08 | Historial de incidentes con filtros | Cumplido | Listado web con filtros, búsqueda, ordenamiento y exportación Excel/PDF. |
| RF-09 | Asistente virtual con IA para consultas frecuentes | Cumplido | Endpoint `/api/asistente/chat/`, proveedor Gemini o fallback local controlado. |
| RF-10 | Acceso directo a contactos de emergencia | Cumplido | Pantalla Flutter `Emergencias` con llamadas `tel:`. |
| RF-11 | Adjuntar evidencia fotográfica hasta 3 imágenes | Cumplido | Validación en serializer y selector de cámara/galería en Flutter. |
| RF-12 | Avisos administrativos a residentes, vigilantes o usuarios específicos | Cumplido | Módulo de avisos con selección de audiencia y banner móvil de avisos vigentes. |

## Requerimientos no funcionales

| Código | Requerimiento | Estado | Evidencia verificable |
| --- | --- | --- | --- |
| RNF-01 | Interfaz intuitiva con flujos cortos | Cumplido | App móvil por pestañas, panel web con navegación lateral, formularios directos. |
| RNF-02 | Respuesta en tiempos aceptables | Cumplido para operación esperada | Endpoints paginados, filtros en base de datos, Render con Gunicorn gthread. |
| RNF-03 | Seguridad con HTTPS, JWT y roles | Cumplido | Render HTTPS, SimpleJWT, permisos por rol y `settings_prod.py` con cookies seguras. |
| RNF-04 | Disponibilidad durante operación del conjunto | Cumplido en despliegue académico | Servicio Render activo y health check `/health/`. |
| RNF-05 | Arquitectura modular y escalable | Cumplido | Apps Django por dominio y Flutter por features. |
| RNF-06 | Compatibilidad Android 8.0+ | Cumplido | Proyecto Flutter Android con `minSdk` compatible y APK generado. |
| RNF-07 | Código organizado con patrones reconocidos | Cumplido | ViewSets, serializers, providers, services, models y separación frontend/backend/mobile. |

## Evidencia técnica

- Backend Django organizado por apps: `usuarios`, `incidentes`, `notificaciones`, `asistente` y `panel_web`.
- API REST protegida con JWT y permisos por rol.
- Modelo de usuario personalizado basado en email.
- Ciclo de vida completo de incidentes con prioridad automática.
- Historial de cambios de estado y trazabilidad de eliminación.
- Notificaciones internas, avisos segmentados y preparación para push real con Firebase.
- Panel web administrativo con Django Templates, Tailwind CSS y Alpine.js.
- App Flutter organizada por features y providers.
- Pruebas automatizadas backend en `backend/tests/test_sistema_completo.py`.
- Pruebas Flutter en `mobile/commusafe_app/test/` e integración móvil en `mobile/commusafe_app/integration_test/`.
- Despliegue en Render con PostgreSQL y HTTPS.
- Documentación técnica completa en `docs/`.

## Comandos de verificación

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest -q
```

Flutter:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat analyze
C:\Users\juanv\flutter\bin\flutter.bat test
C:\Users\juanv\flutter\bin\flutter.bat build apk --debug
```

Producción:

```powershell
curl.exe -i https://commusafe.onrender.com/health/
```

## Estado de entrega

CommuSafe se encuentra listo para sustentación académica como sistema funcional desplegado, con backend, panel web, aplicación móvil Android, documentación, pruebas y trazabilidad metodológica bajo el Modelo de Desarrollo Incremental.
