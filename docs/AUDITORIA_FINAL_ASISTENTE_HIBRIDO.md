# Auditoria final del asistente hibrido CommuSafe

Fecha de auditoria: 10 de junio de 2026.

## Dictamen

El asistente es funcional, mantiene conversaciones aisladas por usuario, responde primero con conocimiento local y conserva Gemini como respaldo controlado. La arquitectura es defendible para un trabajo de grado y para una operacion comunitaria de alcance reducido.

No debe presentarse como un sistema que comprende cualquier redaccion ni como un modelo con generalizacion universal. El holdout final no ajustado obtuvo 55.00 % de precision micro. El comportamiento restante es conservador: ante lenguaje indirecto prefiere aclarar, responder de forma segura o habilitar respaldo antes que afirmar algo incorrecto.

## Hallazgos corregidos

| Hallazgo | Riesgo | Correccion verificable |
|---|---|---|
| Metricas mezclaban consultas reales y ejecuciones tecnicas | Inflar cobertura local y ahorro de tokens | `metricas_uso_asistente()` filtra usuarios autenticados por defecto; el demo genera resumen aislado |
| Health detallado visible para vigilancia | Exposicion innecesaria de modelo, cuotas, cache y metricas | Solo administradores y staff reciben diagnostico detallado |
| Health Flask remoto exponia diagnostico | Revelar estructura operativa del servicio auxiliar | Remoto sin clave recibe solo estado basico |
| Horarios exactos sin fuente administrativa | Presentar datos inventados como oficiales | Se eliminaron horarios exactos no sustentados y se orienta a confirmar con administracion |
| Prueba que exigia un horario no verificado | Convertir un dato inventado en requisito de regresion | La prueba ahora exige ausencia de hora exacta, orientacion a administracion y marca de validacion |
| Normas comunitarias marcadas como verificadas | Confundir recomendaciones con reglamento oficial | 35 orientaciones quedaron pendientes de validacion; 73 entradas conservan estado verificado |
| Conversaciones y mensajes sin restriccion explicita en Django Admin | Acceso accidental por cuentas staff | Ambos administradores usan `SoloAdministradorMixin` |
| Fallback legado duplicado | Dos fuentes de respuesta con riesgo de contradiccion | Se elimino `_respuesta_fallback`; el motor local es la unica ruta local |
| Errores de trazabilidad silenciados | Fallos invisibles de observabilidad | El registro fallido ahora genera `LOGGER.exception` sin romper el chat |
| Desafio inicial demasiado pequeno | Metrica optimista y debil ante jurado | Challenge ampliado a 24 casos y separado como conjunto de desarrollo |
| Challenge usado para corregir el motor | Riesgo de sobreajuste metodologico | Se agrego holdout final de 20 preguntas no usado para ajustes posteriores |
| Vocabulario cotidiano insuficiente | Rechazo prematuro de consultas pertinentes | Se agregaron terminos y reglas generales para acceso, seguimiento, avisos, seguridad, mantenimiento y tramites |

## Evidencia medida

| Conjunto | Uso correcto | Total | Precision micro | F1 macro | Directas incorrectas |
|---|---|---:|---:|---:|---:|
| Test controlado | Frases separadas, originadas en las mismas FAQ | 120 | 90.00 % | 91.82 % | 0 |
| Challenge de desarrollo | Analisis y correccion de errores | 24 | 79.17 % | 82.50 % | 0 |
| Holdout final | Auditoria manual sin ajustes posteriores | 20 | 55.00 % | 37.50 % | 0 |

El test controlado no comparte frases entre particiones, pero nace de la misma base de conocimiento y puede sobreestimar generalizacion. El challenge dejo de ser independiente al utilizarse para mejoras. El holdout final es la referencia mas honesta disponible para lenguaje manual nuevo.

En el test controlado, 61.67 % de las consultas recibieron respuesta local directa, 29.17 % solicitaron aclaracion, 4.17 % recibieron respuesta segura y 5.00 % quedaron como candidatas a respaldo generativo. El ahorro de tokens es una estimacion comparativa, no una factura del proveedor.

La prueba local concurrente ejecutada durante esta auditoria uso 300 solicitudes y 20 workers: 300 exitosas, 0 errores y 0 contaminaciones de cache. Esta evidencia valida el motor en memoria del equipo actual, no una carga distribuida de produccion.

## Seguridad y privacidad

- Todos los endpoints Django del asistente requieren autenticacion.
- Cada consulta de conversaciones se filtra por `request.user`.
- El historial del endpoint legado se considera no confiable y descarta mensajes de asistente enviados por cliente.
- Los logs redactan claves, tokens, correos y telefonos antes de persistir.
- Los intentos de revelar instrucciones, credenciales o datos privados se bloquean antes de Gemini.
- El contexto enviado al proveedor contiene rol y conteos agregados, no nombres, unidades, titulos ni cuerpos de avisos.
- Las respuestas generativas deben reconocer incertidumbre y remitir a administracion; valores exactos no verificados se rechazan.
- El escaneo final no encontro secretos versionados. El `google-services.json` local permanece excluido por `.gitignore`.
- No se modifico codigo funcional de interfaz web o movil durante esta auditoria.

## Riesgos residuales

1. El holdout final evidencia dificultad con lenguaje indirecto. Debe ampliarse con consultas reales anonimizadas antes de afirmar una mejora general.
2. La cuota externa se valida mediante logs. En un despliegue futuro con varios procesos o instancias debe implementarse reserva atomica distribuida, por ejemplo con Redis.
3. La llamada externa ocurre mientras la conversacion mantiene bloqueo transaccional para preservar orden. Es correcto para consistencia, pero puede aumentar espera en mensajes simultaneos de una misma conversacion.
4. No existe una politica automatizada de retencion de conversaciones y logs. Debe definirse con administracion antes de una operacion prolongada.
5. La prueba concurrente no incluye red, PostgreSQL remoto, Firebase ni Gemini real simultaneo.
6. Flask es una capacidad auxiliar implementada, pero no esta desplegada como microservicio productivo.
7. Las 35 orientaciones pendientes no deben aprobarse hasta registrar una fuente administrativa verificable.

## Pasos manuales pendientes

- Sincronizar en produccion los estados actuales de conocimiento mediante el flujo administrable y revision de administracion.
- Capturar un nuevo snapshot productivo que declare `alcance: usuarios_autenticados`.
- Definir retencion de chats y logs.
- Ejecutar carga distribuida sobre el entorno desplegado si aumenta el numero de usuarios.
- Incorporar consultas reales anonimizadas al siguiente holdout, sin entrenar sobre el conjunto usado para evaluar.

## Reproduccion

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py validar_base_conocimiento
.\.venv\Scripts\python.exe manage.py generar_evidencia_tecnica_asistente --solicitudes 300 --workers 20
.\.venv\Scripts\python.exe manage.py demostrar_asistente_hibrido --solicitudes 30 --workers 6
.\.venv\Scripts\python.exe -m pytest asistente -q
.\.venv\Scripts\python.exe -m pytest -q
```

La evidencia completa se conserva en `docs/evidencias/asistente_evidencia_tecnica_2026.json` y `docs/evidencias/asistente_evidencia_tecnica_2026.md`.

## Resultado de regresion final

```text
Suite del asistente: 80 passed, 16 subtests passed
Suite completa backend: 209 passed, 22 subtests passed
Django check: sin problemas
Migraciones pendientes: ninguna
Base de conocimiento: 108 FAQ, 73 verificadas y 35 pendientes
Flutter analyze: sin problemas
Flutter test: 8 pruebas aprobadas
```
