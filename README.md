# CommuSafe

**Plataforma integral de gestión de seguridad y organización comunitaria para Remansos del Norte**

![Estado](https://img.shields.io/badge/estado-listo%20para%20presentaci%C3%B3n-10B981)
![Backend](https://img.shields.io/badge/backend-Django%204.2-1A1A2E)
![Mobile](https://img.shields.io/badge/mobile-Flutter%203.x-0F3460)

CommuSafe es una plataforma digital hiperlocal diseñada para mejorar la gestión de seguridad, convivencia e infraestructura del conjunto residencial Remansos del Norte. El sistema permite que residentes reporten incidentes desde una aplicación móvil, que vigilantes atiendan y actualicen casos en tiempo real, y que administradores gestionen usuarios, reportes, avisos y métricas desde un panel web moderno.

El proyecto se construyó bajo el modelo incremental: cada sprint entregó un incremento funcional integrado con el anterior, desde la arquitectura base hasta las pruebas finales y preparación de presentación. Esta estrategia permite demostrar evolución técnica, trazabilidad, control de riesgos y una integración progresiva entre backend, panel web y aplicación Android.

## Stack Tecnológico

| Tecnología | Versión | Propósito |
|---|---:|---|
| Python | 3.11+ | Lenguaje principal del backend |
| Django | 4.2 | Framework web, ORM, panel administrativo y plantillas |
| Django REST Framework | 3.17.1 | API REST para app móvil y clientes externos |
| SimpleJWT | 5.5.1 | Autenticación por access token y refresh token |
| SQLite | Desarrollo | Base de datos local para pruebas y sustentación |
| PostgreSQL | Producción | Base de datos recomendada para despliegue |
| Tailwind CSS CDN | 3.x | Diseño visual del panel web |
| Alpine.js CDN | 3.x | Interactividad ligera en el panel web |
| Flutter | 3.x | Aplicación móvil Android |
| Dio | 5.9.0 | Cliente HTTP de Flutter |
| Provider | 6.1.5 | Manejo de estado en Flutter |
| GoRouter | 16.2.1 | Navegación declarativa en Flutter |
| Anthropic SDK | 0.96.0 | Integración del asistente virtual con IA |
| PyFCM | 2.1.0 | Servicio base para notificaciones push |
| Pytest / Coverage | 9.0.3 / 7.13.5 | Pruebas automatizadas y cobertura |

## Requisitos Locales

- Windows 10/11, Linux o macOS.
- Python 3.11 o superior.
- Flutter 3.x con Android SDK configurado.
- Android Studio o un emulador Android activo.
- Git.
- Conexión local entre app y backend usando `10.0.2.2:8000` desde el emulador Android.

## Instalación del Backend

Desde la raíz del repositorio:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_demo
python manage.py runserver
```

En Linux o macOS:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_demo
python manage.py runserver
```

El backend queda disponible en:

```text
http://127.0.0.1:8000
```

El panel web queda disponible en:

```text
http://127.0.0.1:8000/login/
```

## Instalación de la App Flutter

En otra terminal, con el backend corriendo:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat pub get
C:\Users\juanv\flutter\bin\flutter.bat run
```

Si `flutter` está configurado en el PATH:

```bash
cd mobile/commusafe_app
flutter pub get
flutter run
```

La app usa como URL base `http://10.0.2.2:8000`, que permite al emulador Android conectarse al backend local.

## Credenciales Demo

| Rol | Correo | Contraseña | Uso principal |
|---|---|---|---|
| Administrador | `admin@remansos.com` | `Admin2026*` | Panel web, gestión completa y app |
| Vigilante | `vigilante1@remansos.com` | `Commu2026*` | Atención de incidentes y avisos |
| Vigilante | `vigilante2@remansos.com` | `Commu2026*` | Atención de incidentes |
| Residente | `residente1@remansos.com` | `Commu2026*` | Reporte y seguimiento de incidentes |
| Residente | `residente2@remansos.com` | `Commu2026*` | Reporte y seguimiento de incidentes |
| Residente | `residente3@remansos.com` | `Commu2026*` | Reporte y seguimiento de incidentes |
| Residente | `residente4@remansos.com` | `Commu2026*` | Reporte y seguimiento de incidentes |
| Residente | `residente5@remansos.com` | `Commu2026*` | Reporte y seguimiento de incidentes |

## Endpoints Principales de la API

| Método | Ruta | Descripción | Rol requerido |
|---|---|---|---|
| POST | `/api/auth/login/` | Inicia sesión y devuelve tokens JWT con datos del usuario | Público |
| POST | `/api/auth/refresh/` | Renueva el access token usando refresh token | Usuario autenticado |
| GET | `/api/auth/perfil/` | Consulta el perfil propio | Usuario autenticado |
| PUT | `/api/auth/perfil/` | Actualiza datos editables del perfil propio | Usuario autenticado |
| POST | `/api/auth/fcm/` | Actualiza el token FCM del dispositivo | Usuario autenticado |
| GET | `/api/auth/usuarios/` | Lista usuarios del sistema | Administrador |
| POST | `/api/auth/usuarios/` | Crea usuarios desde administración | Administrador |
| PUT | `/api/auth/usuarios/{id}/` | Actualiza usuarios | Administrador |
| POST | `/api/auth/usuarios/{id}/activar/` | Activa una cuenta | Administrador |
| POST | `/api/auth/usuarios/{id}/desactivar/` | Desactiva una cuenta | Administrador |
| POST | `/api/auth/usuarios/{id}/cambiar-rol/` | Cambia el rol de una cuenta | Administrador |
| GET | `/api/incidentes/` | Lista incidentes; residentes ven solo los propios | Administrador, vigilante, residente |
| POST | `/api/incidentes/` | Crea un incidente con hasta 3 evidencias | Residente, vigilante |
| GET | `/api/incidentes/{id}/` | Consulta detalle, evidencias e historial | Administrador, vigilante, propietario |
| DELETE | `/api/incidentes/{id}/` | Elimina un incidente | Administrador |
| POST | `/api/incidentes/{id}/cambiar-estado/` | Cambia estado, crea historial y notifica | Administrador, vigilante |
| POST | `/api/incidentes/{id}/agregar-evidencia/` | Adjunta evidencia adicional respetando límite | Administrador, vigilante, propietario |
| GET | `/api/notificaciones/` | Lista notificaciones propias | Usuario autenticado |
| GET | `/api/notificaciones/no-leidas-count/` | Devuelve conteo de no leídas | Usuario autenticado |
| POST | `/api/notificaciones/{id}/leer/` | Marca una notificación como leída | Usuario autenticado |
| POST | `/api/notificaciones/leer-todas/` | Marca todas las notificaciones como leídas | Usuario autenticado |
| POST | `/api/notificaciones/avisos/` | Envía avisos comunitarios segmentados | Administrador, vigilante |
| POST | `/api/asistente/chat/` | Envía mensaje al asistente virtual IA/fallback | Usuario autenticado |

## Pruebas

Backend:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -q
coverage run -m pytest -q
coverage report
```

Flutter:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat analyze
C:\Users\juanv\flutter\bin\flutter.bat test
C:\Users\juanv\flutter\bin\flutter.bat build apk --debug
C:\Users\juanv\flutter\bin\flutter.bat build apk --release
```

APK release generado:

```text
mobile/commusafe_app/build/app/outputs/flutter-apk/app-release.apk
```

## Estructura del Repositorio

```text
CommuSafe/
  backend/
    commusafe_backend/     Configuración Django, URLs y WSGI
    usuarios/              Usuario personalizado, JWT, permisos y CRUD admin
    incidentes/            Reportes, evidencias, historial y reglas de negocio
    notificaciones/        Notificaciones internas, push y avisos comunitarios
    asistente/             Chat con IA y fallback local
    panel_web/             Vistas del panel administrativo
    tests/                 Suite pytest integral del sistema
  frontend/
    templates/             Plantillas Django del panel web
    static/                Archivos estáticos del panel
  mobile/
    commusafe_app/         Aplicación Flutter Android
  docs/
    ARQUITECTURA.md        Arquitectura técnica completa
    MODELO_DATOS.md        Entidades y relaciones
    PLAN_DESARROLLO.md     Ruta incremental por sprints
    DISENO.md              Identidad visual
    MODELO_INCREMENTAL.md  Sustento metodológico incremental
```

## Producción

La configuración de producción está en:

```text
backend/commusafe_backend/settings_prod.py
```

Variables requeridas para producción:

```text
SECRET_KEY
ALLOWED_HOSTS
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
FCM_SERVER_KEY
LLM_API_KEY
```

Comando de despliegue sugerido:

```bash
gunicorn commusafe_backend.wsgi:application --log-file -
```

## Datos del Proyecto

| Campo | Valor |
|---|---|
| Universidad | Proyecto universitario de trabajo de grado |
| Programa | Ingeniería de Software |
| Estudiante | Juan Vizuette |
| Año | 2026 |
| Sistema | CommuSafe |
| Comunidad objetivo | Conjunto residencial Remansos del Norte |
| Metodología | Modelo incremental |
