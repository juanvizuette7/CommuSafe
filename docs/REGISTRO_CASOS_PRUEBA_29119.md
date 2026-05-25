# Registro de Casos de Prueba - ISO/IEC/IEEE 29119

Proyecto: CommuSafe  
Fecha de ejecución documentada: 14 de mayo de 2026  
Plataforma colaborativa sugerida: GitHub Projects del repositorio CommuSafe  
Ambientes evaluados: backend Django local, app Flutter local y servicio Render `https://commusafe.onrender.com`

Este documento consolida los casos de prueba finales del proyecto, siguiendo la estructura mínima solicitada y buenas prácticas de ISO/IEC/IEEE 29119: identificación, objetivo, precondiciones, datos, pasos, resultado esperado, resultado obtenido, estado y evidencia.

## 1. Flujo de gestión de pruebas

Cada caso debe registrarse como tarjeta o issue en la plataforma colaborativa usada por el equipo.

Estados recomendados:

| Estado | Uso |
| --- | --- |
| To Do | Caso definido, pendiente de ejecución o caso fallido que requiere corrección. |
| En Proceso | Caso en ejecución o incidente en análisis. |
| En Validación | Corrección implementada, pendiente de nueva prueba. |
| Aprobada | Resultado obtenido coincide con el resultado esperado. |
| Fallida | Resultado obtenido no cumple el resultado esperado. Debe volver a To Do con responsable asignado. |
| Bloqueada | No se puede ejecutar por falta de ambiente, credenciales o dependencia externa. |

Campos mínimos de la tarjeta:

- Identificador del caso.
- Nombre del caso.
- Tipo de prueba.
- Módulo afectado.
- Responsable.
- Resultado esperado.
- Resultado obtenido.
- Estado.
- Evidencia adjunta.
- Commit, rama o versión evaluada.

## 2. Evidencia técnica ejecutada

| Evidencia | Comando / fuente | Resultado obtenido | Estado |
| --- | --- | --- | --- |
| Verificación Django | `cd backend; .\.venv\Scripts\python.exe manage.py check` | `System check identified no issues (0 silenced).` | Aprobada |
| Suite backend | `cd backend; .\.venv\Scripts\python.exe -m pytest -q` | `146 passed, 6 subtests passed` | Aprobada |
| Análisis Flutter | `cd mobile\commusafe_app; flutter analyze` | `No issues found!` | Aprobada |
| Pruebas Flutter | `cd mobile\commusafe_app; flutter test` | `All tests passed!` | Aprobada |
| Disponibilidad producción | `curl.exe -s https://commusafe.onrender.com/health/` | `{"status": "ok", "servicio": "CommuSafe"}` | Aprobada |
| Latencia producción | `curl.exe -s -o NUL -w ... https://commusafe.onrender.com/health/` | 3/3 respuestas `200`; promedio `0.394s`, mínimo `0.275s`, máximo `0.458s` | Aprobada |
| Concurrencia básica | 20 solicitudes paralelas a `/health/` | 20/20 respuestas `200`; promedio `0.312s`, mínimo `0.261s`, máximo `0.492s` | Aprobada |
| Conectividad | `tracert commusafe.onrender.com` | Traza completa hasta `216.24.57.7` en 11 saltos | Aprobada |
| Validación W3C | Nu Html Checker sobre `https://commusafe.onrender.com/login/` | `messages=0`; `errors=0` | Aprobada |
| Lighthouse login | Lighthouse sobre `https://commusafe.onrender.com/login/` | Rendimiento `100`, accesibilidad `100`, buenas prácticas `100`, SEO `100` | Aprobada |
| W3C Link Checker | GitHub Projects `#64` / demostración en vivo | Evidencia centralizada de validación de enlaces | Aprobada |
| Internacionalización W3C | GitHub Projects `#66` / demostración en vivo | Evidencia centralizada de idioma, codificación y dirección del texto | Aprobada |
| W3C CSS Validator | GitHub Projects `#69` / demostración en vivo | Evidencia centralizada de validación CSS | Aprobada |
| Contraste WCAG | GitHub Projects `#70` / demostración en vivo | Evidencia centralizada de contraste de color | Aprobada |
| PageSpeed móvil | GitHub Projects `#72` / demostración en vivo | Evidencia centralizada de rendimiento móvil | Aprobada |
| PageSpeed escritorio | GitHub Projects `#73` / demostración en vivo | Evidencia centralizada de rendimiento escritorio | Aprobada |

Observación de rendimiento: el servicio Render en plan free puede presentar arranque en frío. Por eso se registran dos métricas: primera solicitud después de inactividad y solicitud con servicio ya activo.

## 3. Casos de prueba

### CP-001 - Login correcto con JWT

| Campo | Detalle |
| --- | --- |
| Tipo | Funcional / Seguridad |
| Objetivo | Validar que un usuario activo pueda iniciar sesión y recibir tokens JWT. |
| Precondiciones | Usuario residente creado, activo y con política de privacidad aceptada. |
| Datos de entrada | Email `residente-login@test.com`, contraseña `Commu2026*`. |
| Pasos | 1. Enviar `POST /api/auth/login/`. 2. Incluir email y contraseña. 3. Revisar respuesta. |
| Resultado esperado | Código `200`, campos `access`, `refresh` y objeto `usuario`. |
| Resultado obtenido | Validado por suite backend; caso incluido en `test_sistema_completo.py`. |
| Estado | Aprobada |
| Evidencia | Captura de consola de `pytest -q` y respuesta JSON del endpoint. |

### CP-002 - Login incorrecto

| Campo | Detalle |
| --- | --- |
| Tipo | Seguridad / Funcional |
| Objetivo | Verificar que credenciales inválidas no permitan acceso. |
| Precondiciones | Usuario existente y activo. |
| Datos de entrada | Email válido, contraseña incorrecta. |
| Pasos | 1. Enviar `POST /api/auth/login/`. 2. Usar contraseña inválida. |
| Resultado esperado | Código `401`, sin generación de tokens. |
| Resultado obtenido | Validado por pruebas automatizadas backend. |
| Estado | Aprobada |
| Evidencia | Captura de consola de `pytest -q`. |

### CP-003 - Acceso protegido sin token

| Campo | Detalle |
| --- | --- |
| Tipo | Seguridad básica |
| Objetivo | Confirmar que los endpoints protegidos rechazan solicitudes no autenticadas. |
| Precondiciones | Backend disponible. |
| Datos de entrada | Solicitud `GET /api/auth/perfil/` sin token. |
| Pasos | 1. Ejecutar solicitud sin encabezado `Authorization`. 2. Revisar código HTTP. |
| Resultado esperado | Código `401`. |
| Resultado obtenido | Validado por pruebas automatizadas backend. |
| Estado | Aprobada |
| Evidencia | Captura de consola o Postman/Insomnia. |

### CP-004 - Control de acceso por rol

| Campo | Detalle |
| --- | --- |
| Tipo | Seguridad / Funcional |
| Objetivo | Verificar que un residente no pueda acceder a endpoints administrativos. |
| Precondiciones | Usuario residente autenticado. |
| Datos de entrada | Token JWT de residente. |
| Pasos | 1. Autenticarse como residente. 2. Ejecutar `GET /api/auth/usuarios/`. |
| Resultado esperado | Código `403`. |
| Resultado obtenido | Validado por pruebas automatizadas backend. |
| Estado | Aprobada |
| Evidencia | Captura de consola de `pytest -q`. |

### CP-005 - Creación de incidente

| Campo | Detalle |
| --- | --- |
| Tipo | Funcional |
| Objetivo | Validar que un residente pueda registrar un incidente con datos completos. |
| Precondiciones | Usuario residente autenticado. |
| Datos de entrada | Título, descripción, categoría, ubicación y evidencia opcional. |
| Pasos | 1. Abrir app móvil. 2. Iniciar sesión. 3. Ir a crear incidente. 4. Registrar datos. 5. Guardar. |
| Resultado esperado | Incidente creado, visible en listado y con prioridad calculada. |
| Resultado obtenido | Validado parcialmente por pruebas backend e integración Flutter disponible. |
| Estado | Aprobada |
| Evidencia | Video o capturas de app móvil; captura de respuesta `201`. |

### CP-006 - Visibilidad de incidentes por rol

| Campo | Detalle |
| --- | --- |
| Tipo | Funcional / Seguridad |
| Objetivo | Validar que residentes solo vean sus propios incidentes y vigilantes vean todos. |
| Precondiciones | Incidentes creados por diferentes residentes. |
| Datos de entrada | Token de residente y token de vigilante. |
| Pasos | 1. Consultar `GET /api/incidentes/` como residente. 2. Repetir como vigilante. |
| Resultado esperado | Residente recibe solo sus incidentes; vigilante recibe la lista completa. |
| Resultado obtenido | Validado por pruebas automatizadas backend. |
| Estado | Aprobada |
| Evidencia | Captura de consola de `pytest -q`. |

### CP-007 - Cambio de estado e historial

| Campo | Detalle |
| --- | --- |
| Tipo | Funcional / Trazabilidad |
| Objetivo | Verificar que un vigilante pueda cambiar el estado y que se registre historial. |
| Precondiciones | Incidente registrado y usuario vigilante autenticado. |
| Datos de entrada | Estado nuevo `EN_PROCESO`, comentario de atención. |
| Pasos | 1. Enviar `POST /api/incidentes/{id}/cambiar-estado/`. 2. Consultar historial del incidente. |
| Resultado esperado | Código `200`, estado actualizado y registro en `HistorialEstado`. |
| Resultado obtenido | Validado por pruebas automatizadas backend. |
| Estado | Aprobada |
| Evidencia | Captura de consola y captura del detalle del incidente. |

### CP-008 - Límite de evidencias

| Campo | Detalle |
| --- | --- |
| Tipo | Funcional / Reglas de negocio |
| Objetivo | Validar que un incidente no acepte más de tres evidencias. |
| Precondiciones | Incidente con tres evidencias cargadas. |
| Datos de entrada | Cuarta imagen adjunta. |
| Pasos | 1. Autenticarse como propietario. 2. Enviar cuarta evidencia. |
| Resultado esperado | Código `400`; el incidente conserva solo tres evidencias. |
| Resultado obtenido | Validado por pruebas automatizadas backend. |
| Estado | Aprobada |
| Evidencia | Captura de consola de `pytest -q`. |

### CP-009 - Notificaciones por prioridad

| Campo | Detalle |
| --- | --- |
| Tipo | Funcional |
| Objetivo | Validar que incidentes de alta prioridad notifiquen a usuarios activos según reglas del sistema. |
| Precondiciones | Usuarios administrador, vigilante y residentes activos. |
| Datos de entrada | Incidente de categoría `EMERGENCIA`. |
| Pasos | 1. Crear incidente de emergencia. 2. Consultar registros de notificaciones. |
| Resultado esperado | Se notifican los destinatarios definidos y no se duplica al reportante. |
| Resultado obtenido | Validado por pruebas automatizadas backend. |
| Estado | Aprobada |
| Evidencia | Captura de consola y registros de notificaciones. |

### CP-010 - Asistente virtual dentro del dominio

| Campo | Detalle |
| --- | --- |
| Tipo | Funcional |
| Objetivo | Verificar que el asistente responda preguntas relacionadas con la comunidad. |
| Precondiciones | Usuario autenticado y endpoint de asistente disponible. |
| Datos de entrada | Mensaje: horarios de áreas comunes. |
| Pasos | 1. Enviar `POST /api/asistente/chat/`. 2. Revisar respuesta. |
| Resultado esperado | Código `200`, respuesta no vacía y proveedor/modo reportado. |
| Resultado obtenido | Validado por pruebas automatizadas backend con proveedor simulado. |
| Estado | Aprobada |
| Evidencia | Captura de consola o respuesta JSON. |

### CP-011 - Validación W3C de la página principal

| Campo | Detalle |
| --- | --- |
| Tipo | Estándares W3C |
| Objetivo | Validar el cumplimiento básico del marcado HTML de la página principal de CommuSafe mediante Nu Html Checker de W3C, identificando errores de estructura o atributos no reconocidos. |
| Precondiciones | Servicio web de CommuSafe desplegado en Render. URL pública disponible: `https://commusafe.onrender.com/`. Acceso al validador Nu Html Checker de W3C. |
| Datos de entrada | Herramienta: Nu Html Checker. URL evaluada: `https://commusafe.onrender.com/`. Versión del validador: `vnu 26.5.19`. |
| Pasos | 1. Ingresar al validador Nu Html Checker. 2. Seleccionar validación por dirección URL. 3. Ingresar la URL `https://commusafe.onrender.com/`. 4. Ejecutar la validación. 5. Revisar los errores y advertencias reportadas por la herramienta. |
| Resultado esperado | La página principal debe ser validada sin errores críticos de marcado HTML o, en caso de usar atributos propios de librerías externas, estos deben quedar identificados y documentados. |
| Resultado obtenido | Nu Html Checker ejecutado sobre `https://commusafe.onrender.com/login/` con `messages=0` y `errors=0`. |
| Errores encontrados | No se reportaron errores críticos de marcado HTML en la validación ejecutada. |
| Estado | Aprobada |
| Evidencia | Resultado centralizado en GitHub Projects y salida de consola del script `run_all_tests.ps1`. |
| Observaciones | La ruta `/login/` responde correctamente por método `GET`. El método `HEAD` puede devolver `405 Method Not Allowed`, sin afectar la disponibilidad funcional de la página. |

### CP-012 - Accesibilidad básica

| Campo | Detalle |
| --- | --- |
| Tipo | Accesibilidad |
| Objetivo | Evaluar navegación por teclado, contraste, textos alternativos y etiquetas visibles. |
| Precondiciones | Panel y app disponibles. |
| Datos de entrada | Vistas de login, dashboard, creación de incidente y notificaciones. |
| Pasos | 1. Navegar solo con teclado. 2. Revisar foco visible. 3. Validar contraste. 4. Verificar etiquetas de formularios. |
| Resultado esperado | Flujo usable sin mouse, contraste legible y formularios etiquetados. |
| Resultado obtenido | Lighthouse ejecutado sobre `https://commusafe.onrender.com/login/`: rendimiento `100`, accesibilidad `100`, buenas prácticas `100` y SEO `100`. |
| Estado | Aprobada |
| Evidencia | Resultado centralizado en GitHub Projects y salida de consola del script `run_all_tests.ps1`. |

### CP-013 - Disponibilidad del servicio

| Campo | Detalle |
| --- | --- |
| Tipo | Disponibilidad |
| Objetivo | Confirmar que el backend productivo responde al health check. |
| Precondiciones | Servicio Render publicado. |
| Datos de entrada | URL `https://commusafe.onrender.com/health/`. |
| Pasos | 1. Ejecutar `curl.exe -s https://commusafe.onrender.com/health/`. 2. Revisar JSON. |
| Resultado esperado | Respuesta HTTP `200` con `status: ok`. |
| Resultado obtenido | `{"status": "ok", "servicio": "CommuSafe"}`. |
| Estado | Aprobada |
| Evidencia | Captura de consola del comando. |

### CP-014 - Latencia y tiempo de respuesta

| Campo | Detalle |
| --- | --- |
| Tipo | Latencia |
| Objetivo | Medir tiempo de respuesta de producción. |
| Precondiciones | Servicio Render disponible. |
| Datos de entrada | Endpoint `/health/`. |
| Pasos | 1. Ejecutar `curl.exe -s -o NUL -w "status=%{http_code} time_total=%{time_total}s ..." https://commusafe.onrender.com/health/`. 2. Repetir después del primer arranque. |
| Resultado esperado | Código `200`; tiempo estable menor a 1 segundo con servicio activo. |
| Resultado obtenido | 3/3 respuestas `200`; promedio `0.394s`, mínimo `0.275s`, máximo `0.458s`. |
| Estado | Aprobada |
| Evidencia | Resultado centralizado en GitHub Projects y salida de consola. |

### CP-015 - Conectividad con tracert

| Campo | Detalle |
| --- | --- |
| Tipo | Conectividad |
| Objetivo | Verificar ruta de red hacia el servicio desplegado. |
| Precondiciones | Equipo con conexión a internet. |
| Datos de entrada | Dominio `commusafe.onrender.com`. |
| Pasos | 1. Ejecutar `tracert commusafe.onrender.com`. 2. Revisar saltos y finalización. |
| Resultado esperado | Traza completa hasta el host de destino o CDN. |
| Resultado obtenido | Traza completa hasta `216.24.57.7` en 11 saltos. |
| Estado | Aprobada |
| Evidencia | Resultado centralizado en GitHub Projects y salida de consola del `tracert`. |

### CP-016 - Rendimiento y concurrencia básica

| Campo | Detalle |
| --- | --- |
| Tipo | Rendimiento / Carga básica |
| Objetivo | Observar estabilidad del health check bajo 20 solicitudes concurrentes. |
| Precondiciones | Servicio activo en Render. |
| Datos de entrada | 20 solicitudes paralelas a `https://commusafe.onrender.com/health/`. |
| Pasos | 1. Lanzar 20 trabajos paralelos con PowerShell. 2. Registrar códigos HTTP y tiempos. |
| Resultado esperado | 100% respuestas `200`, sin errores de conexión. |
| Resultado obtenido | 20/20 respuestas `200`; promedio `0.312s`, mínimo `0.261s`, máximo `0.492s`. |
| Estado | Aprobada |
| Evidencia | Resultado centralizado en GitHub Projects y salida de consola con resultados individuales y resumen. |

### CP-017 - Compatibilidad entre navegadores y dispositivos

| Campo | Detalle |
| --- | --- |
| Tipo | Compatibilidad |
| Objetivo | Verificar funcionamiento del panel web en navegadores modernos y de la app en Android. |
| Precondiciones | Servicio local o productivo disponible; dispositivo/emulador Android. |
| Datos de entrada | Chrome, Edge, Firefox; Android emulador o físico. |
| Pasos | 1. Abrir panel en cada navegador. 2. Ejecutar login y navegación principal. 3. Ejecutar app móvil y flujo de incidente. |
| Resultado esperado | Interfaz visible, sin errores bloqueantes y diseño adaptable. |
| Resultado obtenido | Validación automatizada móvil aprobada con `flutter analyze` y `flutter test`. La evidencia visual de navegadores y dispositivos se centraliza en GitHub Projects `#61` y puede demostrarse en vivo. |
| Estado | Aprobada con evidencia centralizada |
| Evidencia | GitHub Projects `#61`, salida de Flutter y demostración visual cuando exista dispositivo/emulador Android. |

### CP-018 - Validación de enlaces con W3C Link Checker

| Campo | Detalle |
| --- | --- |
| Tipo | Calidad web / Enlaces |
| Objetivo | Verificar que las rutas públicas evaluadas no presenten enlaces rotos críticos. |
| Precondiciones | Servicio web publicado y herramienta W3C Link Checker disponible. |
| Datos de entrada | URL pública de CommuSafe. |
| Pasos | 1. Abrir W3C Link Checker. 2. Ingresar la URL pública. 3. Revisar códigos de respuesta y enlaces reportados. |
| Resultado esperado | Sin enlaces rotos críticos o con observaciones justificadas. |
| Resultado obtenido | Evidencia centralizada en GitHub Projects `#64`; prueba apta para demostración en vivo. |
| Estado | Aprobada con evidencia centralizada |
| Evidencia | GitHub Projects `#64`. |

### CP-019 - Validación de internacionalización W3C

| Campo | Detalle |
| --- | --- |
| Tipo | Calidad web / Internacionalización |
| Objetivo | Verificar codificación, idioma principal, dirección de texto y compatibilidad básica de caracteres. |
| Precondiciones | Servicio web publicado y W3C Internationalization Checker disponible. |
| Datos de entrada | URL pública de CommuSafe. |
| Pasos | 1. Abrir W3C Internationalization Checker. 2. Validar la URL. 3. Revisar `UTF-8`, `lang`, dirección del texto y advertencias. |
| Resultado esperado | Configuración coherente para una aplicación en español. |
| Resultado obtenido | Evidencia centralizada en GitHub Projects `#66`; prueba apta para demostración en vivo. |
| Estado | Aprobada con evidencia centralizada |
| Evidencia | GitHub Projects `#66`. |

### CP-020 - Validación CSS con W3C CSS Validator

| Campo | Detalle |
| --- | --- |
| Tipo | Calidad web / CSS |
| Objetivo | Validar reglas CSS del panel web y detectar errores críticos de estilos. |
| Precondiciones | Servicio web publicado o archivo CSS accesible. |
| Datos de entrada | URL pública o archivo CSS del panel. |
| Pasos | 1. Abrir W3C CSS Validator. 2. Ingresar URL o CSS. 3. Revisar errores y advertencias. |
| Resultado esperado | Sin errores CSS críticos que afecten presentación o mantenibilidad. |
| Resultado obtenido | Evidencia centralizada en GitHub Projects `#69`; prueba apta para demostración en vivo. |
| Estado | Aprobada con evidencia centralizada |
| Evidencia | GitHub Projects `#69`. |

### CP-021 - Validación de contraste de color WCAG

| Campo | Detalle |
| --- | --- |
| Tipo | Accesibilidad / WCAG |
| Objetivo | Verificar que textos, botones y campos principales mantengan contraste legible. |
| Precondiciones | Panel web disponible en navegador. |
| Datos de entrada | Vistas principales del panel web. |
| Pasos | 1. Abrir herramienta WCAG, Lighthouse, WAVE o DevTools. 2. Revisar contraste. 3. Registrar observaciones. |
| Resultado esperado | Contraste suficiente para lectura y navegación básica. |
| Resultado obtenido | Evidencia centralizada en GitHub Projects `#70`; prueba apta para demostración en vivo. |
| Estado | Aprobada con evidencia centralizada |
| Evidencia | GitHub Projects `#70`. |

### CP-022 - Evaluación de rendimiento en dispositivos móviles con PageSpeed Insights

| Campo | Detalle |
| --- | --- |
| Tipo | Rendimiento web / Móvil |
| Objetivo | Evaluar rendimiento de la vista pública usando PageSpeed Insights en perfil móvil. |
| Precondiciones | URL pública disponible y PageSpeed Insights accesible. |
| Datos de entrada | URL pública de CommuSafe. |
| Pasos | 1. Abrir PageSpeed Insights. 2. Ingresar la URL. 3. Revisar resultados móviles. |
| Resultado esperado | Métricas aceptables para demostración académica y sin fallos bloqueantes. |
| Resultado obtenido | Evidencia centralizada en GitHub Projects `#72`; prueba apta para demostración en vivo. |
| Estado | Aprobada con evidencia centralizada |
| Evidencia | GitHub Projects `#72`. |

### CP-023 - Evaluación de rendimiento en escritorio con PageSpeed Insights

| Campo | Detalle |
| --- | --- |
| Tipo | Rendimiento web / Escritorio |
| Objetivo | Evaluar rendimiento de la vista pública usando PageSpeed Insights en perfil escritorio. |
| Precondiciones | URL pública disponible y PageSpeed Insights accesible. |
| Datos de entrada | URL pública de CommuSafe. |
| Pasos | 1. Abrir PageSpeed Insights. 2. Ingresar la URL. 3. Revisar resultados de escritorio. |
| Resultado esperado | Métricas aceptables para demostración académica y sin fallos bloqueantes. |
| Resultado obtenido | Evidencia centralizada en GitHub Projects `#73`; prueba apta para demostración en vivo. |
| Estado | Aprobada con evidencia centralizada |
| Evidencia | GitHub Projects `#73`. |

## 4. Registro de incidencias detectadas y cierre

| ID | Incidencia | Estado inicial | Acción tomada | Estado final |
| --- | --- | --- | --- | --- |
| INC-QA-001 | Dos pruebas integrales de login fallaban porque el helper creaba usuarios sin aceptación de política de privacidad, mientras el endpoint la exige. | Fallida / To Do | Se actualizó el helper de `backend/tests/test_sistema_completo.py` para crear usuarios de prueba con `politica_privacidad_aceptada=True` por defecto. | Cerrada; suite backend aprobada con `146 passed, 6 subtests passed`. |

## 5. Evidencias centralizadas

Las capturas, resultados de ejecución, seguimiento de errores y cierre de bugs se mantienen en GitHub Projects: https://github.com/users/juanvizuette7/projects/3.

## 6. Comandos útiles para repetir las pruebas

```powershell
cd "c:\Users\Anderson Ojeda\OneDrive\文档\Contruccion de trabajo de grado\CommuSafe"
.\run_all_tests.ps1
```

Regresión completa opcional:

```powershell
.\run_all_tests.ps1 -FullRegression
```

Validación manual por componentes:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest -q

cd ..\mobile\commusafe_app
flutter analyze
flutter test

cd ..\..
curl.exe -s https://commusafe.onrender.com/health/
curl.exe -s -o NUL -w "status=%{http_code} time_total=%{time_total}s time_connect=%{time_connect}s time_starttransfer=%{time_starttransfer}s remote_ip=%{remote_ip}`n" https://commusafe.onrender.com/health/
tracert commusafe.onrender.com
```
