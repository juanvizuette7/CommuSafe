# CommuSafe

**Plataforma integral de seguridad, convivencia y organizacion comunitaria para el conjunto residencial Remansos del Norte.**

![Estado](https://img.shields.io/badge/estado-lanzamiento-10B981)
![Backend](https://img.shields.io/badge/backend-Django%204.2-1A1A2E)
![API](https://img.shields.io/badge/API-REST%20%2B%20JWT-0F3460)
![Mobile](https://img.shields.io/badge/mobile-Flutter%20Android-E94560)
![Deploy](https://img.shields.io/badge/deploy-Render%20%2B%20Neon-16213E)

CommuSafe es un sistema hiperlocal para apoyar la gestion de seguridad, convivencia y organizacion operativa del conjunto residencial Remansos del Norte. El producto permite registrar incidentes, adjuntar evidencias fotograficas, hacer seguimiento por estados, notificar a los actores correspondientes, emitir avisos comunitarios y consultar informacion mediante un asistente virtual especializado.

El sistema esta construido como una solucion cliente-servidor: un backend Django expone una API REST segura, un panel web administrativo permite gestionar la operacion desde navegador y una aplicacion movil Flutter Android facilita el uso diario por residentes, vigilantes y administracion. En produccion, el backend Django y el panel web se alojan en Render con HTTPS automatico, mientras la base de datos PostgreSQL se aloja de forma administrada en Neon.

## Que Es CommuSafe

CommuSafe centraliza informacion que normalmente se pierde en llamadas, chats informales o reportes verbales. Cada incidente queda registrado con responsable, fecha, categoria, prioridad, estado, evidencia, historial y cierre. Esto mejora la trazabilidad y permite que administracion y vigilancia tengan una vista clara de lo que ocurre en el conjunto.

El sistema no reemplaza la labor humana de vigilancia o administracion. Su objetivo es ordenar la informacion, acelerar la comunicacion y dejar evidencia verificable de cada proceso operativo.

La recuperación segura de una base PostgreSQL nueva se documenta en `docs/RECUPERACION_BASE_DATOS.md`. El comando `reconstruir_base_segura` es idempotente y no elimina ni sobrescribe registros existentes.

## Caracteristicas Principales

### Gestion De Usuarios Y Seguridad

- Usuario personalizado con inicio de sesion por correo electronico.
- Roles diferenciados: residente, vigilante y administrador.
- Autenticacion JWT para la API movil.
- Sesiones protegidas para el panel web.
- Control de acceso por rol en backend, app movil y panel web.
- Perfil con datos de contacto, foto, unidad o referencia operativa.
- Gestion administrativa de usuarios: crear, editar, activar, desactivar, cambiar rol y eliminar.

### Gestion De Incidentes

- Registro de incidentes desde la app movil.
- Campos principales: titulo, descripcion, categoria, ubicacion y evidencia.
- Categorias: seguridad, convivencia, infraestructura y emergencia.
- Prioridad calculada automaticamente en backend.
- Estados: registrado, en proceso, resuelto y cerrado.
- Historial inmutable de cambios de estado.
- Evidencias fotograficas con limite de hasta tres imagenes por incidente.
- Eliminacion de incidentes con trazabilidad, responsable, fecha y motivo.
- Exportacion del historial a Excel y PDF desde el panel web.

### Notificaciones Y Avisos

- Notificaciones internas consultables desde app movil y panel web.
- Push real mediante Firebase Cloud Messaging.
- Avisos comunitarios emitidos por administracion o vigilancia.
- Seleccion de destinatarios por rol o usuarios especificos.
- Avisos vigentes destacados en la pantalla principal movil.
- Conteo de notificaciones no leidas.

### Panel Web Administrativo

- Dashboard con metricas operativas.
- Listado de incidentes con filtros, busqueda y badges visuales.
- Detalle completo de incidente con evidencias, historial y cambio de estado.
- Gestion de usuarios con perfil individual.
- Visualizacion ordenada de fotos de perfil y evidencias.
- Modulo de avisos y notificaciones.
- Auditoria de incidentes eliminados.
- Exportacion de reportes administrativos.

### Aplicacion Movil Android

- Login seguro con JWT.
- Lista de incidentes segun rol.
- Creacion de reportes con camara o galeria para evidencias.
- Detalle de incidente con informacion, reportante, historial y evidencias.
- Alertas y notificaciones.
- Asistente virtual conversacional.
- Contactos de emergencia.
- Perfil editable con foto y telefono.
- Ajustes visuales: color principal, contraste, tamano de texto e idioma.

### Asistente Virtual

- Asistente conversacional orientado al contexto de Remansos del Norte.
- Conversaciones persistentes por usuario.
- Historial de mensajes almacenado en base de datos.
- Base de conocimiento local con 108 FAQ verificables agrupadas en 20 intenciones principales.
- Base de conocimiento administrable desde Django Admin con revisión, aprobación, vigencia, desactivación, versionado y auditoría por responsable.
- Detección de consultas frecuentes sin respuesta para convertir necesidades reales en nuevo conocimiento verificado.
- Motor local-first con busqueda exacta, normalizacion, palabras clave, similitud TF-IDF, clasificacion de intencion, cache, reglas de negocio, umbrales de confianza y respuestas seguras.
- Gemini o Anthropic funcionan solo como respaldo controlado: nunca son la primera opcion y solo se usan ante baja confianza local dentro del dominio.
- Control de uso IA con cuotas por hora/dia, limite diario de tokens, timeout, validacion anti-invencion y respuesta segura si el proveedor falla.
- Servicio Flask auxiliar opcional para inferencia local por HTTP, evaluacion, reentrenamiento logico y seleccion de respuestas.
- Logs tecnicos de modo, proveedor, intencion, confianza, latencia, tokens estimados y ahorro de tokens por resolver localmente.
- Evaluacion automatizada del asistente con precision, recall, F1, cobertura local y matriz de confusion resumida.
- Estrategia verificable de aceptación, seguridad, resiliencia, carga, latencia, consumo de tokens y persistencia del asistente.
- Dataset profesional de comprension de intenciones con 720 ejemplos balanceados en entrenamiento, validacion y prueba.
- Comparacion reproducible de modelos locales: baseline por palabras clave, TF-IDF por palabra, TF-IDF por caracteres, ensambles y motor hibrido de produccion.

## Arquitectura Usada

CommuSafe usa una arquitectura cliente-servidor con backend modular y API REST.

```text
Aplicacion Flutter Android
  -> HTTPS
  -> JSON / Multipart
  -> Django REST Framework
  -> PostgreSQL

Panel Web Administrativo
  -> Django Templates
  -> Sesion protegida
  -> Servicios internos del backend
  -> PostgreSQL

Backend Django
  -> Usuarios y autenticacion
  -> Incidentes y evidencias
  -> Historial y auditoria
  -> Notificaciones y Firebase
  -> Asistente virtual e IA
  -> Panel web administrativo
```

La arquitectura se organiza como un monolito modular. Cada app de Django tiene una responsabilidad clara: usuarios, incidentes, notificaciones, asistente y panel web. Esto simplifica el despliegue y mantiene separada la logica de negocio.

## Flujo Principal Del Sistema

1. Un residente o vigilante inicia sesion en la app movil.
2. El usuario registra un incidente con categoria, descripcion, ubicacion y evidencias.
3. El backend guarda el reporte y calcula la prioridad automaticamente.
4. El sistema genera notificaciones segun rol, categoria y prioridad.
5. Vigilancia o administracion revisa el caso desde la app o el panel web.
6. El responsable cambia el estado agregando comentario obligatorio.
7. El sistema crea un registro inmutable en el historial.
8. El residente recibe notificacion del avance.
9. El caso puede quedar resuelto o cerrado.
10. La informacion queda disponible para consulta, auditoria y exportacion.

## Reglas De Negocio Principales

La prioridad no se decide desde la interfaz ni por IA. Se calcula en backend con reglas auditables:

| Categoria | Prioridad | Criterio |
|---|---|---|
| Emergencia | Alta | Puede afectar seguridad o integridad inmediata |
| Seguridad | Alta | Requiere atencion prioritaria de vigilancia |
| Convivencia | Media | Afecta la convivencia, sin riesgo inmediato habitual |
| Infraestructura | Baja | Requiere gestion, pero normalmente puede programarse |

Otras reglas implementadas:

- Un incidente acepta maximo tres evidencias fotograficas.
- El historial de estado no se edita ni se elimina desde la API.
- Solo administracion puede eliminar incidentes.
- Toda eliminacion de incidente exige motivo de trazabilidad.
- Residentes ven sus propios incidentes en la lista principal.
- Alertas de prioridad alta de otros residentes llegan por notificacion, pero no se mezclan en la lista principal.
- Vigilantes y administradores pueden consultar y atender incidentes segun permisos.

## Roles Del Sistema

| Rol | App movil | Panel web | Responsabilidades |
|---|---|---|---|
| Residente | Si | No | Reportar incidentes, consultar sus casos, recibir avisos y alertas |
| Vigilante | Si | Si | Atender incidentes, cambiar estados y emitir avisos operativos |
| Administrador | Si | Si | Gestionar usuarios, incidentes, avisos, auditoria y metricas |

## Tecnologias Utilizadas

| Capa | Tecnologia | Uso |
|---|---|---|
| Lenguaje backend | Python 3.11 | Desarrollo del servidor |
| Framework backend | Django 4.2 | Modelos, ORM, seguridad, panel y configuracion |
| API REST | Django REST Framework | Endpoints consumidos por Flutter |
| Autenticacion | SimpleJWT | Access token y refresh token |
| Base local | SQLite | Desarrollo local |
| Base produccion | PostgreSQL en Neon | Persistencia real |
| Variables de entorno | python-decouple | Configuracion segura |
| CORS | django-cors-headers | Acceso desde app movil y clientes externos |
| Filtros API | django-filter | Filtros avanzados en endpoints |
| Archivos | Pillow, ImageField | Fotos de perfil y evidencias |
| Estaticos | WhiteNoise | Servicio de archivos estaticos |
| Produccion | Gunicorn | Servidor WSGI en Render |
| DB URL | dj-database-url | Conexion PostgreSQL por `DATABASE_URL` |
| Push backend | firebase-admin | Envio de FCM desde Django |
| IA | google-genai, Anthropic | Asistente virtual |
| NLP auxiliar | Flask | Servicio local opcional de inferencia del asistente |
| Exportaciones | openpyxl, reportlab | Excel y PDF |
| Pruebas backend | pytest, pytest-django, coverage, factory-boy | Validacion automatizada |
| Panel web | Django Templates | Interfaz administrativa |
| Estilos web | Tailwind CSS, Alpine.js | Diseno moderno e interactividad ligera |
| App movil | Flutter 3.x / Dart | Aplicacion Android |
| Estado movil | Provider | Manejo de estado |
| Navegacion movil | GoRouter | Rutas protegidas |
| HTTP movil | Dio | Cliente API e interceptores JWT |
| Storage movil | Flutter Secure Storage | Almacenamiento seguro de tokens |
| Imagenes movil | image_picker, cached_network_image | Camara, galeria y cache |
| Notificaciones movil | firebase_messaging, flutter_local_notifications | Push y notificaciones locales |
| Utilidades movil | intl, url_launcher, shimmer, badges, google_fonts | Fechas, llamadas, UI y carga visual |
| Despliegue | Render + Neon | Backend HTTPS y PostgreSQL |

## Modulos Del Backend

| App Django | Responsabilidad |
|---|---|
| `commusafe_backend` | Configuracion general, rutas principales, settings local y produccion |
| `usuarios` | Usuario personalizado, roles, permisos, JWT, perfil y FCM token |
| `incidentes` | Incidentes, evidencias, historial, auditoria, exportaciones y reglas de negocio |
| `notificaciones` | Notificaciones internas, avisos, FCM y segmentacion |
| `asistente` | Conversaciones, mensajes, base de conocimiento e integracion IA |
| `panel_web` | Dashboard, vistas web, formularios, usuarios, incidentes, avisos y notificaciones |
| `tests` | Pruebas integrales del sistema |

## Modulos De La App Movil

| Carpeta | Responsabilidad |
|---|---|
| `core/constants` | URLs, endpoints y constantes globales |
| `core/services` | API, storage seguro, Firebase, navegacion y notificaciones |
| `core/theme` | Tema visual, colores, tipografia y configuracion dinamica |
| `core/localization` | Soporte de idioma en la interfaz |
| `features/auth` | Login, perfil, edicion de datos y sesion |
| `features/incidentes` | Lista, creacion, detalle y cambio de estado |
| `features/notificaciones` | Alertas, avisos y conteo de no leidas |
| `features/asistente` | Chat conversacional persistente |
| `features/emergencias` | Contactos de emergencia |
| `features/ajustes` | Preferencias visuales y accesibilidad |
| `shared/layouts` | Layout principal con navegacion |
| `shared/widgets` | Componentes reutilizables |

## Estructura De Carpetas

```text
CommuSafe/
  README.md
  render.yaml
  run_all_tests.ps1
  package.json
  tailwind.config.js
  .gitignore
  .gitattributes
  backend/
    manage.py
    requirements.txt
    Procfile
    pytest.ini
    commusafe_backend/
      settings.py
      settings_prod.py
      urls.py
      wsgi.py
      asgi.py
    usuarios/
      models.py
      serializers.py
      views.py
      permissions.py
      urls.py
      admin.py
      forms.py
      services.py
      management/
      migrations/
    incidentes/
      models.py
      serializers.py
      views.py
      services.py
      services_eliminacion.py
      exporters.py
      filters.py
      permissions.py
      urls.py
      admin.py
      management/
      migrations/
    notificaciones/
      models.py
      serializers.py
      views.py
      services.py
      urls.py
      admin.py
      migrations/
    asistente/
      models.py
      serializers.py
      views.py
      services.py
      knowledge_base.py
      local_knowledge.py
      taxonomy.py
      local_engine.py
      training_dataset.py
      evaluation.py
      model_selection.py
      nlp_flask_service.py
      urls.py
      admin.py
      management/
      migrations/
    panel_web/
      views.py
      urls.py
      forms.py
      context_processors.py
      decorators.py
      templatetags/
      migrations/
    tests/
      test_sistema_completo.py
    media/
      incidentes/
      usuarios/
    staticfiles/
  frontend/
    templates/
      base.html
      panel/
        base.html
        login.html
        dashboard.html
        incidentes_lista.html
        incidente_detalle.html
        incidentes_eliminados.html
        usuarios_lista.html
        usuario_detalle.html
        usuario_form.html
        avisos.html
        notificaciones.html
        notificacion_detalle.html
        politica_privacidad.html
  mobile/
    commusafe_app/
      pubspec.yaml
      android/
      assets/
      lib/
        main.dart
        app.dart
        core/
          constants/
          localization/
          services/
          theme/
        features/
          ajustes/
          asistente/
          auth/
          emergencias/
          incidentes/
          notificaciones/
        shared/
          layouts/
          widgets/
      test/
      integration_test/
  docs/
    ARQUITECTURA.md
    MODELO_DATOS.md
    MODELO_INCREMENTAL.md
    PLAN_DESARROLLO.md
    DISENO.md
    DESPLIEGUE.md
    ASISTENTE_HIBRIDO.md
    MEJORA_ACADEMICA_ASISTENTE_HIBRIDO.md
    GUIA_DEMO_ASISTENTE_HIBRIDO.md
    AUDITORIA_ASISTENTE_VIRTUAL.md
    CHECKLIST_ENTREGA.md
    GUION_DEMO.md
    MATRIZ_CUMPLIMIENTO.md
    PLAN_PRUEBAS_CALIDAD.md
    INSTRUMENTO_USABILIDAD.md
    VERIFICACION_PRODUCCION.md
```

## Endpoints Principales

| Metodo | Ruta | Descripcion | Acceso |
|---|---|---|---|
| `POST` | `/api/auth/login/` | Inicio de sesion JWT | Publico controlado |
| `POST` | `/api/auth/refresh/` | Renovar access token | Usuario autenticado |
| `GET/PUT` | `/api/auth/perfil/` | Perfil propio | Usuario autenticado |
| `POST` | `/api/auth/fcm/` | Actualizar token FCM | Usuario autenticado |
| `GET/POST` | `/api/auth/usuarios/` | Gestion de usuarios | Administrador |
| `GET/POST` | `/api/incidentes/` | Listar o crear incidentes | Segun rol |
| `GET` | `/api/incidentes/{id}/` | Detalle con evidencias e historial | Segun rol |
| `POST` | `/api/incidentes/{id}/cambiar-estado/` | Cambiar estado | Administrador, vigilante |
| `POST` | `/api/incidentes/{id}/agregar-evidencia/` | Adjuntar evidencia | Segun rol |
| `DELETE` | `/api/incidentes/{id}/` | Eliminar con trazabilidad | Administrador |
| `GET` | `/api/notificaciones/` | Notificaciones propias | Usuario autenticado |
| `GET` | `/api/notificaciones/no-leidas-count/` | Conteo de no leidas | Usuario autenticado |
| `POST` | `/api/notificaciones/avisos/` | Crear aviso segmentado | Administrador, vigilante |
| `GET` | `/api/notificaciones/avisos-vigentes/` | Avisos pendientes recientes | Usuario autenticado |
| `POST` | `/api/asistente/chat/` | Mensaje rapido al asistente | Usuario autenticado |
| `GET` | `/api/asistente/conversaciones/` | Listar conversaciones | Usuario autenticado |
| `POST` | `/api/asistente/conversaciones/` | Crear conversacion | Usuario autenticado |
| `GET` | `/api/asistente/conversaciones/{id}/mensajes/` | Mensajes de una conversacion | Usuario autenticado |
| `POST` | `/api/asistente/conversaciones/{id}/enviar/` | Enviar mensaje y recibir respuesta | Usuario autenticado |
| `GET` | `/api/asistente/health/` | Estado del proveedor IA | Usuario autenticado |

## Produccion

Backend y panel web alojados en Render:

```text
https://commusafe.onrender.com
```

Health check:

```text
GET https://commusafe.onrender.com/health/
```

Base de datos de produccion:

```text
PostgreSQL administrado en Neon mediante DATABASE_URL privada
```

Configuracion de produccion:

```text
backend/commusafe_backend/settings_prod.py
```

Comando de arranque en Render:

```bash
cd backend && gunicorn commusafe_backend.wsgi:application --bind 0.0.0.0:$PORT
```

La app Android de produccion se compila con:

```powershell
cd mobile\commusafe_app
flutter build apk --release --dart-define=PROD=true
```

## Variables De Entorno

El archivo real `backend/.env` no debe versionarse. En produccion las variables se configuran en Render.

| Variable | Proposito |
|---|---|
| `DJANGO_SETTINGS_MODULE` | Usar `commusafe_backend.settings_prod` |
| `SECRET_KEY` | Clave secreta de Django |
| `DEBUG` | `False` en produccion |
| `ALLOWED_HOSTS` | Dominios permitidos |
| `CSRF_TRUSTED_ORIGINS` | Origenes HTTPS confiables |
| `DATABASE_URL` | Conexion PostgreSQL privada de Neon |
| `GEMINI_API_KEY` | IA real para el asistente |
| `GEMINI_MODEL` | Modelo Gemini activo |
| `LLM_PROVIDER` | Proveedor IA configurado |
| `LLM_API_KEY` | Alternativa Anthropic |
| `LLM_BACKUP_ENABLED` | Activa o desactiva el respaldo generativo |
| `LLM_TIMEOUT_SECONDS` | Tiempo maximo de espera para Gemini/Anthropic |
| `LLM_MAX_OUTPUT_TOKENS` | Maximo de tokens de salida generativa |
| `LLM_HOURLY_REQUEST_LIMIT` | Limite de consultas IA por hora |
| `LLM_DAILY_REQUEST_LIMIT` | Limite de consultas IA por dia |
| `LLM_DAILY_TOKEN_LIMIT` | Limite diario de tokens estimados en IA |
| `FIREBASE_CREDENTIALS_JSON_BASE64` | Credenciales Firebase Admin codificadas |
| `COMMUSAFE_NLP_SERVICE_URL` | URL opcional del servicio Flask auxiliar, por ejemplo `http://127.0.0.1:5055` |
| `COMMUSAFE_NLP_SERVICE_KEY` | Clave opcional para proteger el servicio Flask auxiliar |
| `COMMUSAFE_NLP_SERVICE_TIMEOUT` | Timeout corto para que Django vuelva al motor interno si Flask no responde |
| `COMMUSAFE_NLP_HOST` | Host del servicio Flask auxiliar; por defecto `127.0.0.1` |
| `COMMUSAFE_NLP_PORT` | Puerto opcional del servicio Flask auxiliar |
| `EMAIL_HOST_USER` | Correo emisor si se activa SMTP |
| `EMAIL_HOST_PASSWORD` | Password de aplicacion SMTP |
| `DEFAULT_FROM_EMAIL` | Remitente del sistema |

Archivos sensibles como `.env`, credenciales Firebase, `google-services.json`, APKs generados y bases de datos locales no deben exponerse en el repositorio publico. La politica completa esta documentada en `docs/SEGURIDAD_CREDENCIALES.md`.

## Instalacion Local Del Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Panel web local:

```text
http://127.0.0.1:8000/login/
```

## Instalacion Local De La App Movil

```powershell
cd mobile\commusafe_app
flutter pub get
flutter run
```

En desarrollo, la app usa `http://10.0.2.2:8000` para conectarse al backend local desde el emulador Android.

## Pruebas Y Verificacion

Backend:

```powershell
cd backend
python manage.py check
pytest -q
coverage run -m pytest -q
coverage report
```

Asistente virtual:

```powershell
cd backend
python manage.py probar_asistente "Como reporto un incidente?"
python manage.py generar_dataset_asistente
python manage.py evaluar_asistente_local
python manage.py evaluar_modelos_asistente --json ..\docs\evidencias\asistente_modelos.json --markdown ..\docs\evidencias\asistente_modelos.md
python manage.py validar_base_conocimiento
python -m pytest asistente/tests.py -q
```

Servicio Flask auxiliar del asistente:

```powershell
cd backend
python -m asistente.nlp_flask_service
```

```powershell
curl -X POST http://127.0.0.1:5055/v1/infer -H "Content-Type: application/json" -d "{\"mensaje\":\"Como reporto un incidente?\",\"rol\":\"RESIDENTE\",\"incluir_candidatos\":true}"
```

Para usarlo desde Django sin reemplazar el motor interno:

```env
COMMUSAFE_NLP_SERVICE_URL=http://127.0.0.1:5055
COMMUSAFE_NLP_SERVICE_KEY=CLAVE_INTERNA_SEGURA
COMMUSAFE_NLP_SERVICE_TIMEOUT=2.5
```

Si el servicio Flask se cae o no responde, Django continua con el motor local embebido.

Flutter:

```powershell
cd mobile\commusafe_app
flutter analyze
flutter test
flutter build apk --release --dart-define=PROD=true
```

Validaciones cubiertas:

- Autenticacion y refresh token.
- Control de acceso por rol.
- Creacion y consulta de incidentes.
- Reglas de prioridad automatica.
- Historial de estados.
- Limite de evidencias.
- Notificaciones segmentadas.
- Asistente virtual hibrido local-first, persistencia, logs y metricas.
- Panel web y rutas protegidas.
- Compilacion Android.

## Calidad Del Software

CommuSafe se construyo considerando atributos de calidad alineados con ISO/IEC 25010:

| Atributo | Aplicacion en CommuSafe |
|---|---|
| Funcionalidad | Flujos completos de incidentes, usuarios, avisos, notificaciones e IA |
| Seguridad | JWT, roles, sesiones protegidas, HTTPS y variables externas |
| Usabilidad | App movil con navegacion clara, panel visual, filtros y estados visibles |
| Mantenibilidad | Apps Django separadas, providers Flutter y servicios reutilizables |
| Confiabilidad | Historial inmutable, reglas backend y PostgreSQL |
| Portabilidad | Backend desplegable en Render y APK Android instalable |
| Eficiencia | Paginacion, filtros y endpoints por modulo |

## Metodologia Incremental

El proyecto se desarrollo bajo el Modelo de Desarrollo Incremental. El sistema no se construyo como una entrega unica al final, sino como una evolucion por incrementos funcionales.

| Incremento | Resultado |
|---|---|
| 1. Nucleo y autenticacion | Proyecto Django, usuario personalizado, roles, JWT y permisos |
| 2. Incidentes | Modelos, API, evidencias, historial y reglas de prioridad |
| 3. Panel web y notificaciones | Dashboard, gestion web, avisos, notificaciones y FCM |
| 4. App movil e IA | Flutter Android, perfil, incidentes, alertas, asistente y emergencias |
| 5. Calidad y despliegue | Pruebas, refinamiento visual, backend en Render, PostgreSQL en Neon y documentacion |

Cada incremento paso por analisis, diseno, implementacion, pruebas e integracion con lo ya construido. Esto permite demostrar avance verificable, trazabilidad tecnica y coherencia con la metodologia seleccionada para el trabajo de grado.

## Seguridad Y Privacidad

- Las contrasenas se gestionan mediante el sistema seguro de Django.
- La API movil usa JWT.
- El panel web usa sesion autenticada.
- El backend valida permisos por rol.
- HTTPS esta activo en produccion.
- Las variables sensibles no se documentan con valores reales.
- Las evidencias quedan asociadas a incidentes y usuarios autenticados.
- La politica de tratamiento de datos esta contemplada en el flujo del sistema.

## Alcance Actual Y Limites

Implementado:

- Usuarios por rol.
- Reporte y seguimiento de incidentes.
- Evidencias fotograficas.
- Notificaciones y avisos.
- Panel web administrativo.
- App movil Android.
- Asistente virtual.
- Contactos de emergencia.
- Despliegue HTTPS.
- PostgreSQL en produccion.

Fuera del alcance actual:

- Camaras de vigilancia o CCTV.
- Integracion con hardware de acceso fisico.
- Pagos de administracion.
- Votaciones de asamblea.
- Analitica avanzada con graficas predictivas.

La camara del celular solo se usa para adjuntar evidencias fotograficas a reportes de incidentes.

## Datos Del Proyecto

| Campo | Valor |
|---|---|
| Sistema | CommuSafe |
| Comunidad objetivo | Remansos del Norte |
| Tipo de proyecto | Trabajo de grado universitario |
| Programa | Ingenieria de Software |
| Metodologia | Modelo de Desarrollo Incremental |
| Backend | Django REST Framework |
| App movil | Flutter Android |
| Panel web | Django Templates, Tailwind CSS y Alpine.js |
| Produccion | Backend y panel web en Render; PostgreSQL en Neon; HTTPS |
| Ano | 2026 |

## Cierre

CommuSafe fue desarrollado como una solucion academica y funcional para demostrar como la ingenieria de software puede aportar orden, trazabilidad y comunicacion efectiva a una comunidad residencial real.

**👨‍💻 Desarrollado por Juan Vizuette y el equipo del proyecto CommuSafe.**
