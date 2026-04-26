# Arquitectura del Sistema CommuSafe

## 1. Propósito del sistema

CommuSafe es una plataforma hiperlocal de gestión de seguridad y organización comunitaria para el conjunto residencial Remansos del Norte. Su objetivo es centralizar el reporte, atención, seguimiento y cierre de incidentes, mejorar la coordinación entre residentes y personal de vigilancia, y ofrecer a la administración un panel de control con trazabilidad completa.

El sistema se compone de tres superficies principales:

- Backend API y panel web en Django.
- Aplicación móvil Android en Flutter.
- Servicios externos para inteligencia artificial y notificaciones push.

## 2. Principios arquitectónicos

- Arquitectura modular por dominios de negocio.
- API REST versionada para desacoplar backend y cliente móvil.
- Control de acceso basado en roles: residente, vigilante y administrador.
- Trazabilidad completa del ciclo de vida de cada incidente.
- Persistencia simple en desarrollo con SQLite y preparada para PostgreSQL en producción.
- Separación clara entre lógica de dominio, presentación web, API y servicios externos.
- Diseño evolutivo: el sistema inicia con una base monolítica bien organizada, lista para crecer sin una migración traumática a microservicios.
- Desarrollo incremental: cada sprint agrega un incremento funcional integrado con los modulos anteriores, de modo que el sistema crece por versiones acumulativas y verificables.

## 3. Componentes del sistema

### 3.1 Backend Django

Ubicación: `commusafe/backend/`

Responsabilidades:

- Exponer la API REST consumida por la app móvil.
- Renderizar el panel web administrativo con Django Templates.
- Gestionar autenticación JWT con SimpleJWT.
- Aplicar reglas de negocio de incidentes, prioridades y estados.
- Registrar historial inmutable de cambios.
- Generar notificaciones internas y coordinar envíos push por FCM.
- Integrarse con Anthropic Claude Haiku para el asistente virtual.

### 3.2 Aplicación móvil Flutter

Ubicación: `commusafe/mobile/`

Responsabilidades:

- Autenticación de usuarios.
- Registro de incidentes por residentes, con evidencia fotográfica.
- Consulta de incidentes y notificaciones.
- Atención operativa de incidentes por vigilantes.
- Interacción con el asistente virtual.
- Visualización de contactos de emergencia y estado del conjunto.

### 3.3 Panel web administrativo

Tecnología: Django Templates + Tailwind CSS por CDN + Alpine.js

Responsabilidades:

- Gestión de usuarios por rol.
- Vista centralizada de incidentes.
- Métricas operativas y tablero de control.
- Reasignación, cierre y auditoría de incidentes.
- Gestión de configuración institucional y contenido de ayuda.

### 3.4 Servicios externos

- Anthropic Claude API:
  - Responde preguntas frecuentes de residentes.
  - Opera sobre una base controlada de contexto definida por el proyecto.
  - Nunca modifica incidentes ni ejecuta acciones críticas; solo informa y orienta.

- Firebase Cloud Messaging:
  - Envía notificaciones push a la app móvil.
  - Se activa en eventos como creación, asignación, atención, cambio de estado y cierre de incidentes.

## 4. Vista de alto nivel

```text
Residente/Vigilante -> App Flutter -> API REST Django -> Base de Datos
                                            |               |
                                            |               -> Historial / Notificaciones
                                            |
                                            -> FCM -> Push móvil
                                            |
                                            -> Anthropic Claude -> Respuesta asistente

Administrador -> Panel Web Django -> Servicios de dominio Django -> Base de Datos
```

## 5. Estructura lógica del backend

El backend se organizará como un monolito modular con las siguientes apps de Django:

### 5.1 `core`

Responsabilidad:

- Configuración global.
- Clases base compartidas.
- Utilidades comunes.
- Health checks.
- Mixins, constantes de estados y permisos reutilizables.

### 5.2 `users`

Responsabilidad:

- Modelo de usuario personalizado.
- Gestión de roles.
- Autenticación JWT.
- Perfil del usuario.
- Vinculación con información operativa relevante, por ejemplo nombre, apartamento, teléfono y estado activo.

### 5.3 `incidents`

Responsabilidad:

- Modelo `Incidente`.
- Modelo `EvidenciaIncidente`.
- Modelo `HistorialEstado`.
- Reglas de cálculo de prioridad.
- Reglas de transición de estados.
- Asignación de vigilantes.
- Filtros y consultas por estado, categoría y fechas.

### 5.4 `notifications`

Responsabilidad:

- Modelo `Notificacion`.
- Generación automática de mensajes internos.
- Registro del estado de entrega push.
- Integración con Firebase Cloud Messaging.

### 5.5 `assistant`

Responsabilidad:

- Endpoint del asistente virtual.
- Orquestación de consultas a Anthropic Claude Haiku.
- Construcción del contexto permitido para respuestas.
- Registro de consultas realizadas por usuarios para auditoría y mejora futura.

### 5.6 `dashboard`

Responsabilidad:

- Vistas del panel web.
- Tablero administrativo.
- Métricas agregadas.
- Vistas HTML para usuarios, incidentes, reportes y configuración.

## 6. Estructura lógica de la aplicación Flutter

La app móvil seguirá una organización por features para mantener independencia funcional y facilitar pruebas.

### 6.1 `core`

Responsabilidad:

- Configuración de entorno.
- Cliente HTTP.
- Manejo de tokens JWT.
- Persistencia segura local.
- Tema visual.
- Componentes reutilizables.
- Enrutamiento base.

### 6.2 `features/auth`

Responsabilidad:

- Inicio de sesión.
- Cierre de sesión.
- Carga del perfil autenticado.
- Restauración de sesión.

### 6.3 `features/home`

Responsabilidad:

- Pantalla principal según rol.
- Resumen de actividad.
- Accesos rápidos.

### 6.4 `features/incidents`

Responsabilidad:

- Crear incidente con formulario guiado.
- Adjuntar hasta tres evidencias.
- Listar incidentes propios del residente.
- Mostrar detalle, historial y estado.
- Mostrar cola operativa y acciones de atención para vigilantes.

### 6.5 `features/notifications`

Responsabilidad:

- Listado de notificaciones internas.
- Marcado como leídas.
- Apertura contextual del incidente relacionado.

### 6.6 `features/assistant`

Responsabilidad:

- Interfaz de chat.
- Consulta al asistente virtual.
- Historial corto de conversación local.

### 6.7 `features/profile`

Responsabilidad:

- Datos del usuario.
- Cambio de contraseña.
- Configuración básica.

### 6.8 `features/emergency_contacts`

Responsabilidad:

- Directorio de contactos importantes del conjunto y emergencias externas.

## 7. Comunicación entre componentes

### 7.1 Flutter -> API REST

- Protocolo: HTTPS.
- Formato: JSON.
- Autenticación: JWT Bearer.
- Archivos: multipart/form-data para evidencias.

### 7.2 Panel web -> servicios internos Django

- No hay API separada entre panel web y backend: el panel web usa directamente servicios, consultas y plantillas del mismo proyecto Django.
- Esta decisión reduce complejidad para el trabajo de grado y mantiene una sola fuente de verdad de negocio.

### 7.3 Django -> FCM

- Comunicación saliente mediante SDK o llamada HTTP del servicio de Firebase.
- Se dispara después de persistir el cambio de negocio relevante.

### 7.4 Django -> Anthropic Claude

- Endpoint servidor a servidor.
- El backend controla prompt del sistema, contexto permitido y filtrado de respuestas.
- La app móvil nunca llama directamente al proveedor de IA.

## 8. Diseño de capas en backend

Para cada módulo del backend se seguirá esta separación:

- `models`: estructura persistente.
- `selectors`: consultas complejas y optimizadas.
- `services`: reglas de negocio y orquestación.
- `serializers`: entrada y salida API.
- `views`: endpoints REST o vistas HTML.
- `permissions`: permisos por rol y por recurso.
- `tests`: pruebas unitarias e integrales.

Esta estructura evita concentrar toda la lógica en modelos o vistas y facilita mantenimiento.

## 9. API REST propuesta

Prefijo general: `/api/v1/`

### 9.1 Autenticación y perfil

- `POST /api/v1/auth/login/`
  - Inicia sesión con correo o documento y contraseña.
- `POST /api/v1/auth/refresh/`
  - Renueva access token.
- `POST /api/v1/auth/logout/`
  - Invalida el refresh token del dispositivo actual.
- `GET /api/v1/auth/me/`
  - Devuelve información del usuario autenticado.
- `PATCH /api/v1/auth/me/`
  - Actualiza datos permitidos del perfil.
- `POST /api/v1/auth/change-password/`
  - Cambia la contraseña.

### 9.2 Usuarios y administración

- `GET /api/v1/usuarios/`
  - Lista usuarios para administración.
- `POST /api/v1/usuarios/`
  - Crea usuario.
- `GET /api/v1/usuarios/{id}/`
  - Detalle de usuario.
- `PATCH /api/v1/usuarios/{id}/`
  - Edita usuario.
- `POST /api/v1/usuarios/{id}/activar/`
  - Activa usuario.
- `POST /api/v1/usuarios/{id}/desactivar/`
  - Desactiva usuario.

### 9.3 Catálogos

- `GET /api/v1/catalogos/categorias-incidente/`
  - Devuelve categorías disponibles.
- `GET /api/v1/catalogos/estados-incidente/`
  - Devuelve estados del flujo.
- `GET /api/v1/catalogos/contactos-emergencia/`
  - Devuelve directorio de apoyo.

### 9.4 Incidentes

- `GET /api/v1/incidentes/`
  - Lista incidentes según rol:
  - residente: solo sus reportes.
  - vigilante: incidentes abiertos, asignados o atendidos por operación.
  - administrador: todos.
- `POST /api/v1/incidentes/`
  - Crea un incidente con datos y evidencias.
- `GET /api/v1/incidentes/{id}/`
  - Detalle completo del incidente.
- `PATCH /api/v1/incidentes/{id}/`
  - Edita campos permitidos antes de cierre, según permisos.
- `GET /api/v1/incidentes/{id}/historial/`
  - Obtiene línea de tiempo de estados.
- `POST /api/v1/incidentes/{id}/asignar/`
  - Asigna vigilante.
- `POST /api/v1/incidentes/{id}/atender/`
  - Cambia a estado en atención.
- `POST /api/v1/incidentes/{id}/resolver/`
  - Marca el incidente como resuelto.
- `POST /api/v1/incidentes/{id}/cerrar/`
  - Cierre administrativo final.
- `POST /api/v1/incidentes/{id}/reabrir/`
  - Reabre incidente cuando exista justificación.

### 9.5 Evidencias

- `POST /api/v1/incidentes/{id}/evidencias/`
  - Adjunta evidencias nuevas respetando el máximo permitido.
- `DELETE /api/v1/incidentes/{id}/evidencias/{evidencia_id}/`
  - Elimina evidencia cuando las reglas lo permitan.

### 9.6 Notificaciones

- `GET /api/v1/notificaciones/`
  - Lista notificaciones del usuario autenticado.
- `POST /api/v1/notificaciones/{id}/marcar-leida/`
  - Marca una notificación como leída.
- `POST /api/v1/notificaciones/marcar-todas-leidas/`
  - Marca todas como leídas.

### 9.7 Asistente virtual

- `POST /api/v1/asistente/consulta/`
  - Envía una consulta del usuario y devuelve respuesta.
- `GET /api/v1/asistente/preguntas-frecuentes/`
  - Devuelve FAQs precargadas para acceso rápido.

### 9.8 Dashboard administrativo

- `GET /api/v1/dashboard/resumen/`
  - Totales, abiertos, resueltos, cerrados, prioridad alta y tiempos promedio.
- `GET /api/v1/dashboard/tendencias/`
  - Serie temporal de incidentes.
- `GET /api/v1/dashboard/categorias/`
  - Distribución por categoría.

## 10. Rutas del panel web

Prefijo sugerido: `/panel/`

- `/panel/login/`
- `/panel/`
- `/panel/incidentes/`
- `/panel/incidentes/{id}/`
- `/panel/usuarios/`
- `/panel/usuarios/{id}/`
- `/panel/notificaciones/`
- `/panel/reportes/`
- `/panel/configuracion/`

Estas rutas serán HTML renderizado del lado del servidor y reutilizarán la misma lógica de dominio del backend.

## 11. Ciclo de vida del incidente

Estados definidos:

- `reportado`
- `asignado`
- `en_atencion`
- `resuelto`
- `cerrado`
- `reabierto`

Reglas generales:

- Todo incidente inicia en `reportado`.
- Solo vigilancia o administración pueden asignar y pasar a `en_atencion`.
- Solo vigilancia o administración pueden marcar como `resuelto`.
- Solo administración puede marcar como `cerrado`.
- Un incidente cerrado solo puede volver a `reabierto` por justificación administrativa.

## 12. Flujo de datos completo: del reporte al cierre

### 12.1 Reporte por residente

1. El residente inicia sesión en la app Flutter.
2. Completa formulario con categoría, título, descripción, ubicación interna y hasta tres imágenes.
3. La app envía `POST /api/v1/incidentes/` con JSON y archivos.
4. Django valida autenticación, datos y cantidad de evidencias.
5. Se crea el incidente en estado `reportado`.
6. Se calcula prioridad con base en categoría, palabras clave críticas y contexto operativo.
7. Se guardan las evidencias.
8. Se genera primer registro de `HistorialEstado`.
9. Se crean notificaciones para vigilancia y administración.
10. Se envía push vía FCM a usuarios relevantes.

### 12.2 Atención por vigilancia

1. El vigilante visualiza la cola operativa en la app.
2. Abre detalle del incidente.
3. Ejecuta acción de asignación o atención.
4. Django valida permisos y transición de estado.
5. Se actualiza el incidente.
6. Se registra nuevo `HistorialEstado`.
7. Se generan notificaciones para residente y administración.
8. El residente puede ver en tiempo real que el caso está siendo atendido.

### 12.3 Resolución operativa

1. El vigilante agrega observación final.
2. Ejecuta la acción de resolver.
3. El backend cambia el estado a `resuelto`.
4. Se registra la transición en historial.
5. Se notifica al residente que el caso fue resuelto operativamente.

### 12.4 Cierre administrativo

1. El administrador revisa el caso desde el panel web.
2. Verifica evidencia, trazabilidad y observaciones.
3. Si todo está correcto, ejecuta cierre.
4. El backend cambia el estado a `cerrado`.
5. Se crea registro final de historial.
6. Se genera notificación de cierre al residente.
7. El incidente queda solo para consulta y auditoría, salvo reapertura autorizada.

## 13. Reglas de seguridad y permisos

- Residente:
  - Puede crear incidentes.
  - Puede ver sus propios incidentes, historial y notificaciones.
  - Puede consultar el asistente virtual.

- Vigilante:
  - Puede ver incidentes operativos.
  - Puede actualizar estado según flujo permitido.
  - Puede registrar observaciones de atención.

- Administrador:
  - Acceso completo a panel web.
  - Gestión de usuarios.
  - Acceso total a incidentes, métricas y cierre administrativo.

## 14. Persistencia y almacenamiento

- Desarrollo:
  - SQLite para rapidez de arranque.
- Producción:
  - PostgreSQL por robustez, concurrencia y soporte de índices más sólidos.
- Archivos de evidencia:
  - Durante desarrollo pueden almacenarse localmente.
  - En producción se dejará preparado el backend para migrar a almacenamiento externo compatible con Django.

## 15. Observabilidad y calidad

- Logging estructurado en backend.
- Validaciones centralizadas en serializers y servicios.
- Historial inmutable para auditoría.
- Pruebas de API, permisos, servicios y flujos críticos.
- Datos de demostración para evaluación académica.

## 16. Decisiones clave de arquitectura

- Se elige un monolito modular porque:
  - reduce complejidad de despliegue;
  - facilita la evaluación universitaria;
  - acelera desarrollo sin sacrificar orden interno.

- Se usa JWT porque:
  - desacopla cliente móvil del backend;
  - simplifica sesiones móviles;
  - encaja con DRF y SimpleJWT.

- Se centraliza la IA en backend porque:
  - protege la clave del proveedor;
  - permite control de contexto;
  - facilita auditoría y límites de uso.

- Se mantiene un historial inmutable porque:
  - garantiza trazabilidad;
  - mejora la confianza del jurado evaluador;
  - soporta métricas y revisiones posteriores.
