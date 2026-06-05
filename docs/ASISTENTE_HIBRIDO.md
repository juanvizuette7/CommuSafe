# Asistente virtual hibrido de CommuSafe

## Objetivo

El asistente virtual de CommuSafe funciona como un orientador conversacional especializado en Remansos del Norte y en el uso del sistema. Su responsabilidad es responder consultas sobre incidentes, avisos, convivencia, administracion, vigilancia, visitantes, parqueaderos, mascotas, zonas comunes, mantenimiento, notificaciones y uso de la aplicacion.

El diseno evita que el asistente dependa siempre de una API externa. Primero intenta resolver con una base de conocimiento local verificada y, solo cuando la pregunta es del dominio pero no tiene una respuesta local suficientemente confiable, escala a IA generativa configurada en produccion.

## Arquitectura

```text
Usuario autenticado
  -> Flutter o endpoint REST
  -> API Django /api/asistente/
  -> Motor local de conocimiento
     -> Respuesta local de alta confianza
     -> Aclaracion si la pregunta es ambigua
     -> Respuesta segura si esta fuera del dominio
     -> IA generativa si es del dominio pero no hay respuesta local suficiente
  -> Log tecnico de respuesta
  -> Conversacion persistente en PostgreSQL
```

La arquitectura queda separada por responsabilidades:

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Base de conocimiento | `backend/asistente/local_knowledge.py` | Preguntas frecuentes, variaciones, categorias, palabras clave, roles permitidos y trazabilidad de cada entrada |
| Motor local | `backend/asistente/local_engine.py` | Coincidencia exacta, scoring por palabras clave, TF-IDF, umbrales de confianza y respuesta segura |
| Servicio LLM | `backend/asistente/services.py` | Orquestacion local-first, contexto del usuario, historial conversacional, Gemini/Anthropic y logs |
| API REST | `backend/asistente/views.py` | Chat rapido, conversaciones persistentes, mensajes, health check y acciones REST |
| Persistencia | `backend/asistente/models.py` | Conversaciones, mensajes y logs tecnicos de respuestas |
| Evaluacion | `backend/asistente/evaluation.py` | Dataset local, metricas, cobertura y matriz de confusion resumida |
| Servicio auxiliar | `backend/asistente/nlp_flask_service.py` | Microservicio Flask opcional para inferencia local por HTTP |

## Base de conocimiento local

La base local contiene mas de 100 entradas iniciales organizadas por categorias:

- Uso del sistema.
- Incidentes.
- Notificaciones.
- Seguridad.
- Administracion.
- Convivencia.
- Visitantes.
- Parqueaderos.
- Mascotas.
- Zonas comunes.
- Mantenimiento.
- Asistente virtual.

Cada entrada define:

- `intent`: identificador funcional de la pregunta.
- `category`: categoria operacional.
- `question`: pregunta principal.
- `answer`: respuesta validada para el asistente.
- `keywords`: terminos relevantes para busqueda local.
- `variations`: formas alternativas de preguntar.
- `allowed_roles`: roles que pueden recibir esa respuesta.
- `verified`: indica si la respuesta esta validada.
- `change_trace`: motivo o historial de la entrada.

Esto permite ampliar la informacion sin modificar toda la logica del asistente.

## Estrategia local-first

El motor local usa cuatro niveles de decision:

| Resultado | Uso |
|---|---|
| `answer` | Responde directamente cuando la confianza es alta |
| `clarify` | Pide aclaracion cuando detecta dominio valido pero intencion ambigua |
| `safe` | Rechaza o redirige consultas fuera del contexto de Remansos del Norte y CommuSafe |
| `fallback_allowed` | Permite escalar a Gemini o Anthropic cuando la pregunta es del dominio pero la base local no alcanza confianza suficiente |

Los umbrales actuales son:

- Confianza alta: `0.62`.
- Confianza media: `0.42`.

La respuesta segura impide que el asistente invente datos sobre valores, sanciones, nombres, decisiones administrativas o temas externos al conjunto.

## IA generativa

Cuando se usa IA real, el proveedor se resuelve desde variables de entorno:

| Variable | Uso |
|---|---|
| `LLM_PROVIDER` | Proveedor preferido: `gemini` o `anthropic` |
| `GEMINI_API_KEY` | API key de Google AI Studio |
| `GEMINI_MODEL` | Modelo Gemini activo |
| `LLM_API_KEY` | API key alternativa de Anthropic |

El prompt del sistema restringe al asistente al contexto de CommuSafe, evita Markdown decorativo, evita respuestas externas y solicita texto claro en espanol. El historial persistente de la conversacion se envia como contexto para mantener coherencia.

Para controlar consumo de tokens, el historial completo permanece guardado en PostgreSQL, pero la ventana enviada al LLM se compacta a los ultimos mensajes relevantes:

| Control | Valor |
|---|---:|
| Maximo de mensajes enviados a IA | 12 |
| Maximo de caracteres de historial enviado a IA | 6000 |
| Maximo de salida de Gemini/Anthropic | 700 tokens |

## Persistencia

El asistente usa tres modelos principales:

| Modelo | Funcion |
|---|---|
| `ConversacionAsistente` | Chat independiente por usuario, con titulo y fecha de ultima actividad |
| `MensajeAsistente` | Mensajes del usuario y del asistente asociados a una conversacion |
| `AsistenteRespuestaLog` | Trazabilidad tecnica de modo, proveedor, modelo, intencion, confianza, latencia y tokens estimados |

Cada usuario solo puede listar, abrir, enviar mensajes y eliminar sus propias conversaciones.

## Servicio Flask auxiliar

El archivo `backend/asistente/nlp_flask_service.py` expone un servicio auxiliar opcional:

```powershell
cd backend
python -m asistente.nlp_flask_service
```

Endpoints:

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/health` | Estado del motor local |
| `POST` | `/infer` | Inferencia local para una pregunta |
| `GET` | `/knowledge` | Resumen de la base de conocimiento |

Si se define `COMMUSAFE_NLP_SERVICE_KEY`, las peticiones deben enviar el header `X-CommuSafe-NLP-Key`.

Por seguridad, el servicio escucha por defecto en `127.0.0.1`. Para exponerlo a otra interfaz se debe configurar conscientemente `COMMUSAFE_NLP_HOST` y protegerlo con `COMMUSAFE_NLP_SERVICE_KEY`.

## Evaluacion y metricas

El comando de evaluacion genera un dataset deterministico desde preguntas y variaciones registradas:

```powershell
cd backend
python manage.py evaluar_asistente_local
```

Metricas reportadas:

- Precision micro.
- Recall micro.
- F1 micro.
- Cobertura local.
- Tasa de aclaracion.
- Tasa de respuesta segura.
- Uso estimado de IA.
- Latencia promedio.
- Matriz de confusion resumida.

Resultado local verificado en desarrollo:

```text
train:      F1 0.9921
validation: F1 0.9756
test:       F1 0.9438
```

Comparacion de estrategias locales:

| Estrategia | Validation F1 | Test F1 | Decision |
|---|---:|---:|---|
| Palabras clave baseline | 0.1829 | 0.1124 | Insuficiente como solucion unica |
| TF-IDF semantico puro | 0.3780 | 0.3483 | Mejora frente al baseline, pero falla en muchas intenciones cortas o ambiguas |
| Hibrido seleccionado | 0.9756 | 0.9438 | Estrategia activa por mejor generalizacion y control de seguridad |

La comparacion se calcula con el comando `python manage.py evaluar_asistente_local`. El resultado debe interpretarse como evidencia tecnica inicial sobre la base registrada, no como reemplazo de pruebas con usuarios reales.

## Pruebas

Pruebas relevantes:

```powershell
cd backend
python -m pytest asistente/tests.py -q
python -m pytest tests/test_sistema_completo.py -q
python manage.py check
```

Cobertura funcional validada:

- Respuesta local de alta confianza.
- Respuesta segura fuera del dominio.
- Health check con informacion del motor local.
- Logs tecnicos de respuesta.
- Conversaciones persistentes.
- Aislamiento por usuario.
- Eliminacion de conversaciones.
- Uso de IA cuando la consulta es del dominio pero no tiene respuesta local suficiente.
- Manejo de errores del proveedor LLM.

## Criterios de seguridad

- El usuario debe estar autenticado para usar el asistente.
- Las conversaciones se filtran por propietario.
- No se exponen chats de otros usuarios.
- Los endpoints del asistente tienen throttling por usuario.
- No se guardan claves de IA en el repositorio.
- El asistente no responde temas externos al conjunto.
- El prompt prohibe inventar datos administrativos no registrados.
- Los logs registran informacion tecnica, no claves ni secretos.
- El servicio Flask auxiliar bloquea inferencia remota si no existe clave de servicio.

## Comandos utiles

Probar una pregunta en consola:

```powershell
cd backend
python manage.py probar_asistente "Como reporto un incidente?"
```

Evaluar cobertura local:

```powershell
python manage.py evaluar_asistente_local
```

Verificar configuracion:

```powershell
python manage.py check
```

Ejecutar servicio Flask auxiliar:

```powershell
python -m asistente.nlp_flask_service
```
