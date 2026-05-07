# Plan de Pruebas y Evaluación de Calidad

Este plan organiza las pruebas de CommuSafe con base en los atributos relevantes del estándar ISO/IEC 25010: funcionalidad, usabilidad, confiabilidad, seguridad, eficiencia y mantenibilidad.

## 1. Alcance

El plan cubre:

- Backend Django REST API.
- Panel web administrativo.
- Aplicación móvil Flutter Android.
- Base de datos PostgreSQL en producción.
- Integración con IA y notificaciones.
- Flujos completos por rol: residente, vigilante y administrador.

## 2. Pruebas automatizadas backend

Archivo principal:

```text
backend/tests/test_sistema_completo.py
```

Cobertura funcional:

- Login correcto e incorrecto.
- Refresh token.
- Rechazo de endpoints protegidos sin token.
- Control de acceso por rol.
- Visibilidad de incidentes según usuario.
- Eliminación restringida a administrador.
- Cálculo automático de prioridad.
- Creación de historial al cambiar estado.
- Límite de tres evidencias.
- Notificaciones por prioridad.
- Respuesta del asistente dentro del dominio.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Con cobertura:

```powershell
cd backend
.\.venv\Scripts\python.exe -m coverage run -m pytest -q
.\.venv\Scripts\python.exe -m coverage report
```

## 3. Pruebas Flutter

Pruebas disponibles:

- `mobile/commusafe_app/test/widget_test.dart`: renderizado base del login.
- `mobile/commusafe_app/integration_test/auth_flow_test.dart`: flujo de login, perfil y logout.
- `mobile/commusafe_app/integration_test/incidentes_flow_test.dart`: creación de incidente y cambio de estado.

Comandos:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat analyze
C:\Users\juanv\flutter\bin\flutter.bat test
C:\Users\juanv\flutter\bin\flutter.bat build apk --debug
```

Para pruebas de integración con emulador o celular conectado:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat test integration_test
```

## 4. Pruebas manuales por rol

| Rol | Flujo | Resultado esperado |
| --- | --- | --- |
| Residente | Login, ver incidentes propios, crear incidente con evidencia. | El incidente queda registrado con prioridad automática y aparece en su lista. |
| Vigilante | Login, ver todos los incidentes, cambiar estado. | Se actualiza el estado, se crea historial y se notifica al residente. |
| Administrador | Login panel web, gestionar usuarios, filtrar incidentes y exportar historial. | El panel permite operación completa con mensajes de éxito. |

## 5. Atributos de calidad evaluados

| Atributo | Criterio de validación | Instrumento |
| --- | --- | --- |
| Funcionalidad | Los flujos principales ejecutan sin errores críticos. | Pytest, pruebas Flutter y guion manual. |
| Seguridad | Cada rol accede únicamente a datos y acciones autorizadas. | Pruebas de control de acceso y revisión de permisos. |
| Confiabilidad | Los cambios de estado y eliminaciones quedan trazados. | Revisión de tablas `HistorialEstado` e `IncidenteEliminado`. |
| Usabilidad | Usuarios representativos completan tareas básicas sin asistencia excesiva. | Instrumento de usabilidad en `docs/INSTRUMENTO_USABILIDAD.md`. |
| Eficiencia | Endpoints frecuentes responden en tiempos aceptables para el contexto académico. | Medición con navegador, consola o herramientas de carga básica. |
| Mantenibilidad | Código separado por capas y módulos. | Revisión de estructura del repositorio y documentación técnica. |

## 6. Checklist de regresión antes de sustentar

1. `python manage.py check` no reporta errores.
2. `pytest -q` pasa sin fallos.
3. `flutter analyze` no reporta errores.
4. `flutter test` pasa.
5. `flutter build apk --debug` genera APK.
6. Render responde en `/health/`.
7. Panel web permite login de administrador.
8. App móvil permite login de residente.
9. Se puede crear un incidente desde la app.
10. Se puede cambiar estado desde panel o app vigilante.
11. Se genera notificación.
12. CommuBot responde con IA real o fallback controlado.

## 7. Registro de evidencia recomendado

Para la entrega final se recomienda guardar capturas o resultados de consola de:

- Salida de `pytest -q`.
- Salida de `flutter analyze`.
- Salida de `flutter test`.
- APK generado.
- Panel web en producción.
- App móvil ejecutándose en celular.
- Tabla de incidentes en PostgreSQL.
- Respuesta de `/api/asistente/health/`.

Esto permite demostrar ante el jurado que la evaluación de calidad no fue solo declarativa, sino verificable.
