# Plan de pruebas de CommuSafe

## Objetivo
El registro detallado de casos de prueba, resultados obtenidos, estados y evidencias solicitadas por ISO/IEC/IEEE 29119 se encuentra en `docs/REGISTRO_CASOS_PRUEBA_29119.md`.

Este plan organiza las pruebas de CommuSafe con base en los atributos relevantes del estándar ISO/IEC 25010: funcionalidad, usabilidad, confiabilidad, seguridad, eficiencia y mantenibilidad.

Documentar las pruebas aplicadas al proyecto CommuSafe para validar la calidad, estabilidad, seguridad, disponibilidad y correcto funcionamiento del sistema.

## Alcance

El plan de pruebas contempla los componentes principales del sistema: backend, panel web administrativo, aplicación móvil, integraciones, despliegue y documentación metodológica.

## Tipos de pruebas consideradas

- Pruebas funcionales
- Pruebas exploratorias
- Validación W3C
- Pruebas de accesibilidad
- Pruebas de disponibilidad
- Pruebas de latencia y tiempos de respuesta
- Pruebas de conectividad mediante tracert
- Pruebas de rendimiento
- Pruebas de carga
- Pruebas de usabilidad
- Pruebas de compatibilidad entre navegadores y dispositivos
- Pruebas de seguridad básicas
- Pruebas de despliegue

## Estructura de casos de prueba

Cada caso de prueba debe contener:

- Identificador y nombre de la prueba
- Objetivo de la prueba
- Precondiciones
- Datos de entrada
- Pasos de ejecución
- Resultado esperado
- Resultado obtenido
- Estado de la prueba
- Evidencia mediante pantallazos, capturas o video demostrativo

## Gestión de incidencias

Cuando una prueba no sea superada, se debe registrar el fallo como incidencia dentro del tablero de GitHub Projects. La actividad debe retornar al estado To Do, Product Backlog o Sprint Backlog para que el desarrollador responsable pueda corregir el error y posteriormente realizar una nueva validación.

## Relación con GitHub Projects

Los casos de prueba se gestionan en GitHub Projects dentro del Sprint 5 — QA, pruebas, despliegue y documentación, permitiendo mantener trazabilidad entre pruebas, resultados, responsables, evidencias y estado de avance.

## Estructura sugerida para GitHub Projects

```text
QA — Plan de pruebas CommuSafe
├── CP-001 - Login correcto con JWT
├── CP-002 - Login incorrecto
├── CP-003 - Acceso protegido sin token
├── CP-004 - Control de acceso por rol
├── CP-005 - Creación de incidente
├── CP-006 - Visibilidad de incidentes por rol
├── CP-007 - Cambio de estado e historial
├── CP-008 - Límite de evidencias
├── CP-009 - Notificaciones por prioridad
├── CP-010 - Asistente virtual dentro del dominio
├── CP-011 - Validación W3C del panel web
├── CP-012 - Accesibilidad básica
├── CP-013 - Disponibilidad del servicio en Render
├── CP-014 - Latencia y tiempo de respuesta en Render
├── CP-015 - Conectividad con tracert
├── CP-016 - Rendimiento y concurrencia básica
├── CP-017 - Validación final de pruebas ejecutadas
└── CP-018 - Compatibilidad entre navegadores y dispositivos
```

Para registrar las tarjetas en GitHub Projects, se recomienda usar el nombre del caso como título del issue o tarjeta y enlazar como referencia principal el documento `docs/REGISTRO_CASOS_PRUEBA_29119.md`.

Campos sugeridos para cada tarjeta:

| Campo | Valor recomendado |
| --- | --- |
| Proyecto | CommuSafe |
| Épica | QA — Plan de pruebas CommuSafe |
| Sprint | Sprint 5 — QA, pruebas, despliegue y documentación |
| Tipo | Caso de prueba |
| Módulo | Backend, app móvil, panel web, despliegue o documentación |
| Prioridad | Alta para seguridad y funcionalidad principal; media para compatibilidad y evidencia complementaria |
| Estado | To Do, En Proceso, En Validación, Aprobada, Fallida o Bloqueada |
| Evidencia | Captura, video, salida de consola o reporte de herramienta |

Estados iniciales recomendados según el registro actual:

| Caso | Estado sugerido |
| --- | --- |
| CP-001 a CP-010 | Aprobada |
| CP-011 | Aprobada, con evidencia W3C anexada |
| CP-012 | Aprobada, con evidencia Lighthouse anexada |
| CP-013 a CP-016 | Aprobada |
| CP-017 | Aprobada |
| CP-018 | En Proceso |

Nota: las pruebas de despliegue en Render están cubiertas principalmente por `CP-013`, `CP-014`, `CP-015` y `CP-016`, porque validan disponibilidad, latencia, conectividad y concurrencia del servicio publicado.

## Procedimiento de ejecución por caso

Antes de ejecutar pruebas de backend desde consola, ubicarse en la carpeta del proyecto:

```powershell
cd "c:\Users\Anderson Ojeda\OneDrive\文档\Contruccion de trabajo de grado\CommuSafe"
```

### CP-001 - Login correcto con JWT

Proceso:

1. Ejecutar la prueba automatizada de login correcto.
2. Verificar que la respuesta incluya `access`, `refresh` y datos del usuario.
3. Adjuntar captura de la consola con el resultado aprobado.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py -k "login_correcto" -q
```

Nota tecnica: pytest esta configurado para tratar los warnings como errores mediante `filterwarnings = error`, de forma que nuevas advertencias no pasen inadvertidas. En Python 3.14, `google-genai` puede emitir un `DeprecationWarning` interno por el uso de `_UnionGenericAlias` en `google.genai.types`; se verifico `google-genai==2.4.0` y el warning persiste, por lo que se mantiene la version fijada del proyecto y se ignora solo esa advertencia externa no critica.

### CP-002 - Login incorrecto

Proceso:

1. Ejecutar la prueba automatizada con contraseña inválida.
2. Verificar que el backend responda `401`.
3. Confirmar que no se generan tokens JWT.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py -k "login_incorrecto" -q
```

### CP-003 - Acceso protegido sin token

Proceso:

1. Solicitar un endpoint protegido sin encabezado `Authorization`.
2. Verificar que la respuesta sea `401`.
3. Registrar la salida de consola como evidencia.

Comando automatizado:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py -k "sin_token" -q
```

Comando manual con servidor local activo:

```powershell
curl.exe -i http://127.0.0.1:8000/api/auth/perfil/
```

### CP-004 - Control de acceso por rol

Proceso:

1. Autenticarse como residente.
2. Intentar acceder a un endpoint administrativo.
3. Verificar que el sistema responda `403`.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py -k "administracion" -q
```

### CP-005 - Creación de incidente

Proceso:

1. Ejecutar prueba automatizada de creación de incidente.
2. Verificar código `201` y que el incidente tenga título, descripción, categoría, ubicación y evidencias cuando aplique.
3. Para evidencia visual, abrir la app móvil, iniciar sesión como residente y registrar un incidente desde el formulario.

Comando backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest incidentes/tests.py -k "crear_incidente" -q
```

Comandos para validar la app móvil:

```powershell
cd mobile\commusafe_app
flutter analyze
flutter test
```

### CP-006 - Visibilidad de incidentes por rol

Proceso:

1. Ejecutar pruebas con usuario residente y vigilante.
2. Confirmar que el residente solo vea sus propios incidentes.
3. Confirmar que el vigilante pueda ver todos los incidentes.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py incidentes/tests.py -k "ve_sus_propios_incidentes or ve_todos_los_incidentes" -q
```

### CP-007 - Cambio de estado e historial

Proceso:

1. Crear o usar un incidente existente.
2. Cambiar su estado como vigilante.
3. Verificar que el estado se actualice y que se cree registro en el historial.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py incidentes/tests.py -k "cambiar_estado" -q
```

### CP-008 - Límite de evidencias

Proceso:

1. Usar un incidente que ya tenga tres evidencias.
2. Intentar subir una cuarta evidencia.
3. Verificar que el sistema responda `400` y mantenga solo tres evidencias.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py incidentes/tests.py -k "mas_de_tres_evidencias or evidencia_limite" -q
```

### CP-009 - Notificaciones por prioridad

Proceso:

1. Crear un incidente de alta prioridad o emergencia.
2. Verificar que se generen notificaciones para los usuarios definidos por la regla de negocio.
3. Confirmar que no se duplique la notificación al usuario reportante.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py notificaciones/tests.py -k "notifica" -q
```

### CP-010 - Asistente virtual dentro del dominio

Proceso:

1. Enviar una pregunta relacionada con CommuSafe o la comunidad.
2. Verificar que la respuesta no esté vacía.
3. Confirmar que el asistente responda dentro del dominio funcional del sistema.

Comando:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_sistema_completo.py -k "chat_asistente" -q
```

### CP-011 - Validación W3C del panel web

Proceso:

1. Abrir `https://commusafe.onrender.com/login/`.
2. Copiar la URL en el validador Nu Html Checker: `https://validator.w3.org/nu/`.
3. Revisar errores críticos de HTML.
4. Adjuntar captura del resultado.

Comando opcional para confirmar que la página responde:

```powershell
curl.exe -I https://commusafe.onrender.com/login/
```

### CP-012 - Accesibilidad básica

Proceso:

1. Abrir `https://commusafe.onrender.com/login/` en Chrome o Edge.
2. Ejecutar Lighthouse desde DevTools.
3. Revisar accesibilidad, contraste, etiquetas de formularios y navegación por teclado.
4. Adjuntar captura del puntaje y observaciones.

Comando opcional para ejecutar Lighthouse si está instalado:

```powershell
npx lighthouse https://commusafe.onrender.com/login/ --view
```

### CP-013 - Disponibilidad del servicio en Render

Proceso:

1. Consultar el endpoint `/health/` del backend desplegado.
2. Verificar que responda HTTP `200`.
3. Confirmar que el JSON contenga `status: ok`.

Comando:

```powershell
curl.exe -s https://commusafe.onrender.com/health/
```

### CP-014 - Latencia y tiempo de respuesta en Render

Proceso:

1. Ejecutar medición de tiempo contra `/health/`.
2. Registrar una primera medición si el servicio está en arranque en frío.
3. Repetir la medición con el servicio activo.
4. Comparar `time_total`.

Comando:

```powershell
curl.exe -s -o NUL -w "status=%{http_code} time_total=%{time_total}s time_connect=%{time_connect}s time_starttransfer=%{time_starttransfer}s remote_ip=%{remote_ip}`n" https://commusafe.onrender.com/health/
```

### CP-015 - Conectividad con tracert

Proceso:

1. Ejecutar traza hacia el dominio de producción.
2. Verificar que exista resolución DNS y ruta de red.
3. Adjuntar captura de consola.

Comando:

```powershell
tracert commusafe.onrender.com
```

### CP-016 - Rendimiento y concurrencia básica

Proceso:

1. Enviar 20 solicitudes paralelas al endpoint `/health/`.
2. Verificar que todas respondan `200`.
3. Calcular promedio, mínimo y máximo de tiempo de respuesta.

Comando:

```powershell
$url='https://commusafe.onrender.com/health/'
$jobs=1..20 | ForEach-Object { Start-Job -ScriptBlock { param($u) curl.exe -s -o NUL -w "%{http_code} %{time_total}`n" $u } -ArgumentList $url }
$results=$jobs | Wait-Job | Receive-Job
$jobs | Remove-Job
$results
$times=$results | ForEach-Object { ($_ -split ' ')[1] } | ForEach-Object { [double]$_ }
"count=$($times.Count) avg=$([math]::Round(($times | Measure-Object -Average).Average,3))s min=$([math]::Round(($times | Measure-Object -Minimum).Minimum,3))s max=$([math]::Round(($times | Measure-Object -Maximum).Maximum,3))s"
```

### CP-017 - Validación final de pruebas ejecutadas

Proceso:

1. Ejecutar las pruebas automatizadas disponibles del backend.
2. Ejecutar las validaciones disponibles de la aplicación móvil.
3. Verificar que el servicio desplegado responda correctamente.
4. Registrar salidas de consola y capturas como evidencia de cierre.

Comandos de apoyo:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest -q

cd ..\mobile\commusafe_app
flutter analyze
flutter test
```

### CP-018 - Compatibilidad entre navegadores y dispositivos

Proceso:

1. Abrir el panel web en Chrome, Edge y Firefox.
2. Validar login, navegación principal y visualización adaptable.
3. Ejecutar la app Flutter en un emulador o dispositivo Android.
4. Adjuntar capturas por navegador y dispositivo.

Comandos de apoyo:

```powershell
cd mobile\commusafe_app
flutter devices
flutter analyze
flutter test
```

Validación general recomendada antes de cerrar el plan:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest -q

cd ..\mobile\commusafe_app
flutter analyze
flutter test
```
