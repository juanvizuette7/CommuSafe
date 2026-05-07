# Despliegue del backend en Render

Este documento describe el despliegue real del backend de CommuSafe en Render.com con HTTPS automatico, Gunicorn y PostgreSQL administrado.

## 1. Crear cuenta y conectar repositorio

1. Crear una cuenta en `https://render.com`.
2. Entrar al Dashboard de Render.
3. Seleccionar `New` y luego `Blueprint`.
4. Conectar la cuenta de GitHub.
5. Elegir el repositorio `CommuSafe`.
6. Confirmar que Render detecte el archivo `render.yaml` en la raiz del repositorio.

## 2. Servicios definidos por `render.yaml`

El archivo `render.yaml` crea:

1. Un servicio web Python llamado `commusafe`.
2. Una base de datos PostgreSQL llamada `commusafe-db`.

El servicio web ejecuta:

```bash
pip install -r backend/requirements.txt && cd backend && python manage.py migrate && python manage.py crear_admin_produccion && python manage.py collectstatic --noinput
```

Como comando de inicio ejecuta:

```bash
cd backend && gunicorn commusafe_backend.wsgi:application --bind 0.0.0.0:$PORT --worker-class gthread --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
```

## 3. Variables de entorno requeridas

Render configura automáticamente `DATABASE_URL` desde la base de datos PostgreSQL declarada en el Blueprint.

Revisar o crear estas variables en el servicio web:

```env
DJANGO_SETTINGS_MODULE=commusafe_backend.settings_prod
SECRET_KEY=valor_seguro_generado_por_render
DEBUG=False
ALLOWED_HOSTS=.onrender.com,commusafe.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com,https://commusafe.onrender.com
SERVE_MEDIA_FILES=True
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_API_KEY=TU_API_KEY_REAL_DE_GOOGLE_AI_STUDIO
FIREBASE_CREDENTIALS_JSON_BASE64=JSON_BASE64_DE_FIREBASE_ADMIN
PROD_ADMIN_EMAIL=correo_real_del_administrador
PROD_ADMIN_PASSWORD=contrasena_segura_del_administrador
PROD_ADMIN_NOMBRE=Nombre
PROD_ADMIN_APELLIDO=Apellido
PROD_ADMIN_TELEFONO=3000000000
EMAIL_HOST_USER=correo_smtp_real
EMAIL_HOST_PASSWORD=app_password_smtp
DEFAULT_FROM_EMAIL=CommuSafe <correo_smtp_real>
```

No se debe ejecutar `cargar_demo` en produccion. El despliegue real arranca con base limpia y crea solo el administrador indicado por las variables `PROD_ADMIN_*`.

## 4. Configurar IA real

1. Entrar a `https://aistudio.google.com/apikey`.
2. Crear una API key.
3. Pegarla en la variable `GEMINI_API_KEY` del servicio web en Render.
4. Mantener `LLM_PROVIDER=gemini`.
5. Mantener `GEMINI_MODEL=gemini-2.5-flash-lite`.

## 5. Configurar Firebase Admin

1. En Firebase Console abrir el proyecto de CommuSafe.
2. Ir a `Configuración del proyecto`.
3. Entrar a `Cuentas de servicio`.
4. Generar una nueva clave privada.
5. Convertir el archivo JSON a base64 desde PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\ruta\firebase-service-account.json"))
```

6. En Render, abrir el servicio web `commusafe`.
7. Entrar a `Environment`.
8. Crear la variable `FIREBASE_CREDENTIALS_JSON_BASE64` y pegar el texto base64 completo.
9. No subir el archivo JSON al repositorio.

Como alternativa, se puede usar un Secret File y configurar `FIREBASE_CREDENTIALS_PATH=/etc/secrets/firebase-service-account.json`, pero la opcion base64 evita depender de rutas del entorno.

## 6. Desplegar

1. Guardar variables y secret files.
2. Ejecutar `Manual Deploy`.
3. Verificar que el build instale dependencias, ejecute migraciones y recolecte archivos estaticos.
4. Abrir la URL HTTPS asignada por Render.

## 7. Verificación HTTPS

La verificación liviana del servicio es:

```powershell
curl.exe -i https://commusafe.onrender.com/health/
```

La respuesta esperada es `HTTP/2 200` con `{"status":"ok","servicio":"CommuSafe"}`.

Cuando el servicio este publicado, validar desde consola:

```powershell
curl.exe -i https://commusafe.onrender.com/api/auth/login/
```

La respuesta esperada para una peticion `GET` es:

```text
HTTP/2 405
```

Ese estado confirma que la URL HTTPS responde y que el endpoint existe, pero exige `POST` para iniciar sesion.

## 8. Compilar app móvil apuntando a producción

Para que la app Flutter use el backend publicado:

```powershell
cd mobile\commusafe_app
C:\Users\juanv\flutter\bin\flutter.bat build apk --debug --dart-define=PROD=true
```

La app usara:

```text
https://commusafe.onrender.com
```

Si se necesita otra URL de Render, actualizar `baseUrlProduccion` en `AppConstants`.

## 9. Referencias oficiales

- Render Blueprint YAML: `https://render.com/docs/blueprint-spec`
- Django en Render: `https://render.com/docs/deploy-django`
- Variables y secretos en Render: `https://render.com/docs/configure-environment-variables`
