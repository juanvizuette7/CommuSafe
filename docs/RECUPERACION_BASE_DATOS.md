# Recuperación y reconstrucción segura de base de datos

## Estado de recuperación

La base PostgreSQL anterior de Render aparece vencida y el repositorio no conserva una URL privada operativa, dump PostgreSQL ni backup exportado. Por esta razón no se puede afirmar que los registros de PostgreSQL anterior hayan sido recuperados directamente.

Fuentes verificadas:

- SQLite local privada `backend/db.sqlite3`, excluida de Git.
- Versiones históricas de SQLite presentes antes de su exclusión.
- Migraciones Django y modelos vigentes.
- Comandos `preparar_lanzamiento`, `cargar_demo` y `sincronizar_base_conocimiento`.
- Base local versionada del asistente con 108 preguntas frecuentes.
- Documentación, pruebas e historial Git.

La SQLite local actual conserva el último estado operativo coherente encontrado: ocho usuarios, cuatro incidentes, tres cambios de estado y notificaciones relacionadas. Las SQLite históricas contienen conjuntos de demostración anteriores y no incluyen conversaciones persistentes del asistente.

## Mecanismo idempotente

El comando siguiente completa una base nueva sin eliminar ni sobrescribir registros existentes:

```powershell
cd backend
python manage.py migrate
python manage.py reconstruir_base_segura
```

Puede ejecutarse varias veces. Usa `get_or_create`, conserva contraseñas y datos existentes, y solo crea registros faltantes:

- Ocho usuarios de demostración por roles.
- Cuatro incidentes coherentes con historial y notificaciones.
- Un aviso recurrente.
- Una conversación demostrativa identificada como tal.
- La base administrable del asistente con al menos 100 entradas verificadas.

Las contraseñas de demostración se leen de `RECOVERY_ADMIN_PASSWORD` y `RECOVERY_USER_PASSWORD`. Si no están configuradas, se usan las credenciales académicas documentadas para la sustentación. Deben rotarse si el entorno deja de ser exclusivamente demostrativo.

## Neon y Render

`DATABASE_URL` debe configurarse únicamente como variable privada del servicio Render usando la cadena de conexión de Neon. No debe copiarse al repositorio, documentación, logs ni comandos versionados.

El Blueprint ejecuta en orden:

```text
migrate
crear_admin_produccion
reconstruir_base_segura
collectstatic
```

El repositorio ya no declara una base PostgreSQL gratuita de Render, evitando que un nuevo despliegue vuelva a enlazar la base vencida.

## Verificación

```powershell
cd backend
python manage.py check
python manage.py showmigrations
python manage.py reconstruir_base_segura
python -m pytest tests/test_reconstruccion_base.py -q
python -m pytest -q
python manage.py validar_base_conocimiento
python manage.py evaluar_asistente_local
```

La ejecución debe confirmar que todas las migraciones están aplicadas, existen registros operativos y una segunda reconstrucción no cambia los conteos.

## Resultado verificado localmente

La reconstrucción fue ejecutada dos veces sobre la SQLite local conservada. La primera ejecución completó información faltante y la segunda creó cero registros.

| Registro principal | Cantidad final |
|---|---:|
| Tablas | 26 |
| Usuarios | 8 |
| Incidentes | 4 |
| Historiales de estado | 3 |
| Notificaciones | 40 |
| Avisos programados | 1 |
| Entradas administrables del asistente | 108 |
| Conversaciones del asistente | 1 |
| Mensajes persistentes | 2 |

Validaciones ejecutadas:

- `python manage.py check`: sin problemas.
- Migraciones pendientes: cero.
- Creación y eliminación posterior de un registro: correcta.
- Suite específica de reconstrucción: `2 passed`.
- Suite completa backend: `202 passed, 14 subtests passed`.
- `flutter analyze`: sin problemas.
- Base de conocimiento: 108 preguntas, 100 verificadas y 8 pendientes de validación administrativa.

El servicio público de Render respondió correctamente en `/health/`, pero las credenciales académicas conocidas no autenticaron antes del despliegue de esta reconstrucción. Esto confirma que no debe afirmarse que la nueva base ya contiene los registros locales hasta completar y verificar el despliegue.

## Resultado verificado en Neon

El 9 de junio de 2026 se actualizó el comando de compilación del servicio Render y se desplegó el commit de reconstrucción. La variable privada `DATABASE_URL` fue verificada sin imprimir su contenido y apunta a Neon.

Validación pública posterior al despliegue:

| Flujo | Resultado |
|---|---|
| Health check | `200` |
| Login administrador | `200` |
| Login residente | `200` |
| Login vigilante | `200` |
| Panel web y dashboard | `200` |
| Usuarios visibles para administrador | 9 |
| Incidentes visibles para administrador y vigilante | 4 |
| Incidentes propios del residente de prueba | 1 |
| Conversación persistente del residente de prueba | 1 |
| Notificaciones segmentadas | Disponibles para los tres roles |
| Asistente virtual | Respuesta local no vacía |

El total de usuarios es nueve porque Neon ya contenía una cuenta administrativa creada mediante variables privadas de producción. El comando conservó esa cuenta y agregó únicamente las cuentas faltantes.

Para el primer inicio de sesión mediante API se debe aceptar la política de tratamiento de datos. La aplicación móvil y el panel web gestionan este flujo desde su interfaz.

## Restricciones

- No versionar `.env`, SQLite, dumps, backups, archivos multimedia privados, logs o credenciales.
- No ejecutar `preparar_lanzamiento` para recuperar una base existente porque elimina datos operativos.
- No afirmar que datos reconstruidos son registros reales recuperados de PostgreSQL.
- Para recuperar datos reales de Render se requiere que el proveedor habilite temporalmente la base vencida o entregue un backup descargable.
