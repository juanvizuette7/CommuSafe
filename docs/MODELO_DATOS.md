# Modelo de Datos de CommuSafe

## 1. Enfoque general

El modelo de datos se diseña alrededor del incidente como entidad central del sistema. Todas las acciones relevantes, como creación, cambio de estado, evidencia y notificación, se relacionan directa o indirectamente con el incidente para asegurar trazabilidad completa.

## 2. Entidades principales

### 2.1 Usuario

Representa a cualquier actor autenticado del sistema: residente, vigilante o administrador.

Tabla lógica: `users_usuario`

Campos propuestos:

| Campo | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| id | UUID | Sí | Identificador único primario. |
| email | EmailField | Sí | Credencial principal de acceso, única. |
| username | CharField(150) | Sí | Identificador visible y único. |
| first_name | CharField(150) | Sí | Nombres del usuario. |
| last_name | CharField(150) | Sí | Apellidos del usuario. |
| telefono | CharField(20) | No | Número de contacto. |
| apartamento | CharField(20) | No | Unidad residencial asociada, aplica sobre todo a residentes. |
| rol | CharField(20) | Sí | Valores permitidos: `residente`, `vigilante`, `administrador`. |
| is_active | BooleanField | Sí | Estado de activación de la cuenta. |
| is_staff | BooleanField | Sí | Habilita acceso interno al panel y administración técnica cuando aplique. |
| fecha_ultimo_acceso | DateTimeField | No | Último acceso registrado. |
| creado_en | DateTimeField | Sí | Fecha de creación. |
| actualizado_en | DateTimeField | Sí | Fecha de última actualización. |

Reglas:

- `email` y `username` deben ser únicos.
- `rol` define permisos y navegación.
- `apartamento` será obligatorio para residentes y opcional para otros roles.

### 2.2 Incidente

Es la entidad central del sistema. Representa un hecho reportado dentro del conjunto residencial.

Tabla lógica: `incidents_incidente`

Campos propuestos:

| Campo | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| id | UUID | Sí | Identificador único primario. |
| numero_caso | CharField(20) | Sí | Consecutivo visible para trazabilidad humana, único. |
| residente_reporta_id | FK -> Usuario | Sí | Usuario que reportó el incidente. |
| vigilante_asignado_id | FK -> Usuario | No | Vigilante responsable actual. |
| categoria | CharField(50) | Sí | Clasificación del incidente. |
| titulo | CharField(150) | Sí | Resumen corto del caso. |
| descripcion | TextField | Sí | Detalle narrativo del incidente. |
| ubicacion | CharField(120) | Sí | Lugar dentro del conjunto. |
| prioridad | CharField(20) | Sí | Valor calculado: `baja`, `media`, `alta`, `critica`. |
| estado | CharField(20) | Sí | Estado actual del incidente. |
| observacion_resolucion | TextField | No | Comentario final operativo o administrativo. |
| resuelto_en | DateTimeField | No | Momento en que pasa a resuelto. |
| cerrado_en | DateTimeField | No | Momento del cierre administrativo. |
| creado_en | DateTimeField | Sí | Fecha de creación. |
| actualizado_en | DateTimeField | Sí | Fecha de última actualización. |

Reglas:

- `prioridad` se calcula automáticamente y no la define manualmente el usuario final.
- `estado` sigue un flujo controlado.
- Un incidente pertenece siempre a un residente reportante.
- La asignación a vigilante es opcional al crear y obligatoria solo cuando entra en atención.

### 2.3 EvidenciaIncidente

Representa cada imagen adjunta a un incidente.

Tabla lógica: `incidents_evidenciaincidente`

Campos propuestos:

| Campo | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| id | UUID | Sí | Identificador único primario. |
| incidente_id | FK -> Incidente | Sí | Incidente al que pertenece la evidencia. |
| archivo | ImageField | Sí | Imagen almacenada. |
| nombre_original | CharField(255) | Sí | Nombre original del archivo cargado. |
| tamano_bytes | PositiveIntegerField | Sí | Tamaño del archivo. |
| contenido_tipo | CharField(100) | Sí | MIME type de la imagen. |
| subido_por_id | FK -> Usuario | Sí | Usuario que adjuntó la evidencia. |
| creado_en | DateTimeField | Sí | Fecha de carga. |

Reglas:

- Máximo 3 evidencias por incidente.
- Solo se permiten formatos de imagen válidos.
- La evidencia queda asociada permanentemente al caso para auditoría.

### 2.4 HistorialEstado

Registra de forma inmutable cada transición o evento relevante de un incidente.

Tabla lógica: `incidents_historialestado`

Campos propuestos:

| Campo | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| id | UUID | Sí | Identificador único primario. |
| incidente_id | FK -> Incidente | Sí | Incidente afectado. |
| estado_anterior | CharField(20) | No | Estado previo; puede ser nulo en la creación inicial. |
| estado_nuevo | CharField(20) | Sí | Estado resultante. |
| comentario | TextField | No | Observación asociada al cambio. |
| cambiado_por_id | FK -> Usuario | Sí | Usuario que ejecutó el cambio. |
| creado_en | DateTimeField | Sí | Momento exacto del evento. |

Reglas:

- Es un registro inmutable: no se edita ni elimina.
- La creación del incidente genera al menos un registro inicial.
- Toda transición de estado debe crear su entrada correspondiente.

### 2.5 Notificacion

Representa mensajes internos generados automáticamente por el sistema para informar eventos relevantes a un usuario.

Tabla lógica: `notifications_notificacion`

Campos propuestos:

| Campo | Tipo | Requerido | Descripción |
| --- | --- | --- | --- |
| id | UUID | Sí | Identificador único primario. |
| usuario_id | FK -> Usuario | Sí | Destinatario de la notificación. |
| incidente_id | FK -> Incidente | No | Incidente relacionado cuando aplique. |
| titulo | CharField(150) | Sí | Encabezado breve del mensaje. |
| mensaje | TextField | Sí | Contenido visible al usuario. |
| tipo | CharField(30) | Sí | Tipo funcional: `incidente`, `sistema`, `recordatorio`, `alerta`. |
| leida | BooleanField | Sí | Indica si el usuario ya la abrió. |
| enviada_push | BooleanField | Sí | Indica si también se intentó enviar push. |
| creada_en | DateTimeField | Sí | Fecha de creación. |
| leida_en | DateTimeField | No | Fecha en la que fue leída. |

Reglas:

- Una notificación pertenece a un usuario destino.
- Puede o no estar asociada a un incidente.
- Se genera automáticamente desde eventos de negocio.

## 3. Entidades de apoyo recomendadas

Aunque no forman parte del mínimo solicitado, el sistema quedará mejor preparado si luego incorpora estas entidades complementarias:

- `DispositivoFCM`:
  - Guarda token push por usuario y dispositivo.
- `ConsultaAsistente`:
  - Registra preguntas realizadas al asistente virtual y su respuesta.
- `CategoriaIncidente`:
  - Catálogo administrable en lugar de valores quemados.
- `ContactoEmergencia`:
  - Directorio configurable mostrado en la app.

Estas entidades no reemplazan a las principales; complementan la solución.

## 4. Relaciones entre entidades

### 4.1 Relaciones directas

- Un `Usuario` puede crear muchos `Incidente`.
- Un `Usuario` vigilante puede estar asignado a muchos `Incidente`.
- Un `Incidente` pertenece a un `Usuario` residente que lo reporta.
- Un `Incidente` puede tener cero o un `Usuario` vigilante asignado.
- Un `Incidente` puede tener muchas `EvidenciaIncidente`.
- Un `Incidente` puede tener muchos `HistorialEstado`.
- Un `Incidente` puede generar muchas `Notificacion`.
- Un `Usuario` puede subir muchas `EvidenciaIncidente`.
- Un `Usuario` puede ejecutar muchos `HistorialEstado`.
- Un `Usuario` puede recibir muchas `Notificacion`.

### 4.2 Diagrama de relaciones descrito en texto

```text
Usuario (1) ---- (N) Incidente
  motivo: un residente puede reportar múltiples incidentes.

Usuario (1) ---- (N) Incidente [como vigilante_asignado]
  motivo: un vigilante puede atender múltiples incidentes en momentos distintos.

Incidente (1) ---- (N) EvidenciaIncidente
  motivo: cada incidente admite hasta 3 imágenes de soporte.

Usuario (1) ---- (N) EvidenciaIncidente
  motivo: se debe saber quién subió cada archivo.

Incidente (1) ---- (N) HistorialEstado
  motivo: cada cambio de estado debe quedar registrado para trazabilidad.

Usuario (1) ---- (N) HistorialEstado
  motivo: se debe conocer qué actor produjo cada cambio.

Usuario (1) ---- (N) Notificacion
  motivo: cada notificación pertenece a un destinatario concreto.

Incidente (1) ---- (N) Notificacion
  motivo: muchas notificaciones se generan por eventos del incidente.
```

## 5. Justificación de diseño relacional

- `Incidente` es el centro del dominio porque concentra la necesidad principal del sistema.
- `HistorialEstado` se separa de `Incidente` para preservar trazabilidad sin sobrescribir el pasado.
- `EvidenciaIncidente` se separa porque un incidente puede tener múltiples archivos y cada archivo requiere sus propios metadatos.
- `Notificacion` se separa porque el sistema necesita una bandeja por usuario, independiente del incidente, con estado de lectura y entrega.
- `Usuario` unifica todos los actores para simplificar autenticación, permisos y escalabilidad.

## 6. Enumeraciones recomendadas

### 6.1 Roles de usuario

- `residente`
- `vigilante`
- `administrador`

### 6.2 Estados del incidente

- `reportado`
- `asignado`
- `en_atencion`
- `resuelto`
- `cerrado`
- `reabierto`

### 6.3 Prioridades del incidente

- `baja`
- `media`
- `alta`
- `critica`

### 6.4 Tipos de notificación

- `incidente`
- `sistema`
- `recordatorio`
- `alerta`

## 7. Reglas de integridad importantes

- No puede existir un `Incidente` sin `residente_reporta_id`.
- No puede existir `EvidenciaIncidente` sin `incidente_id`.
- No puede existir `HistorialEstado` sin `incidente_id` ni `cambiado_por_id`.
- No puede existir `Notificacion` sin `usuario_id`.
- El backend debe impedir más de 3 evidencias por incidente.
- El cierre administrativo exige que el incidente ya esté resuelto o reabierto con decisión explícita.

## 8. Índices y optimización recomendada

- Índice en `Usuario.email`.
- Índice en `Usuario.rol`.
- Índice en `Incidente.numero_caso`.
- Índice compuesto en `Incidente.estado`, `Incidente.prioridad`, `Incidente.creado_en`.
- Índice en `Incidente.residente_reporta_id`.
- Índice en `Incidente.vigilante_asignado_id`.
- Índice en `HistorialEstado.incidente_id`, `HistorialEstado.creado_en`.
- Índice en `Notificacion.usuario_id`, `Notificacion.leida`, `Notificacion.creada_en`.

## 9. Convenciones de borrado

- `Usuario` no se elimina físicamente en escenarios normales; se desactiva.
- `Incidente` no debe eliminarse después de creado, salvo limpieza técnica en desarrollo.
- `HistorialEstado` nunca se elimina.
- `Notificacion` puede archivarse o mantenerse para trazabilidad.
- `EvidenciaIncidente` solo podrá eliminarse bajo reglas controladas antes de estados finales si el negocio lo permite; por defecto se preserva.
