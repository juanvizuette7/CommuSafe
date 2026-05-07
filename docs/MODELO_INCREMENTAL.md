# Modelo de Desarrollo Incremental de CommuSafe

## 1. Enfoque metodológico

CommuSafe se desarrolló bajo el Modelo de Desarrollo Incremental. El sistema no se construyó como una única entrega monolítica, sino mediante entregas parciales, funcionales e integradas. Cada incremento agregó capacidades verificables sobre una base existente: primero autenticación y roles, luego gestión de incidentes, después panel web, notificaciones, aplicación móvil, asistente virtual, pruebas y despliegue.

La planeación técnica se organizó en sprints numerados del Sprint 0 al Sprint 10. La memoria metodológica del proyecto agrupa esos sprints en cinco incrementos académicos. No existe contradicción entre ambos niveles: el sprint es la unidad operativa de construcción y el incremento es la unidad funcional usada para explicar el avance ante el jurado.

## 2. Relación entre incrementos académicos y sprints técnicos

| Incremento académico | Sprints técnicos relacionados | Entrega funcional verificable |
| --- | --- | --- |
| Incremento 1: Núcleo del sistema y autenticación | Sprint 0, Sprint 1, Sprint 5, Sprint 6 | Arquitectura documentada, backend Django configurado, usuario personalizado, autenticación JWT, app Flutter base, login móvil y perfil. |
| Incremento 2: Gestión de incidentes | Sprint 2, Sprint 7 | Modelo de incidentes, evidencias, historial de estados, API REST, listado móvil, creación de incidentes, detalle e historial. |
| Incremento 3: Panel web y notificaciones | Sprint 3, Sprint 4, parte del Sprint 8 | Notificaciones internas y push, avisos administrativos, panel web con dashboard, filtros, usuarios, detalle de incidentes y gestión por rol. |
| Incremento 4: Asistente virtual con IA y emergencias | Sprint 3, Sprint 8 | Backend del asistente, integración con Gemini o fallback local, chat móvil, contactos de emergencia y acceso rápido a llamadas. |
| Incremento 5: Pruebas, despliegue y documentación final | Sprint 9, Sprint 10 y refinamientos posteriores | Suite de pruebas backend, pruebas Flutter, APK, PostgreSQL en producción, Render con HTTPS, README, checklist, guion de demo y documentación técnica. |

## 3. Justificación del modelo para CommuSafe

El modelo incremental se ajusta al proyecto por cuatro razones principales:

- Equipo reducido: permite dividir el trabajo en entregas controladas sin una estructura pesada de gestión.
- Arquitectura modular: Django está separado por apps de dominio y Flutter por features, lo que permite construir módulos independientes e integrarlos progresivamente.
- Requerimientos ajustables: el contexto real del conjunto residencial permite refinar detalles de operación, avisos, notificaciones y presentación visual durante el desarrollo.
- Evaluación académica: cada incremento produce evidencia demostrable, como código funcional, pruebas ejecutables, documentación y despliegue.

## 4. Cierre verificable de cada incremento

| Incremento | Criterio de cierre aplicado | Evidencia en el repositorio |
| --- | --- | --- |
| 1. Núcleo y autenticación | El sistema permite iniciar sesión por rol y proteger rutas mediante JWT. | `backend/usuarios/`, `mobile/commusafe_app/lib/features/auth/`, pruebas de autenticación en `backend/tests/test_sistema_completo.py`. |
| 2. Incidentes | El ciclo registrar, consultar, cambiar estado y cerrar incidente funciona con historial. | `backend/incidentes/`, `mobile/commusafe_app/lib/features/incidentes/`, serializers, viewsets y pruebas de lógica de negocio. |
| 3. Panel y notificaciones | Administrador y vigilante gestionan incidentes y reciben notificaciones o avisos. | `backend/panel_web/`, `frontend/templates/panel/`, `backend/notificaciones/`. |
| 4. IA y emergencias | El residente puede consultar el asistente y acceder a contactos de emergencia. | `backend/asistente/`, `mobile/commusafe_app/lib/features/asistente/`, `mobile/commusafe_app/lib/features/emergencias/`. |
| 5. Calidad y despliegue | El sistema está probado, documentado y publicado con base de datos de producción. | `render.yaml`, `backend/commusafe_backend/settings_prod.py`, `docs/`, `README.md`, `backend/tests/`. |

## 5. Evidencia del crecimiento incremental

La evolución incremental puede demostrarse con el historial de Git y con la estructura actual del sistema:

- Sprint 0 dejó arquitectura, modelo de datos, diseño visual y plan de desarrollo.
- Sprint 1 habilitó Django, usuarios, permisos y autenticación JWT.
- Sprint 2 agregó la regla de negocio central: incidentes, prioridad automática, evidencias e historial.
- Sprint 3 incorporó notificaciones y asistente virtual.
- Sprint 4 construyó el panel web administrativo.
- Sprint 5 preparó la arquitectura móvil.
- Sprint 6 integró autenticación y perfil en Flutter.
- Sprint 7 agregó gestión móvil de incidentes.
- Sprint 8 completó notificaciones, chat IA y emergencias.
- Sprint 9 consolidó pruebas, datos de verificación y refinamiento.
- Sprint 10 preparó despliegue, documentación final y checklist.

## 6. Cómo defenderlo ante el jurado

La explicación recomendada es:

> CommuSafe se construyó con un enfoque incremental. Para la gestión técnica se usaron sprints pequeños del 0 al 10, pero para la memoria metodológica esos sprints se agrupan en cinco incrementos funcionales: autenticación, incidentes, panel y notificaciones, asistente IA, y cierre de calidad/despliegue. Cada incremento dejó una versión ejecutable y verificable del sistema, integrada con lo construido previamente.

Esta explicación evita presentar los sprints como si fueran una metodología diferente y mantiene coherencia con el capítulo metodológico del trabajo.

## 7. Conclusión

CommuSafe cumple el Modelo de Desarrollo Incremental porque el producto creció mediante entregas funcionales acumulativas, cada módulo se integró con los anteriores y el cierre del proyecto cuenta con evidencia verificable de implementación, pruebas, documentación y despliegue.
