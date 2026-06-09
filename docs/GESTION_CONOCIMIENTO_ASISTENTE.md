# Gestión profesional de la base de conocimiento del asistente

## Propósito

La base de conocimiento administrable permite mantener las preguntas y respuestas de CommuBot después de la entrega del proyecto sin modificar código ni desplegar una nueva versión. El contenido se gestiona desde Django Admin y el motor local solo publica información aprobada y vigente.

El catálogo estático incluido en el repositorio funciona como respaldo inicial controlado. Cuando una entrada se importa a la base de datos, su estado administrado prevalece sobre el respaldo: si se deja en borrador, revisión, inactiva o rechazada, deja de estar disponible para respuestas oficiales.

## Acceso y responsabilidades

Ruta local de administración:

```text
http://127.0.0.1:8000/admin/asistente/entradaconocimiento/
```

Solo usuarios con rol `ADMINISTRADOR` o superusuarios pueden consultar y modificar:

- Base de conocimiento.
- Versiones de conocimiento.
- Consultas sin respuesta.
- Logs técnicos del asistente.

Los residentes y vigilantes no pueden acceder a estos registros administrativos.

## Estados del conocimiento

| Estado | Uso | Disponible para CommuBot |
|---|---|---|
| Borrador | Contenido recién creado o en edición | No |
| En revisión | Contenido listo para validación administrativa | No |
| Aprobada | Respuesta validada, con responsable y fecha de aprobación | Sí, si está vigente |
| Inactiva | Respuesta retirada temporal o definitivamente | No |
| Rechazada | Contenido descartado durante revisión | No |

Una entrada aprobada registra obligatoriamente quién la aprobó. Las fechas `vigente_desde` y `vigente_hasta` permiten programar su disponibilidad.

## Flujo recomendado

1. Crear la pregunta y respuesta como borrador.
2. Registrar categoría, intención, al menos tres palabras clave y dos variaciones naturales.
3. Definir los roles autorizados para recibir la respuesta.
4. Registrar la fuente interna y una nota clara del cambio.
5. Usar la acción `Enviar entradas seleccionadas a revisión`.
6. Un administrador valida contenido, vigencia, fuente y roles.
7. Usar la acción `Aprobar y publicar entradas seleccionadas`.
8. Probar la pregunta desde CommuBot.
9. Desactivar la entrada si deja de ser válida.

No se debe aprobar información sin fuente verificable. Valores de cuotas, sanciones, horarios variables o decisiones administrativas deben redactarse como orientación sujeta a confirmación.

## Versionado y auditoría

Cada cambio de contenido, estado, vigencia, roles o clasificación incrementa automáticamente la versión de la entrada. El sistema conserva un snapshot inmutable con:

- Número de versión.
- Datos completos de esa versión.
- Usuario responsable del cambio.
- Fecha y hora del cambio.

El historial se consulta dentro de cada entrada o en `Versiones de conocimiento`. Las versiones no pueden editarse ni eliminarse desde Django Admin.

Las actualizaciones concurrentes se serializan mediante una transacción y bloqueo de fila para evitar números de versión duplicados.

El código identificador de una entrada es inmutable. Si se edita contenido, clasificación, roles o vigencia de una entrada aprobada, Django Admin la devuelve automáticamente a `En revisión`; la versión anterior deja de publicarse hasta que un administrador apruebe el cambio.

Las entradas no se eliminan desde Django Admin. Cuando una respuesta deja de aplicar, se desactiva para conservar toda su trazabilidad.

## Preguntas frecuentes sin respuesta

Cuando una consulta válida del dominio no alcanza confianza local suficiente, CommuSafe la registra de forma agrupada en `Consultas sin respuesta`. El registro conserva:

- Consulta normalizada y muestra redactada.
- Rol que realizó la consulta.
- Cantidad de repeticiones.
- Confianza máxima detectada.
- Intención sugerida.
- Primera y última fecha de consulta.
- Estado de revisión.

Las consultas fuera del dominio y los intentos de manipulación del prompt no se convierten en conocimiento.

Para convertir una necesidad frecuente:

1. Ordenar las consultas por cantidad.
2. Seleccionar una o varias consultas relevantes.
3. Usar `Convertir consultas seleccionadas en borradores`.
4. Redactar una respuesta verificada y completar su clasificación.
5. Enviar a revisión y aprobar mediante el flujo normal.

El borrador generado nunca se publica automáticamente.

## Importación inicial

Después de aplicar migraciones, un administrador puede importar el catálogo inicial:

```powershell
cd backend
python manage.py sincronizar_base_conocimiento --usuario admin@dominio.com
```

El comando crea entradas faltantes y no sobrescribe cambios administrativos existentes. Para actualizar deliberadamente entradas ya importadas:

```powershell
python manage.py sincronizar_base_conocimiento --usuario admin@dominio.com --actualizar
```

La opción `--actualizar` debe usarse únicamente después de revisar los cambios, porque crea nuevas versiones sobre el contenido administrado.

## Controles de publicación

- El motor consulta únicamente entradas administradas con estado `APROBADA` y vigencia activa.
- Una entrada administrada no aprobada bloquea cualquier versión estática con el mismo código.
- Las respuestas estáticas pendientes se presentan únicamente como orientación segura marcada para validación, no como información oficial.
- El índice local se actualiza automáticamente después de cambios y también verifica revisiones periódicamente.
- El repositorio administrado de Django prevalece sobre respuestas potencialmente desactualizadas del servicio NLP auxiliar.
- Gemini o Anthropic continúan siendo respaldo controlado; no convierten automáticamente sus respuestas en conocimiento oficial.

## Verificación técnica

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest asistente/tests.py -q
python manage.py validar_base_conocimiento
```

Pruebas cubiertas:

- Publicación de entradas aprobadas.
- Exclusión de borradores.
- Creación de versiones inmutables.
- Agrupación de consultas sin respuesta.
- Importación inicial controlada.
