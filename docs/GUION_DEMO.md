# Guion de Demostración CommuSafe

Este guion organiza la presentación del sistema CommuSafe ante el jurado evaluador. El objetivo es demostrar el cumplimiento funcional, la arquitectura incremental y la integración entre backend, panel web y aplicación móvil.

## 1. Inicio del Sistema

### Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py cargar_demo
python manage.py runserver
```

URL del backend:

```text
http://127.0.0.1:8000
```

URL del panel web:

```text
http://127.0.0.1:8000/login/
```

### Aplicación Flutter

En otra terminal:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat run
```

Si Flutter está en el PATH:

```bash
cd mobile/commusafe_app
flutter run
```

## 2. Datos de Acceso

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@remansos.com` | `Admin2026*` |
| Vigilante | `vigilante1@remansos.com` | `Commu2026*` |
| Vigilante | `vigilante2@remansos.com` | `Commu2026*` |
| Residente | `residente1@remansos.com` | `Commu2026*` |
| Residente | `residente2@remansos.com` | `Commu2026*` |

## 3. Flujo del Residente en la App

1. Abrir la app móvil CommuSafe.
2. Iniciar sesión con `residente1@remansos.com` y `Commu2026*`.
3. Verificar que la lista de incidentes muestra únicamente los reportes propios del residente.
4. Revisar la tarjeta de un incidente y explicar los badges de categoría, prioridad y estado.
5. Entrar al detalle de un incidente para mostrar descripción, ubicación, evidencias e historial.
6. Crear un nuevo incidente desde el botón flotante.
7. Seleccionar categoría, escribir título, descripción y ubicación.
8. Adjuntar una evidencia fotográfica desde cámara o galería.
9. Enviar el reporte y mostrar que aparece en el listado.
10. Abrir el chat CommuBot y preguntar: `¿Cómo reporto un incidente?`.
11. Mostrar la respuesta del asistente virtual con fallback local o IA configurada.
12. Abrir la pantalla de contactos de emergencia y explicar el acceso rápido a llamadas.

## 4. Flujo del Vigilante en la App

1. Cerrar sesión como residente.
2. Iniciar sesión con `vigilante1@remansos.com` y `Commu2026*`.
3. Verificar que el vigilante puede ver todos los incidentes del conjunto.
4. Abrir un incidente en estado `REGISTRADO`.
5. Ir a la sección `Actualizar Estado`.
6. Cambiar el estado a `EN_PROCESO` con un comentario operativo.
7. Confirmar la actualización.
8. Mostrar que el historial del incidente registra usuario, fecha, estado anterior, estado nuevo y comentario.
9. Ir a notificaciones y explicar el conteo de alertas no leídas.
10. Crear un aviso comunitario desde la app para residentes, si se desea demostrar la gestión móvil de avisos.

## 5. Flujo del Administrador en el Panel Web

1. Abrir `http://127.0.0.1:8000/login/`.
2. Iniciar sesión con `admin@remansos.com` y `Admin2026*`.
3. Mostrar el dashboard con métricas:
4. Total de incidentes activos.
5. Incidentes de prioridad alta.
6. Incidentes resueltos hoy.
7. Usuarios activos.
8. Abrir la lista de incidentes.
9. Aplicar filtros por categoría, estado y prioridad.
10. Abrir el detalle de un incidente.
11. Mostrar la información del reportante, estado actual, evidencias y timeline de historial.
12. Cambiar estado desde el panel con comentario.
13. Verificar mensaje de éxito y creación de notificación.
14. Abrir la lista de usuarios.
15. Mostrar roles diferenciados por color y botón de activar/desactivar cuenta.
16. Abrir la sección de avisos.
17. Enviar un aviso informativo o de emergencia a una audiencia segmentada.

## 6. Puntos Clave para Explicar al Jurado

- El sistema aplica el modelo incremental: cada sprint agrega una capacidad real y verificable.
- La arquitectura es modular: backend por apps Django, panel web separado en `frontend/`, app Flutter por features.
- La seguridad usa JWT, roles y permisos por endpoint.
- Los residentes solo ven sus propios incidentes; vigilantes y administradores ven todos.
- La prioridad del incidente no depende del usuario, se calcula automáticamente por regla de negocio.
- Cada cambio de estado queda registrado en un historial inmutable.
- Las notificaciones se generan automáticamente por eventos del dominio y también mediante avisos manuales.
- El asistente virtual responde preguntas frecuentes del conjunto y funciona con fallback si no hay API key.
- La app móvil cubre incidentes, notificaciones, IA, perfil y contactos de emergencia.
- El panel web entrega una vista operativa para administración y vigilancia.

## 7. Objetivos Específicos Demostrados

- Digitalizar el reporte de incidentes comunitarios.
- Mejorar la trazabilidad de la atención de incidentes.
- Reducir dependencia de reportes informales por mensajería o llamadas.
- Permitir gestión diferenciada por rol.
- Ofrecer alertas y avisos segmentados.
- Integrar un asistente virtual para orientación básica.
- Presentar una solución escalable y mantenible con arquitectura modular.

## 8. Cierre de la Demostración

1. Mostrar el APK generado en `mobile/commusafe_app/build/app/outputs/flutter-apk/app-release.apk`.
2. Mostrar la suite de pruebas ejecutada con `pytest` y `flutter test`.
3. Mostrar `docs/CHECKLIST_ENTREGA.md`.
4. Concluir que CommuSafe está listo para uso piloto en Remansos del Norte.
