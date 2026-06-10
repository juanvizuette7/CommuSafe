# Asistente virtual hibrido de CommuSafe

La explicación académica consolidada de la mejora, sus resultados y sus limitaciones se encuentra en `docs/MEJORA_ACADEMICA_ASISTENTE_HIBRIDO.md`. Este documento conserva el detalle técnico y operativo necesario para implementar, mantener y reproducir el módulo.

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
| Catalogo inicial | `backend/asistente/local_knowledge.py` | Respaldo inicial de preguntas frecuentes y metadatos de comprension |
| Repositorio administrable | `backend/asistente/knowledge_repository.py` y modelos de conocimiento | Combina el respaldo con contenido aprobado y vigente administrado en base de datos |
| Taxonomia | `backend/asistente/taxonomy.py` | Agrupacion mantenible de FAQ y subtemas en intenciones principales |
| Motor local | `backend/asistente/local_engine.py` | Coincidencia exacta, normalizacion, palabras clave, TF-IDF, clasificacion de intencion, reglas de negocio, cache, umbrales de confianza y respuesta segura |
| Servicio LLM | `backend/asistente/services.py` | Orquestacion local-first, contexto del usuario, historial conversacional, Gemini/Anthropic y logs |
| API REST | `backend/asistente/views.py` | Chat rapido, conversaciones persistentes, mensajes, health check y acciones REST |
| Persistencia | `backend/asistente/models.py` | Conversaciones, mensajes, logs, entradas administrables, versiones y consultas sin respuesta |
| Evaluacion | `backend/asistente/evaluation.py` | Dataset local, metricas, cobertura y matriz de confusion resumida |
| Dataset profesional | `backend/asistente/training_dataset.py` | Generacion balanceada de entrenamiento, validacion y prueba para intenciones del asistente |
| Seleccion de modelo | `backend/asistente/model_selection.py` | Entrenamiento, comparacion, calibracion y seleccion reproducible de modelos locales |
| Servicio auxiliar | `backend/asistente/nlp_flask_service.py` | Microservicio Flask opcional para inferencia local por HTTP, lote, candidatos, evaluacion, seleccion de modelo y reentrenamiento logico |

## Base de conocimiento local

La base local contiene 108 entradas iniciales organizadas por categorias. En la auditoria final quedaron 73 verificadas y 35 orientaciones comunitarias pendientes de aprobacion administrativa:

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

- `main_intent`: intencion principal usada por el clasificador y las metricas.
- `subintent`: identificador funcional especifico de la FAQ.
- `category`: categoria operacional.
- `question`: pregunta principal.
- `answer`: respuesta validada para el asistente.
- `keywords`: terminos relevantes para busqueda local.
- `variations`: formas alternativas de preguntar.
- `allowed_roles`: roles que pueden recibir esa respuesta.
- `verified`: indica si la respuesta esta validada.
- `verification_status`: estado formal de verificacion.
- `valid_from` y `valid_until`: vigencia de la entrada.
- `validity_status`: indica si la entrada esta vigente o vencida.
- `maintainer_role`: rol responsable de mantenimiento.
- `source`: fuente interna registrada para trazabilidad.
- `change_trace`: motivo o historial de la entrada.

Esto permite ampliar la informacion sin modificar toda la logica del asistente. Para mantenimiento posterior a la entrega, las entradas se crean, revisan, aprueban, versionan y desactivan desde Django Admin. El procedimiento completo se encuentra en `docs/GESTION_CONOCIMIENTO_ASISTENTE.md`.

Solo las entradas administradas con estado `APROBADA` y vigencia activa se incorporan al motor. Una entrada en borrador, revision, inactiva o rechazada nunca se presenta como informacion oficial. Cada cambio conserva una version inmutable con responsable y fecha.

Estado actual verificado:

| Indicador | Valor |
|---|---:|
| Preguntas principales diferentes | 108 |
| Intenciones principales | 20 |
| Subintenciones FAQ | 108 |
| Categorias | 12 |
| Entradas verificadas | 73 |
| Pendientes de validacion administrativa | 35 |
| Entradas vigentes | 108 |
| Entradas vencidas | 0 |

## Decision de taxonomia

La primera version trataba cada una de las 108 FAQ como una intencion independiente. Aunque conservaba mucha informacion, producia clases pequenas, aumentaba ambiguedad y dificultaba explicar el modelo. La auditoria reorganizo el conocimiento sin eliminarlo:

```text
Categoria operacional
  -> Intencion principal
     -> FAQ o subintencion
        -> Pregunta principal
        -> Variaciones naturales
        -> Respuesta preparada y verificada
```

Las categorias sirven para organizar el dominio; las 20 intenciones principales representan objetivos del usuario; las 108 FAQ conservan el detalle operativo; y las variaciones permiten reconocer distintas formas de preguntar. Esta estructura evita que el clasificador memorice una clase por pregunta y permite que el motor recupere una respuesta concreta despues de comprender el tema general.

## Dataset profesional de entrenamiento

El asistente cuenta con un dataset deterministico generado desde la base de conocimiento local. Este dataset no reemplaza la base operativa; sirve para entrenar, validar, probar y sustentar la comprension de intenciones en espanol.

El dataset no es un archivo aislado: `training_dataset.py` y el chat real consumen la misma fuente de verdad, `FAQ_ENTRIES` y `MAIN_INTENTS`. El motor recupera la FAQ concreta para responder, mientras el dataset evalua la intencion principal y conserva `subintent` y `entry_id` para trazabilidad.

La taxonomia se basa en:

- Veinte intenciones principales faciles de explicar y mantener.
- Ciento ocho FAQ conservadas como subintenciones y respuestas preparadas.
- Categoria operacional.
- Rol principal aplicable.
- Palabras clave verificables.
- Estado de verificacion.
- Vigencia.
- Estilo de redaccion.

Los estilos obligatorios por intencion son:

- Formal.
- Informal.
- Corta.
- Larga.
- Error ortografico comun.
- Expresion no tecnica.

Cada intencion principal tiene exactamente 36 ejemplos, seis por cada estilo, distribuidos sin repetir frases entre particiones:

| Particion | Ejemplos | Uso |
|---|---:|---|
| Train | 480 | Ajuste y revision del motor |
| Validation | 120 | Comparacion de estrategias y calibracion |
| Test | 120 | Medicion final con frases no vistas |

Resumen actual:

| Indicador | Valor |
|---|---:|
| Total de ejemplos | 720 |
| Intenciones principales | 20 |
| FAQ representadas | 108 de 108 |
| Categorias | 12 |
| Ejemplos por intencion | 36 |
| Estilos por intencion | 6 |
| Errores de dataset | 0 |

Distribucion de estilos por particion:

| Particion | Formal | Informal | Corta | Larga | Error ortografico | No tecnico |
|---|---:|---:|---:|---:|---:|---:|
| Train | 80 | 80 | 80 | 80 | 80 | 80 |
| Validation | 20 | 20 | 20 | 20 | 20 | 20 |
| Test | 20 | 20 | 20 | 20 | 20 | 20 |

El comando de generacion valida automaticamente duplicados, ambiguedades, balance por intencion, estilos obligatorios y fuga entre train/validation/test:

```powershell
cd backend
python manage.py generar_dataset_asistente
```

Exportar para revision externa:

```powershell
python manage.py generar_dataset_asistente --json tmp/commusafe_dataset.json --csv-dir tmp/commusafe_dataset
```

## Estrategia local-first

El motor local usa cuatro niveles de decision:

| Resultado | Uso |
|---|---|
| `answer` | Responde directamente cuando la confianza es alta |
| `clarify` | Pide aclaracion cuando detecta dominio valido pero intencion ambigua |
| `safe` | Rechaza o redirige consultas fuera del contexto de Remansos del Norte y CommuSafe |
| `fallback_allowed` | Permite escalar a Gemini o Anthropic cuando la pregunta es del dominio pero la base local no alcanza confianza suficiente |

Flujo aplicado:

1. Normaliza texto, tildes, puntuacion y errores ortograficos frecuentes.
2. Busca coincidencia exacta en preguntas, variaciones y palabras clave.
3. Aplica reglas de negocio de alta precision para casos operativos claros.
4. Calcula similitud por palabras clave, coincidencia lexica, TF-IDF por FAQ y clasificacion de intencion por centroides.
5. Recupera la FAQ concreta y su respuesta preparada.
6. Responde localmente si la confianza es alta.
7. Pide aclaracion si la confianza es media o existe ambiguedad entre intenciones principales.
8. Permite Gemini o Anthropic solo si la consulta es del dominio y queda en baja confianza.
9. Responde de forma segura si esta fuera del dominio, el proveedor falla o no hay informacion verificada.

El motor interno de Django es la fuente autoritativa porque conoce el estado administrado de cada entrada. Si el servicio Flask auxiliar esta configurado, su resultado solo complementa consultas que el repositorio interno no puede resolver; nunca reemplaza una respuesta aprobada ni reactiva contenido desactivado.

Los umbrales actuales fueron seleccionados mediante busqueda reproducible sobre validation y casos de reto:

- Confianza alta: `0.52`.
- Confianza media: `0.28`.
- Margen de ambiguedad: `0.04`.

La calibracion obtuvo cero respuestas directas incorrectas sobre el conjunto usado para seleccionar umbrales. Los valores se verifican con `python manage.py evaluar_asistente_local`.

La respuesta segura impide que el asistente invente datos sobre valores, sanciones, nombres, decisiones administrativas o temas externos al conjunto.

## IA generativa

La IA generativa es respaldo, no motor principal. El orden obligatorio es:

1. Motor local con base verificada.
2. Aclaracion cuando hay varias respuestas posibles.
3. Respuesta segura cuando la consulta esta fuera de dominio o no hay informacion verificable.
4. IA externa solo si el motor local devuelve baja confianza, la consulta sigue siendo del dominio y la cuota permite usar respaldo.

Cuando se usa IA real, el proveedor se resuelve desde variables de entorno y queda desacoplado mediante adaptadores:

| Variable | Uso |
|---|---|
| `LLM_PROVIDER` | Proveedor preferido: `gemini` o `anthropic` |
| `GEMINI_API_KEY` | API key de Google AI Studio |
| `GEMINI_MODEL` | Modelo Gemini activo |
| `LLM_API_KEY` | API key alternativa de Anthropic |
| `LLM_BACKUP_ENABLED` | Permite apagar completamente el respaldo generativo |
| `LLM_TIMEOUT_SECONDS` | Tiempo maximo de espera para Gemini/Anthropic |
| `LLM_MAX_OUTPUT_TOKENS` | Limite maximo de salida generativa |
| `LLM_HOURLY_REQUEST_LIMIT` | Limite de consultas IA por hora |
| `LLM_DAILY_REQUEST_LIMIT` | Limite de consultas IA por dia |
| `LLM_DAILY_TOKEN_LIMIT` | Limite diario de tokens estimados |

El prompt del sistema restringe al asistente al contexto de CommuSafe, evita Markdown decorativo, evita respuestas externas y solicita texto claro en espanol. El historial persistente de la conversacion se envia como contexto para mantener coherencia, pero se compacta antes de salir hacia IA externa.

Para controlar consumo de tokens, el historial completo permanece guardado en PostgreSQL, pero la ventana enviada al LLM se compacta a los ultimos mensajes relevantes:

| Control | Valor |
|---|---:|
| Maximo de mensajes enviados a IA | 12 |
| Maximo de caracteres de historial enviado a IA | 6000 |
| Maximo de salida de Gemini/Anthropic | 700 tokens |
| Timeout por llamada generativa | 8 segundos por defecto |
| Limite por hora | 20 consultas IA por defecto |
| Limite por dia | 80 consultas IA por defecto |
| Limite diario de tokens | 120000 tokens estimados por defecto |

Antes de aceptar una respuesta generativa, el backend valida que:

- La respuesta no este vacia ni sea demasiado corta.
- No contenga patrones genericos de modelo de lenguaje o temas externos.
- Incluya marcadores del dominio como CommuSafe, Remansos, porteria, administracion, incidentes, vigilancia o reportes.
- No entregue valores monetarios exactos sin indicar validacion con administracion.

Si falla Gemini, se excede la cuota, vence el timeout o la respuesta parece inventada, el sistema devuelve una respuesta segura y registra el motivo en `AsistenteRespuestaLog.metadata`.

El endpoint `GET /api/asistente/health/` expone a administradores metricas de consultas autenticadas de las ultimas 24 horas:

- Consultas totales.
- Consultas resueltas sin Gemini.
- Consultas que requirieron aclaracion.
- Consultas que usaron IA externa.
- Consultas que usaron Gemini.
- Tokens estimados consumidos por IA.
- Tokens estimados ahorrados por respuestas locales.

## Persistencia

El asistente usa tres modelos principales:

| Modelo | Funcion |
|---|---|
| `ConversacionAsistente` | Chat independiente por usuario, con titulo y fecha de ultima actividad |
| `MensajeAsistente` | Mensajes del usuario y del asistente asociados a una conversacion |
| `AsistenteRespuestaLog` | Trazabilidad tecnica de modo, proveedor, modelo, intencion, confianza, latencia y tokens estimados |

Cada usuario solo puede listar, abrir, enviar mensajes y eliminar sus propias conversaciones.

## Servicio Flask auxiliar

El archivo `backend/asistente/nlp_flask_service.py` expone un servicio auxiliar opcional. No reemplaza a Django: actua como proceso especializado para comprension local, inferencia, evaluacion y mantenimiento del motor NLP. Django puede usarlo si `COMMUSAFE_NLP_SERVICE_URL` esta configurada; si el servicio no responde, vuelve automaticamente al motor local embebido.

```powershell
cd backend
python -m asistente.nlp_flask_service
```

Para un proceso WSGI separado:

```powershell
gunicorn asistente.nlp_flask_service:app --bind 127.0.0.1:5055 --workers 2 --threads 4
```

Endpoints:

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/v1/health` | Estado del motor local, cache, seguridad y version del servicio |
| `POST` | `/v1/infer` | Inferencia local para una pregunta |
| `POST` | `/v1/infer/batch` | Inferencia por lote con limite configurable |
| `POST` | `/v1/candidates` | Candidatos de respuesta ordenados por confianza |
| `GET` | `/v1/knowledge` | Resumen y entradas de la base de conocimiento |
| `POST` | `/v1/evaluate` | Evaluacion local reproducible del motor |
| `POST` | `/v1/models/select` | Entrenamiento, comparacion y seleccion del mejor modelo local |
| `POST` | `/v1/retrain` | Limpieza de cache, validacion del dataset y preparacion para recarga |

Las rutas antiguas `/health`, `/infer` y `/knowledge` se conservan como compatibilidad. Si se define `COMMUSAFE_NLP_SERVICE_KEY`, las peticiones deben enviar el header `X-CommuSafe-NLP-Key`.

El procesamiento principal permanece integrado en Django porque comparte autenticacion, roles, persistencia y servicios de negocio. Flask reutiliza el mismo `ENGINE`, por lo que no duplica la logica de clasificacion. Las operaciones pesadas de evaluacion y seleccion se protegen con bloqueo interno para evitar ejecuciones simultaneas inconsistentes.

Por seguridad, el servicio escucha por defecto en `127.0.0.1`. Para exponerlo a otra interfaz se debe configurar conscientemente `COMMUSAFE_NLP_HOST` y protegerlo con `COMMUSAFE_NLP_SERVICE_KEY`. Las respuestas incluyen `X-CommuSafe-Request-ID` y latencia para facilitar diagnostico.

Variables opcionales:

| Variable | Uso |
|---|---|
| `COMMUSAFE_NLP_SERVICE_URL` | URL que Django usa para delegar inferencia a Flask |
| `COMMUSAFE_NLP_SERVICE_KEY` | Clave interna para proteger llamadas HTTP |
| `COMMUSAFE_NLP_SERVICE_TIMEOUT` | Timeout de Django hacia Flask |
| `COMMUSAFE_NLP_HOST` | Host donde escucha Flask |
| `COMMUSAFE_NLP_PORT` | Puerto de Flask |
| `COMMUSAFE_NLP_MAX_BATCH_SIZE` | Tamano maximo de inferencia por lote |
| `COMMUSAFE_NLP_MAX_MESSAGE_LENGTH` | Longitud maxima por mensaje |

## Evaluacion y metricas

El comando de evaluacion usa el dataset profesional balanceado y un split adicional de reto con preguntas fuera de dominio, ambiguas o que requieren validacion administrativa:

```powershell
cd backend
python manage.py evaluar_asistente_local
```

Para entrenar, comparar y seleccionar el mejor enfoque local se usa:

```powershell
python manage.py evaluar_modelos_asistente --json ..\docs\evidencias\asistente_modelos.json --markdown ..\docs\evidencias\asistente_modelos.md
```

Este comando entrena modelos locales sobre `train`, calibra umbrales con `validation` y `challenge`, y mide la calidad final sobre `test`. La seleccion no usa la precision de entrenamiento como criterio principal.

Para revisar concurrencia, aislamiento de cache y comportamiento sin IA externa:

```powershell
python manage.py probar_resiliencia_asistente --requests 80 --workers 8
```

Para generar la evidencia técnica consolidada para sustentación:

```powershell
python manage.py generar_evidencia_tecnica_asistente
```

Este comando genera:

- `docs/evidencias/asistente_evidencia_tecnica_2026.md`: resumen explicativo para jurado.
- `docs/evidencias/asistente_evidencia_tecnica_2026.json`: matriz de confusión completa, métricas por intención y errores.
- Evidencia de precisión, recall, F1, cobertura local, aclaraciones, candidatos a Gemini, consistencia, tokens estimados y concurrencia.

Resultado consolidado verificado el 2026-06-10: 600 solicitudes, 20 workers, 600 exitosas, 0 errores, 0 contaminaciones de cache y sin uso de IA externa. La evidencia actual se encuentra en `docs/evidencias/asistente_evidencia_tecnica_2026.md`; la prueba de aceptación anterior se conserva en `docs/evidencias/asistente_resiliencia_aceptacion.json`.

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

Resultado local verificado en desarrollo despues de la auditoria de modelo:

```text
train:      F1 0.8771
validation: F1 0.8583
test:       F1 0.9000
challenge de desarrollo: F1 0.9583
holdout final: precision micro 0.5500
```

Los splits `validation` y `test` contienen todos los estilos de pregunta: formal, informal, corta, larga, error ortografico y no tecnico. No comparten frases, pero nacen de las mismas FAQ; por ello miden comportamiento controlado y pueden sobreestimar la generalizacion real.

Comparacion reproducible de estrategias locales entrenadas y evaluadas:

| Estrategia | Validation F1 | Test F1 | Challenge desarrollo | Decision |
|---|---:|---:|---:|---|
| Baseline por palabras clave | 0.6083 | 0.6583 | 0.4167 | Insuficiente como solucion unica |
| TF-IDF centroides por palabra | 0.6667 | 0.6750 | 0.4167 | Mejora el baseline, pero pierde precision en frases cortas |
| TF-IDF centroides por caracteres | 0.6667 | 0.7083 | 0.3750 | Aporta robustez ante errores ortograficos |
| Ensamble palabra/caracter 0.35/0.65 | 0.6583 | 0.7167 | 0.3750 | Mejor entre modelos entrenados puros, pero no supera la base de conocimiento |
| Hibrido local de produccion | 0.8583 | 0.9000 | 0.9583 | Seleccionado por mejor equilibrio interno, trazabilidad y control de seguridad |

Comportamiento consolidado medido el 10 de junio de 2026 sobre `test`:

| Resultado | Porcentaje |
|---|---:|
| Precisión micro | 90.00% |
| F1 macro | 91.82% |
| Respuesta local directa | 61.67% |
| Solicitud de aclaración | 29.17% |
| Candidato a IA generativa | 5.00% |
| Respuesta segura | 4.17% |
| Dependencia de Gemini evitada | 95.00% |
| Consistencia en tres repeticiones | 100.00% |

El reporte completo con matriz de confusion y analisis de errores queda en:

- `docs/evidencias/asistente_modelos.json`
- `docs/evidencias/asistente_modelos.md`
- `docs/evidencias/asistente_evidencia_tecnica_2026.json`
- `docs/evidencias/asistente_evidencia_tecnica_2026.md`

El holdout final de 20 preguntas manuales, no usado para ajustes posteriores, obtuvo 55.00% de precision micro, 0 respuestas directas incorrectas, 50% de respuestas seguras, 25% de aclaraciones y 25% de candidatas a respaldo. La principal limitacion restante es comprender lenguaje indirecto sin depender de terminos explicitos del dominio.

La comparacion se calcula con el comando `python manage.py evaluar_modelos_asistente`. El resultado debe interpretarse como evidencia tecnica inicial sobre la base registrada, no como reemplazo de pruebas con usuarios reales.

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
- Errores ortograficos frecuentes y lenguaje no tecnico.
- Preguntas largas, ambiguas, fuera de alcance y sobre datos no verificados.
- Calibracion reproducible de umbrales.

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

Generar y validar dataset profesional:

```powershell
python manage.py generar_dataset_asistente
```

Evaluar cobertura local:

```powershell
python manage.py evaluar_asistente_local
```

Entrenar y comparar modelos locales:

```powershell
python manage.py evaluar_modelos_asistente --json ..\docs\evidencias\asistente_modelos.json --markdown ..\docs\evidencias\asistente_modelos.md
```

Validar diversidad, vigencia, roles y respuestas seguras:

```powershell
python manage.py validar_base_conocimiento
```

Exportar la base a JSON para revision o mantenimiento:

```powershell
python manage.py validar_base_conocimiento --export-json tmp/commusafe_kb.json
```

Verificar configuracion:

```powershell
python manage.py check
```

Ejecutar servicio Flask auxiliar:

```powershell
python -m asistente.nlp_flask_service
```

## Texto academico para el trabajo de grado

CommuSafe incorporo un asistente virtual hibrido apoyado en una base de conocimiento local y un modelo de comprension de preguntas. La solucion organiza 108 preguntas frecuentes verificables en 20 intenciones principales, lo que permite responder consultas habituales sin consumir servicios externos de inteligencia artificial. El motor combina normalizacion de texto, coincidencia exacta, palabras clave y busqueda semantica TF-IDF; cuando detecta ambiguedad solicita aclaracion y solo permite usar Gemini como respaldo controlado ante consultas del dominio que no pueden resolverse localmente. Esta arquitectura reduce dependencia de tokens, mejora disponibilidad, mantiene consistencia en las respuestas y evita inventar informacion interna no validada por la administracion.
