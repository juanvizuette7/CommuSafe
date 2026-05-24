# CommuSafe

**Plataforma integral de seguridad, convivencia y organización comunitaria para el conjunto residencial Remansos del Norte.**

![Estado](https://img.shields.io/badge/estado-lanzamiento-10B981)
![Backend](https://img.shields.io/badge/backend-Django%204.2-1A1A2E)
![API](https://img.shields.io/badge/API-REST%20%2B%20JWT-0F3460)
![Mobile](https://img.shields.io/badge/mobile-Flutter%20Android-E94560)
![Deploy](https://img.shields.io/badge/deploy-Render%20%2B%20PostgreSQL-16213E)

CommuSafe es un sistema hiperlocal diseñado para centralizar el reporte, atención, seguimiento y cierre de incidentes dentro de Remansos del Norte. La plataforma conecta a residentes, personal de vigilancia y administración mediante una aplicación móvil Android, un panel web administrativo, una API REST segura y un módulo de notificaciones.

El sistema fue construido como producto de software completo: backend en Django, panel web con plantillas y Tailwind, aplicación móvil Flutter, autenticación JWT, control de acceso por roles, notificaciones push con Firebase Cloud Messaging, asistente virtual con IA y despliegue HTTPS en Render con PostgreSQL. La gestión de usuarios se realiza por administración; el acceso público de registro y recuperación de contraseña está deshabilitado en interfaz para mantener control operativo interno.

## Estado Del Producto

CommuSafe se encuentra preparado para operación controlada y presentación académica. El flujo funcional cubre autenticación, gestión de usuarios, reporte de incidentes, evidencias fotográficas, historial de estados, avisos comunitarios, notificaciones, asistente virtual, contactos de emergencia y panel administrativo.

No incluye módulo de cámaras de vigilancia ni integración con CCTV. La cámara del dispositivo se usa únicamente para adjuntar evidencias fotográficas a los reportes de incidentes.

## Problema Que Resuelve

En una comunidad residencial, los reportes de seguridad, convivencia e infraestructura suelen gestionarse por canales dispersos como llamadas, mensajes informales o comunicación verbal. Esto dificulta conocer quién reportó, cuándo se atendió, qué evidencia existe, quién hizo seguimiento y cuál fue el cierre del caso.

CommuSafe resuelve ese problema centralizando el ciclo completo del incidente: registro, clasificación, evidencia, atención, historial, notificación y cierre. El sistema no reemplaza a la administración ni a la vigilancia; les entrega una herramienta trazable para operar con información ordenada, consultar historial y comunicar avisos de forma segmentada.

## Alcance Funcional Cumplido

El alcance implementado corresponde al núcleo operativo del producto:

- Administración de cuentas por rol: residente, vigilante y administrador.
- Inicio de sesión seguro con JWT en la app móvil y sesión protegida en panel web.
- Reporte de incidentes con título, descripción, categoría, ubicación y evidencia fotográfica.
- Clasificación automática de prioridad por reglas de negocio.
- Seguimiento del ciclo de vida del incidente: registrado, en proceso, resuelto y cerrado.
- Historial inmutable de cambios de estado con responsable, fecha y comentario.
- Consulta diferenciada por rol: residentes ven sus propios incidentes; vigilancia y administración ven el conjunto operativo.
- Panel web para dashboard, usuarios, incidentes, perfil de usuarios, avisos, notificaciones, auditoría y exportaciones.
- App móvil Android para reportar, consultar, recibir alertas, usar asistente y llamar líneas de emergencia.
- Notificaciones internas y push con Firebase Cloud Messaging.
- Avisos comunitarios segmentados por audiencia o usuarios específicos.
- Asistente virtual con IA/fallback para consultas de uso y orientación comunitaria.
- Despliegue backend HTTPS en Render con PostgreSQL.

Quedan explícitamente fuera del alcance actual cámaras de vigilancia, integración con hardware de acceso físico, pagos de administración, votaciones de asamblea y analítica avanzada. Esas funcionalidades pueden plantearse como evolución futura sin afectar el núcleo ya entregado.

## Stack Tecnológico

| Capa | Tecnología | Propósito |
|---|---|---|
| Backend | Python 3.11, Django 4.2 | API, lógica de negocio, ORM, panel web y seguridad |
| API REST | Django REST Framework | Endpoints consumidos por Flutter y clientes autenticados |
| Autenticación | SimpleJWT | Access token, refresh token y control de sesión |
| Base de datos local | SQLite | Desarrollo local |
| Base de datos producción | PostgreSQL en Render | Persistencia operativa |
| Panel web | Django Templates, Tailwind CSS, Alpine.js | Administración, vigilancia, usuarios, incidentes y avisos |
| App móvil | Flutter Android | Interfaz para residentes, vigilantes y administradores |
| Estado móvil | Provider | Manejo de sesión, incidentes y notificaciones |
| Navegación móvil | GoRouter | Rutas protegidas y navegación declarativa |
| HTTP móvil | Dio | Cliente API con JWT y refresh automático |
| Notificaciones | Firebase Cloud Messaging, firebase-admin | Push real y alertas internas |
| IA | Google Gemini API con alternativa Anthropic/fallback | Asistente virtual acotado al conjunto |
| Archivos | WhiteNoise, media storage local/Render | Estáticos y evidencias |
| Pruebas | Pytest, coverage, flutter analyze/test | Validación backend y móvil |
| Despliegue | Render, Gunicorn, HTTPS automático | Publicación del backend |

## Arquitectura

CommuSafe usa una arquitectura cliente-servidor modular:

```text
App Flutter Android
  -> HTTPS / JSON / Multipart
  -> Django REST API
  -> PostgreSQL

Panel Web Django
  -> Vistas protegidas por sesión
  -> Misma lógica de dominio
  -> PostgreSQL

Django Backend
  -> Usuarios y roles
  -> Incidentes, evidencias e historial
  -> Notificaciones internas y FCM
  -> Asistente IA
```

Los residentes reportan incidentes desde la app móvil. Vigilantes y administradores pueden consultar todos los casos autorizados, cambiar estados y generar trazabilidad. La administración gestiona usuarios, incidentes, avisos y auditoría desde el panel web. El asistente virtual responde consultas frecuentes del conjunto y deriva a administración cuando la consulta está fuera del alcance.

## Flujo Operativo Principal

El flujo principal del sistema es el ciclo de vida de un incidente:

1. El residente o vigilante inicia sesión en la app móvil.
2. El usuario crea un incidente seleccionando categoría, descripción, ubicación y hasta tres evidencias.
3. El backend guarda el incidente y calcula la prioridad automáticamente.
4. El sistema genera notificaciones para los roles correspondientes.
5. Vigilancia o administración revisa el caso desde la app o el panel web.
6. El responsable cambia el estado agregando un comentario obligatorio.
7. Cada cambio se registra en el historial del incidente.
8. El residente recibe notificación del avance.
9. La administración puede cerrar el incidente cuando el caso queda finalizado.
10. El historial queda disponible para consulta, auditoría y exportación.

Este flujo garantiza trazabilidad: el sistema conserva quién reportó, quién atendió, qué evidencia se adjuntó, cuándo cambió cada estado y cuál fue el comentario operativo de cada transición.

## Roles Del Sistema

| Rol | Acceso móvil | Acceso web | Responsabilidades |
|---|---|---|---|
| Residente | Sí | No | Reportar incidentes, adjuntar evidencia, consultar sus casos, recibir avisos |
| Vigilante | Sí | Sí | Ver incidentes, atender casos, cambiar estado, emitir avisos operativos |
| Administrador | Sí | Sí | Gestionar usuarios, roles, incidentes, avisos, auditoría y métricas |

## Módulos Implementados

- Autenticación con correo, contraseña, JWT, refresh token y política de tratamiento de datos.
- Usuario personalizado con roles, datos de contacto, foto de perfil y token FCM.
- Gestión completa de incidentes con categoría, prioridad automática, estado, responsable y cierre.
- Evidencias fotográficas con límite de hasta tres imágenes por incidente.
- Historial inmutable de cambios de estado.
- Eliminación física de incidentes con registro de trazabilidad y motivo.
- Exportación de historial de incidentes a Excel y PDF desde el panel web.
- Notificaciones internas y push segmentadas por rol.
- Avisos administrativos dirigidos a todos, grupos o usuarios específicos.
- Banner móvil para avisos vigentes.
- Panel web administrativo con dashboard, filtros, usuarios, notificaciones y detalle visual.
- Aplicación móvil con login, incidentes, creación, detalle, alertas, asistente, perfil, ajustes y emergencias.
- Perfil móvil con edición de datos personales, teléfono colombiano y foto.
- Ajustes de experiencia móvil: color, contraste, tamaño de letra e idioma español/inglés.
- Asistente virtual con IA real si existe API key configurada y modo local si no existe.
- Contactos de emergencia reales para Colombia/Pasto.

## Reglas De Negocio Principales

La prioridad del incidente no se define manualmente desde la app ni con IA. Se calcula en el backend mediante reglas determinísticas para garantizar consistencia, trazabilidad y control operativo:

| Categoría | Prioridad automática | Justificación |
|---|---|---|
| Emergencia | Alta | Puede comprometer seguridad o integridad inmediata |
| Seguridad | Alta | Requiere atención prioritaria de vigilancia/administración |
| Convivencia | Media | Afecta convivencia, pero normalmente no implica riesgo inmediato |
| Infraestructura | Baja | Requiere gestión, pero suele permitir programación de atención |

La IA se usa en el asistente virtual para consultas informativas, no para tomar decisiones críticas sobre prioridad o atención de incidentes. Esta separación es intencional: las decisiones operativas sensibles quedan bajo reglas auditables y bajo responsabilidad humana.

Otras reglas implementadas:

- Un incidente puede tener máximo tres evidencias fotográficas.
- El historial de estado es inmutable: se crea, pero no se edita.
- Solo administración puede eliminar incidentes, y la eliminación exige motivo de trazabilidad.
- Residentes no acceden al panel web.
- Vigilantes pueden atender incidentes y emitir avisos operativos según permisos.
- Administradores gestionan usuarios, roles, incidentes, avisos y auditoría.
- Las cuentas son creadas por administración; la recuperación pública de contraseña está oculta en interfaz.

## Correspondencia Con Requerimientos

| Requerimiento | Estado | Evidencia en el sistema |
|---|---|---|
| Autenticación con correo y contraseña | Cumplido | JWT, login móvil, login panel |
| Roles de usuario | Cumplido | Residente, vigilante, administrador |
| Reporte de incidentes | Cumplido | App móvil y API REST |
| Evidencia fotográfica | Cumplido | ImageField, subida multipart, visor web |
| Clasificación automática | Cumplido | Regla en modelo `Incidente.save()` |
| Seguimiento de estados | Cumplido | Cambios con comentario e historial |
| Notificaciones | Cumplido | Internas, conteo, avisos, FCM |
| Panel administrativo | Cumplido | Dashboard, incidentes, usuarios, avisos |
| Gestión de usuarios | Cumplido | Crear, editar, rol, activar, eliminar, perfil |
| Asistente virtual | Cumplido | Chat IA/fallback y health check |
| Contactos de emergencia | Cumplido | Líneas públicas de Colombia/Pasto |
| Exportación de historial | Cumplido | Excel y PDF desde panel |
| Auditoría de eliminación | Cumplido | Modelo `IncidenteEliminado` |
| Despliegue HTTPS | Cumplido | Render con PostgreSQL |

## Metodología Incremental

El desarrollo se organizó bajo el **Modelo de Desarrollo Incremental**. En GitHub Projects se trabajó con 5 sprints macro; cada sprint entregó una parte funcional verificable y se integró sobre el incremento anterior.

| Sprint | Incremento | Resultado funcional |
|---|---|---|
| Sprint 1 | Núcleo del sistema y autenticación | Backend Django, usuario personalizado, roles, JWT, permisos y estructura API |
| Sprint 2 | Gestión de incidentes | Modelos, serializers, endpoints, evidencias, historial, reglas de prioridad y control por rol |
| Sprint 3 | Panel web y notificaciones | Dashboard, usuarios, incidentes, avisos, notificaciones internas y push |
| Sprint 4 | Aplicación móvil e integraciones | Flutter Android, login, incidentes, alertas, perfil, IA, Firebase y contactos de emergencia |
| Sprint 5 | Calidad, despliegue y documentación | Pruebas, correcciones visuales, Render, PostgreSQL, README y preparación de lanzamiento |

Este enfoque permitió validar el producto por incrementos, reducir riesgos técnicos y mantener trazabilidad entre requerimientos, implementación y pruebas.

Cada incremento tuvo un criterio de cierre funcional: debía poder ejecutarse, integrarse con el trabajo anterior y verificarse mediante pruebas o revisión operativa. Por eso el proyecto no se construyó como una entrega monolítica al final, sino como una evolución progresiva: primero el núcleo de autenticación, luego incidentes, después panel y notificaciones, posteriormente app móvil e IA, y finalmente despliegue, pruebas y documentación.

## Decisiones Técnicas Relevantes

- Django se eligió porque permite integrar API REST, ORM, autenticación, panel web y administración de archivos en un mismo backend mantenible.
- Flutter se eligió para construir una app Android con interfaz moderna, navegación protegida y consumo directo de la API.
- PostgreSQL se usa en producción por estabilidad, integridad y compatibilidad con Render.
- JWT se usa en móvil porque permite autenticación stateless y refresh controlado.
- Las reglas de prioridad se implementan en backend para impedir manipulación desde clientes.
- Las evidencias se manejan como archivos asociados al incidente para mantener relación directa entre reporte y soporte visual.
- Firebase Cloud Messaging se usa para push real; si el dispositivo no recibe push, el sistema conserva notificaciones internas consultables.
- El asistente virtual tiene fallback local para que el módulo no falle si no hay API key o si el proveedor IA no responde.
- La recuperación de contraseña existe a nivel técnico, pero está oculta en interfaz porque la operación actual usa cuentas creadas por administración.

## Producción

Backend publicado con HTTPS:

```text
https://commusafe.onrender.com
```

Health check:

```text
GET https://commusafe.onrender.com/health/
```

La configuración de producción está en:

```text
backend/commusafe_backend/settings_prod.py
```

Render usa:

```bash
cd backend && gunicorn commusafe_backend.wsgi:application --bind 0.0.0.0:$PORT --worker-class gthread --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
```

La aplicación móvil de producción se compila con:

```powershell
flutter build apk --release --dart-define=PROD=true
```

Con ese parámetro la app usa la URL pública de Render. En desarrollo, sin `PROD=true`, usa `10.0.2.2:8000` para conectarse al backend local desde el emulador Android.

## Variables De Entorno

El archivo real `backend/.env` no se versiona. Para producción se configuran variables seguras en Render:

| Variable | Uso |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `commusafe_backend.settings_prod` |
| `SECRET_KEY` | Clave secreta de Django |
| `DEBUG` | `False` en producción |
| `ALLOWED_HOSTS` | Dominios permitidos |
| `CSRF_TRUSTED_ORIGINS` | Orígenes HTTPS confiables |
| `DATABASE_URL` | Conexión PostgreSQL administrada por Render |
| `GEMINI_API_KEY` | IA real para asistente virtual |
| `GEMINI_MODEL` | Modelo Gemini configurado |
| `LLM_PROVIDER` | Proveedor activo de IA |
| `FIREBASE_CREDENTIALS_JSON_BASE64` | Configuración segura de Firebase Admin codificada |
| `EMAIL_HOST_USER` | Correo emisor si se reactiva envío SMTP |
| `EMAIL_HOST_PASSWORD` | Contraseña de aplicación SMTP |
| `DEFAULT_FROM_EMAIL` | Remitente del sistema |

Los archivos sensibles como `.env`, `google-services.json` y credenciales de Firebase Admin están excluidos por `.gitignore`.

## Instalación Local Del Backend

Desde la raíz del repositorio:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

En Linux/macOS:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Panel web local:

```text
http://127.0.0.1:8000/login/
```

Los usuarios operativos se crean desde el panel web por un administrador autorizado.

## Instalación Local De La App Android

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat pub get
C:\Users\juanv\flutter\bin\flutter.bat run
```

Si Flutter está en el PATH:

```bash
cd mobile/commusafe_app
flutter pub get
flutter run
```

En entorno local, la app usa:

```text
http://10.0.2.2:8000
```

Para compilar contra producción:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat build apk --release --dart-define=PROD=true
```

APK generado:

```text
mobile/commusafe_app/build/app/outputs/flutter-apk/app-release.apk
```

## Firebase Cloud Messaging

App Android registrada:

```text
com.commusafe.commusafe_app
```

Archivo requerido en entorno local:

```text
mobile/commusafe_app/android/app/google-services.json
```

Configuración Firebase para el backend:

```text
Firebase Console > Project settings > Service accounts > Generate new private key
```

En producción se recomienda usar `FIREBASE_CREDENTIALS_JSON_BASE64` en Render para no almacenar archivos sensibles en el servidor.

## IA Del Asistente Virtual

El asistente se ejecuta con proveedor configurable:

```text
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_API_KEY=<clave real>
```

Si no hay clave, el sistema responde con modo local para preguntas frecuentes sin romper la aplicación. El asistente está limitado a información del conjunto, uso de CommuSafe, normas de convivencia, procedimientos, contactos y orientación operativa.

Información adicional que puede mejorar la precisión del asistente:

- Horarios oficiales de zonas comunes.
- Normas internas de convivencia.
- Procedimiento real para visitantes, domicilios y mudanzas.
- Teléfonos reales de administración y portería.
- Correos o canales oficiales del conjunto.
- Reglamento resumido de mascotas, ruido, parqueaderos y reservas.

El asistente tiene límites definidos: no reemplaza a administración, vigilancia, servicios de emergencia ni asesoría jurídica. Si una consulta excede el conocimiento configurado, debe orientar al usuario a contactar administración o usar las líneas de emergencia según corresponda.

## Contactos De Emergencia En La App

La pantalla móvil de emergencias usa líneas públicas reales para Colombia y operación en Pasto:

| Servicio | Número |
|---|---:|
| Línea única de emergencias | `123` |
| Policía Nacional | `112` |
| Bomberos Pasto / Colombia | `119` |
| Ambulancias / Secretaría de Salud | `125` |
| Cruz Roja Colombiana | `132` |
| Defensa Civil | `144` |

Para emergencias inminentes se prioriza `123`, ya que centraliza la atención de seguridad y emergencia.

## Endpoints Principales

| Método | Ruta | Descripción | Rol |
|---|---|---|---|
| POST | `/api/auth/login/` | Inicio de sesión JWT | Público controlado |
| POST | `/api/auth/refresh/` | Renovación de token | Usuario autenticado |
| GET/PUT | `/api/auth/perfil/` | Consulta y actualización de perfil propio | Usuario autenticado |
| POST | `/api/auth/fcm/` | Registro de token FCM | Usuario autenticado |
| GET/POST | `/api/auth/usuarios/` | Gestión de usuarios | Administrador |
| POST | `/api/auth/usuarios/{id}/activar/` | Activar cuenta | Administrador |
| POST | `/api/auth/usuarios/{id}/desactivar/` | Desactivar cuenta | Administrador |
| POST | `/api/auth/usuarios/{id}/cambiar-rol/` | Cambiar rol | Administrador |
| GET/POST | `/api/incidentes/` | Listar y crear incidentes | Según rol |
| GET | `/api/incidentes/{id}/` | Detalle con evidencias e historial | Según rol |
| DELETE | `/api/incidentes/{id}/` | Eliminar con motivo y trazabilidad | Administrador |
| POST | `/api/incidentes/{id}/cambiar-estado/` | Cambiar estado e historial | Administrador, vigilante |
| POST | `/api/incidentes/{id}/agregar-evidencia/` | Adjuntar evidencia | Según rol |
| GET | `/api/notificaciones/` | Notificaciones propias | Usuario autenticado |
| GET | `/api/notificaciones/no-leidas-count/` | Conteo de no leídas | Usuario autenticado |
| POST | `/api/notificaciones/{id}/leer/` | Marcar como leída | Usuario autenticado |
| POST | `/api/notificaciones/leer-todas/` | Marcar todas como leídas | Usuario autenticado |
| POST | `/api/notificaciones/avisos/` | Crear aviso segmentado | Administrador, vigilante |
| GET | `/api/notificaciones/avisos-vigentes/` | Avisos recientes pendientes | Usuario autenticado |
| POST | `/api/asistente/chat/` | Chat con IA o respuesta local | Usuario autenticado |
| GET | `/api/asistente/health/` | Estado del proveedor IA | Usuario autenticado |

## Pruebas Y Calidad

Backend:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py check
pytest -q
coverage run -m pytest -q
coverage report
```

Flutter:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat analyze
C:\Users\juanv\flutter\bin\flutter.bat test
C:\Users\juanv\flutter\bin\flutter.bat build apk --release --dart-define=PROD=true
```

Validaciones aplicadas:

- Control de acceso por rol.
- Autenticación JWT.
- Reglas de prioridad automática por categoría.
- Historial de cambios de estado.
- Límite de evidencias.
- Notificaciones por rol.
- Renderizado del panel web.
- Compilación Android.
- Pruebas de interfaz móvil base.

Además, la calidad del software se evaluó con base en atributos prácticos alineados con ISO/IEC 25010:

| Atributo | Cómo se cumple en CommuSafe |
|---|---|
| Funcionalidad | Flujos completos de login, incidentes, avisos, notificaciones y perfiles |
| Seguridad | Roles, JWT, sesiones protegidas, HTTPS y variables fuera del repo |
| Usabilidad | App móvil con navegación inferior, panel visual, badges, filtros y estados claros |
| Mantenibilidad | Apps Django separadas, providers Flutter, servicios reutilizables y documentación |
| Confiabilidad | Historial inmutable, reglas backend y PostgreSQL en producción |
| Portabilidad | Backend desplegable en Render y app Android instalable por APK |
| Eficiencia | Consultas paginadas, filtros server-side y endpoints específicos por módulo |

## Estructura Del Repositorio

```text
CommuSafe/
  backend/
    commusafe_backend/     Configuración Django y producción
    usuarios/              Usuario personalizado, roles, JWT y permisos
    incidentes/            Incidentes, evidencias, historial y auditoría
    notificaciones/        Alertas internas, avisos y Firebase
    asistente/             IA, health check y respuestas locales
    panel_web/             Vistas y formularios del panel
    tests/                 Pruebas automatizadas
  frontend/
    templates/             Plantillas HTML del panel web
    static/                CSS y JavaScript del panel
  mobile/
    commusafe_app/         Aplicación Flutter Android
  docs/
    ARQUITECTURA.md
    MODELO_DATOS.md
    MODELO_INCREMENTAL.md
    MATRIZ_CUMPLIMIENTO.md
    PLAN_PRUEBAS_CALIDAD.md
    INSTRUMENTO_USABILIDAD.md
    DESPLIEGUE.md
```

## Seguridad

- Contraseñas cifradas mediante el sistema de autenticación de Django.
- Autenticación JWT para API móvil.
- Refresh token y expiración controlada.
- Control de acceso por rol en backend, panel y app.
- HTTPS automático en Render.
- Variables sensibles fuera del repositorio.
- Evidencias fotográficas servidas bajo rutas de medios controladas.
- Gestión de usuarios centralizada por administración.

## Datos Del Proyecto

| Campo | Valor |
|---|---|
| Sistema | CommuSafe |
| Comunidad objetivo | Remansos del Norte |
| Tipo de proyecto | Trabajo de grado universitario |
| Programa | Ingeniería de Software |
| Año | 2026 |
| Metodología | Modelo de Desarrollo Incremental |
| Despliegue backend | Render con PostgreSQL y HTTPS |
| Aplicación móvil | Android |

## Notas Operativas

- La recuperación de contraseña está oculta en web y móvil porque las cuentas son gestionadas por administración.
- Para crear o modificar usuarios se debe ingresar al panel web con una cuenta administradora.
- Render puede tardar algunos segundos en responder si el servicio estuvo en reposo.
- Los porcentajes de lenguaje en GitHub pueden mostrar HTML por las plantillas del panel web; esto es esperado.
