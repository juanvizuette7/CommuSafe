# Checklist de Entrega CommuSafe

Este documento verifica el cumplimiento funcional y no funcional del sistema CommuSafe para la sustentación del trabajo de grado.

## Requerimientos Funcionales

- ✅ RF-01: Registro de usuarios por administrador.
- ✅ RF-02: Autenticación con email y contraseña.
- ✅ RF-03: Registro de incidentes con categoría, descripción, ubicación y evidencia.
- ✅ RF-04: Clasificación automática de prioridad por categoría.
- ✅ RF-05: Seguimiento de incidentes con cambio de estado y comentario.
- ✅ RF-06: Notificaciones en tiempo real segmentadas por rol.
- ✅ RF-07: Gestión de usuarios por administrador.
- ✅ RF-08: Historial de incidentes con filtros.
- ✅ RF-09: Asistente virtual con IA para consultas frecuentes.
- ✅ RF-10: Acceso directo a contactos de emergencia.
- ✅ RF-11: Adjuntar evidencia fotográfica hasta 3 imágenes.
- ✅ RF-12: Avisos administrativos a todos los residentes.

## Requerimientos No Funcionales

- ✅ RNF-01: Interfaz intuitiva con flujos en máximo 3 pasos.
- ✅ RNF-02: Respuesta del sistema en menos de 3 segundos en operación local.
- ✅ RNF-03: Seguridad con HTTPS en producción, JWT y roles de acceso.
- ✅ RNF-04: Disponibilidad durante horas de operación del conjunto.
- ✅ RNF-05: Arquitectura modular y escalable.
- ✅ RNF-06: Compatibilidad con Android 8.0+.
- ✅ RNF-07: Código organizado con patrones reconocidos.

## Evidencia Técnica

- ✅ Backend Django organizado por apps de dominio.
- ✅ API REST protegida con JWT.
- ✅ Modelo de usuario personalizado basado en email.
- ✅ Ciclo de vida completo de incidentes.
- ✅ Historial inmutable de cambios de estado.
- ✅ Notificaciones internas y preparación para FCM.
- ✅ Panel web administrativo con Tailwind CSS y Alpine.js.
- ✅ App Flutter organizada por features.
- ✅ Pruebas automatizadas con pytest, coverage, widget tests e integration tests.
- ✅ Datos demo reproducibles mediante `python manage.py cargar_demo`.
- ✅ APK Android generado correctamente.

## Estado de Presentación

- ✅ Documentación técnica completa en `docs/`.
- ✅ README final con instalación, pruebas, endpoints y credenciales.
- ✅ Guion de demostración paso a paso.
- ✅ Configuración de producción con PostgreSQL.
- ✅ Procfile para despliegue en Render o Railway.
- ✅ Sistema listo para ejecución local ante jurado.
