# Verificación de Producción CommuSafe

Este documento permite comprobar que la configuración real de producción coincide con lo documentado.

## 1. Servicio Render

- Servicio web: `commusafe`
- URL pública: `https://commusafe.onrender.com`
- Runtime: Python
- Plan: free
- Health check: `/health/`

Validación:

```powershell
curl.exe -i https://commusafe.onrender.com/health/
```

Resultado esperado:

```json
{"status":"ok","servicio":"CommuSafe"}
```

## 2. PostgreSQL

La base de datos de producción está declarada en `render.yaml`:

```yaml
databases:
  - name: commusafe-db
    plan: free
    databaseName: commusafe
    user: commusafe
```

El backend usa `DATABASE_URL` en `backend/commusafe_backend/settings_prod.py`:

```python
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        conn_max_age=600,
        ssl_require=True,
    )
}
```

Esto confirma que SQLite queda solo para desarrollo local y PostgreSQL se usa en producción.

## 3. Variables Sensibles

Las credenciales reales no están versionadas. Deben vivir en Render como variables de entorno:

- `SECRET_KEY`
- `DATABASE_URL`
- `GEMINI_API_KEY`
- `FIREBASE_CREDENTIALS_JSON_BASE64`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `PROD_ADMIN_EMAIL`
- `PROD_ADMIN_PASSWORD`

## 4. Comprobación del Repositorio

Desde la raíz del proyecto:

```powershell
git status
git check-ignore -v backend/.env backend/firebase-service-account.json mobile/commusafe_app/android/app/google-services.json backend/db.sqlite3
```

El primer comando debe indicar que no hay cambios pendientes. El segundo debe mostrar que esos archivos sensibles están protegidos por `.gitignore`.

## 5. Comprobación Técnica Local

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest -q
```

Resultado esperado:

- `System check identified no issues`
- Pruebas automatizadas pasando
