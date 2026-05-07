# Matriz de Cumplimiento del Proyecto CommuSafe

Esta matriz conecta objetivos específicos, requerimientos, módulos implementados y evidencia demostrable. Su propósito es facilitar la sustentación y evitar afirmaciones sin soporte técnico.

## 1. Correspondencia entre objetivos e implementación

| Objetivo específico | Implementación en CommuSafe | Evidencia |
| --- | --- | --- |
| OE1: Analizar necesidades y definir requerimientos funcionales y no funcionales. | Arquitectura, modelo de datos, diseño visual, plan de desarrollo y metodología incremental documentados. | `docs/ARQUITECTURA.md`, `docs/MODELO_DATOS.md`, `docs/DISENO.md`, `docs/PLAN_DESARROLLO.md`, `docs/MODELO_INCREMENTAL.md`. |
| OE2: Diseñar y desarrollar la plataforma para registrar, organizar y dar seguimiento a incidentes. | Backend de incidentes, app móvil para reporte, panel web para gestión, historial y exportaciones. | `backend/incidentes/`, `mobile/commusafe_app/lib/features/incidentes/`, `frontend/templates/panel/incidentes_lista.html`. |
| OE3: Integrar asistente virtual con IA para consultas frecuentes. | Endpoint de chat con Gemini o fallback local, pantalla CommuBot en Flutter y health check del proveedor. | `backend/asistente/`, `mobile/commusafe_app/lib/features/asistente/`, `/api/asistente/health/`. |
| OE4: Evaluar el sistema mediante pruebas y atributos de calidad. | Suite pytest, pruebas Flutter, comandos de análisis, build APK, checklist y plan de calidad. | `backend/tests/test_sistema_completo.py`, `mobile/commusafe_app/test/`, `docs/PLAN_PRUEBAS_CALIDAD.md`. |

## 2. Correspondencia entre incrementos y entregables

| Incremento | Entregable académico | Entregable técnico |
| --- | --- | --- |
| 1. Núcleo y autenticación | Sistema base con roles y acceso seguro. | Django configurado, usuario personalizado, JWT, login web, login móvil y perfil. |
| 2. Gestión de incidentes | Reporte, consulta y seguimiento de incidentes. | Modelos, serializers, ViewSet, pantallas Flutter, evidencias e historial. |
| 3. Panel y notificaciones | Operación administrativa y comunicación segmentada. | Panel web, dashboard, filtros, usuarios, avisos, notificaciones internas y FCM. |
| 4. IA y emergencias | Orientación automatizada y acceso rápido a ayuda. | Chat IA/fallback, health check, pantalla CommuBot y contactos de emergencia. |
| 5. Calidad y despliegue | Sistema validado, documentado y publicado. | Pytest, Flutter tests, APK, Render, PostgreSQL, README y documentación final. |

## 3. Módulos y responsabilidades

| Módulo | Responsabilidad | Usuarios impactados |
| --- | --- | --- |
| `usuarios` | Autenticación, roles, perfil, FCM token y recuperación de contraseña. | Residentes, vigilantes y administradores. |
| `incidentes` | Registro, prioridad automática, evidencias, historial, eliminación trazable y exportación. | Residentes, vigilantes y administradores. |
| `notificaciones` | Notificaciones internas, push, avisos administrativos y conteo de no leídas. | Residentes, vigilantes y administradores. |
| `asistente` | Chat IA con contexto limitado al conjunto y fallback local. | Principalmente residentes. |
| `panel_web` | Panel administrativo y operativo para gestión web. | Administradores y vigilantes. |
| Flutter app | Experiencia móvil de incidentes, notificaciones, perfil, chat y emergencias. | Residentes, vigilantes y administradores. |

## 4. Evidencia que debe mostrarse en sustentación

1. Abrir `https://commusafe.onrender.com/health/` y mostrar respuesta correcta.
2. Abrir `https://commusafe.onrender.com/login/` y entrar al panel como administrador.
3. Mostrar dashboard, lista de incidentes, detalle, timeline y exportación.
4. Mostrar gestión de usuarios y diferenciación de roles.
5. Abrir la app Android instalada y entrar como residente.
6. Crear un incidente con categoría, ubicación y evidencia.
7. Entrar como vigilante y cambiar el estado del incidente.
8. Ver la notificación generada.
9. Abrir CommuBot y hacer una consulta frecuente.
10. Ejecutar o mostrar resultado de `pytest -q`.

## 5. Riesgos controlados

| Riesgo | Control aplicado |
| --- | --- |
| Acceso indebido a datos de residentes | Permisos por rol en API y filtros de queryset según usuario autenticado. |
| Pérdida de trazabilidad en incidentes | Historial de estados e incidente eliminado con motivo y responsable. |
| Fallo de proveedor IA | Fallback local para consultas frecuentes. |
| Credenciales expuestas | `.gitignore`, variables de entorno en Render y archivos sensibles fuera del repositorio. |
| Diferencias entre desarrollo y producción | `settings.py` para desarrollo, `settings_prod.py` para Render y PostgreSQL. |

## 6. Conclusión de cumplimiento

El proyecto cumple el alcance obligatorio y las funcionalidades deseables principales. Las mejoras futuras identificadas, como votaciones de asamblea, reportes estadísticos avanzados e integración con control de acceso físico, quedan documentadas como evolución posterior y no afectan el cumplimiento del núcleo funcional definido para CommuSafe.
