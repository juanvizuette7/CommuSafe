# Seguridad de credenciales

## Politica del repositorio

CommuSafe no debe versionar claves, tokens, contrasenas, archivos `.env`, credenciales Firebase, archivos `google-services.json`, bases de datos locales, APKs, builds, logs ni reportes temporales.

Los valores reales deben configurarse solo en:

- Variables de entorno locales privadas, por ejemplo `backend/.env`.
- Variables de entorno del proveedor de despliegue, por ejemplo Render.
- Secret files del proveedor de despliegue, si se usa esa alternativa.
- Firebase Console, Google AI Studio o el proveedor correspondiente.

## Archivos protegidos por `.gitignore`

- `backend/.env`
- `backend/.env.*`, excepto `backend/.env.example`
- `backend/firebase-service-account.json`
- `backend/*firebase-adminsdk*.json`
- `mobile/commusafe_app/android/app/google-services.json`
- `backend/db.sqlite3`
- `*.sqlite3`
- `*.apk`, `*.aab`, `*.apks`
- `**/build/`
- `**/.dart_tool/`
- `*.log`
- `**/__pycache__/`
- reportes temporales de Lighthouse, coverage y pruebas

## Variables sensibles esperadas

Estas variables existen por configuracion, pero sus valores reales no deben aparecer en el codigo:

- `SECRET_KEY`
- `JWT_SIGNING_KEY`
- `DATABASE_URL`
- `DB_PASSWORD`
- `GEMINI_API_KEY`
- `LLM_API_KEY`
- `FIREBASE_CREDENTIALS_JSON_BASE64`
- `FIREBASE_CREDENTIALS_JSON`
- `FIREBASE_CREDENTIALS_PATH`
- `FCM_SERVER_KEY`
- `EMAIL_HOST_PASSWORD`
- `PROD_ADMIN_PASSWORD`
- `COMMUSAFE_NLP_SERVICE_KEY`

## Hallazgo de auditoria

Durante la revision se detecto que una API key real de Gemini habia quedado registrada en un commit anterior dentro de pruebas del asistente. El valor ya fue retirado del arbol actual del repositorio y reemplazado por mocks/constantes de prueba.

Accion manual obligatoria: esa API key debe considerarse comprometida y debe revocarse o rotarse en Google AI Studio. No basta con eliminarla del codigo porque ya formo parte del historial Git.

## Verificacion recomendada

Ejecutar antes de cada entrega:

```powershell
git status --short
git check-ignore -v backend/.env backend/firebase-service-account.json mobile/commusafe_app/android/app/google-services.json backend/db.sqlite3
rg -n --hidden --glob '!**/.git/**' --glob '!**/build/**' --glob '!**/.dart_tool/**' "AIza|PRIVATE KEY|postgresql://|DATABASE_URL=|EMAIL_HOST_PASSWORD=|GEMINI_API_KEY=|LLM_API_KEY="
```

Si aparece un valor real, reemplazarlo por una variable de entorno, mock o placeholder vacio antes de hacer commit.
