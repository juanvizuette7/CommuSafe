# Auditoria tecnica del asistente virtual de CommuSafe

## Alcance

Esta auditoria revisa exclusivamente el asistente virtual de CommuSafe a nivel backend. No modifica la interfaz movil, navegacion, diseno del chat ni componentes visuales existentes. El objetivo fue evaluar y corregir riesgos que podrian ser cuestionados en sustentacion: dependencia excesiva de IA generativa, consumo innecesario de tokens, respuestas inconsistentes, falta de conocimiento local, concurrencia, seguridad, documentacion y pruebas.

## Hallazgos y correcciones

| Area auditada | Riesgo identificado | Correccion aplicada | Evidencia |
|---|---|---|---|
| Dependencia de IA generativa | El asistente podia depender demasiado de Gemini/Anthropic para preguntas frecuentes. | Se mantiene arquitectura local-first con base de conocimiento de 108 entradas, coincidencia exacta, normalizacion, palabras clave, TF-IDF, clasificacion de intencion, reglas de negocio y respuesta segura. | `backend/asistente/local_knowledge.py`, `backend/asistente/local_engine.py` |
| Consumo de tokens | El historial persistente podia crecer y aumentar el costo si se enviaba completo al LLM. | Se agrego compactacion de historial antes de IA: maximo 12 mensajes y 6000 caracteres. La base de datos conserva el historial completo. | `MAX_LLM_HISTORY_MESSAGES`, `MAX_LLM_HISTORY_CHARS`, `_compactar_historial_para_ia()` |
| Respuestas inconsistentes | La IA podria usar formato Markdown excesivo, inventar informacion o salir del dominio. | Prompt restringido al dominio, limpieza de Markdown decorativo, fallback seguro y logs de modo/intencion/confianza. | `SYSTEM_PROMPT`, `_limpiar_respuesta_ia()`, `AsistenteRespuestaLog` |
| Privacidad frente al proveedor IA | El contexto generativo incluia datos personales y detalles operativos innecesarios. | El contexto externo se minimizo a rol y conteos agregados; no envia nombre, unidad, titulos, ubicaciones ni cuerpos de avisos. | `_contexto_usuario()`, `test_contexto_enviado_a_ia_minimiza_datos_personales` |
| Falta de conocimiento local | El asistente necesitaba respuestas preparadas para normas, procedimientos y uso del sistema. | Base local con preguntas, variaciones, categorias, keywords, roles, estado de verificacion y trazabilidad. | `local_knowledge.py` |
| Mantenimiento futuro | La base necesitaba una forma objetiva de validar diversidad, vigencia y seguridad. | Se agrego comando de validacion/exportacion de base de conocimiento. | `python manage.py validar_base_conocimiento` |
| Concurrencia | Multiples usuarios no deben mezclar conversaciones ni dos mensajes simultaneos deben construir contexto desactualizado. | Motor local stateless con cache por texto/rol, conversaciones filtradas por usuario y bloqueo transaccional por conversacion durante el envio. | `ConversacionAsistenteViewSet.get_queryset()`, `select_for_update()`, `resolve_local_answer_cached()` |
| Abuso del endpoint | No habia limite especifico para mensajes del asistente. | Se agregaron throttles por usuario: 30 mensajes/minuto para chat y 120 lecturas/minuto. | `backend/asistente/throttles.py`, `views.py` |
| Seguridad del servicio Flask | El servicio auxiliar podia quedar escuchando en todas las interfaces sin clave. | Por defecto escucha en `127.0.0.1`; si no hay `COMMUSAFE_NLP_SERVICE_KEY`, bloquea inferencia remota. | `backend/asistente/nlp_flask_service.py` |
| Exposicion de informacion | El servicio `/knowledge` no debe exponerse remotamente sin control. | La misma proteccion de clave/local-only aplica a `/knowledge` e `/infer`. | Prueba `test_servicio_flask_restringe_acceso_remoto_sin_clave` |
| Observabilidad | No habia medicion suficiente del comportamiento por respuesta. | Logs tecnicos con modo, proveedor, modelo, intencion, categoria, confianza, latencia, tokens estimados y metadatos. | Modelo `AsistenteRespuestaLog` |
| Evaluacion | Faltaba comparacion clara entre estrategias locales entrenadas y no entrenadas. | Se agrego entrenamiento/comparacion reproducible de baseline por palabras, TF-IDF por palabra, TF-IDF por caracteres, ensambles y motor hibrido de produccion. | `python manage.py evaluar_modelos_asistente` |
| Fragmentacion de intenciones | Las 108 FAQ estaban tratadas como 108 clases con pocos ejemplos, lo que dificultaba generalizar y explicar la taxonomia. | Se conservaron las 108 FAQ como subintenciones y se agruparon en 20 intenciones principales mantenibles. | `backend/asistente/taxonomy.py` |
| Dataset de entrenamiento | El asistente necesitaba datos separados y sin fuga para sustentar comprension de intenciones. | Se reconstruyo un dataset profesional con 720 ejemplos, 20 intenciones principales, train/validation/test y seis estilos balanceados. | `python manage.py generar_dataset_asistente` |
| Umbrales de confianza | Los umbrales iniciales no tenian evidencia reproducible suficiente. | Se agrego calibracion por busqueda sobre validation y casos de reto; se seleccionaron 0.52, 0.28 y margen 0.04 con cero respuestas directas incorrectas en calibracion. | `calibrate_thresholds()` |
| Errores ortograficos y variaciones | El filtro de dominio rechazaba algunas preguntas utiles antes de clasificarlas. | Se agrego normalizacion de errores frecuentes, pluralizacion simple, vocabulario cotidiano y clasificacion por intencion principal, conservando rechazo seguro fuera de dominio. | `COMMON_TOKEN_CORRECTIONS`, `tokenize()`, `_classify_intents()` |
| Colisiones exactas | Siete variaciones cortas podian corresponder a mas de una FAQ y el indice conservaba solo una. | El indice exacto conserva todos los candidatos y solicita aclaracion cuando una frase es realmente ambigua. | `_exact_ambiguity_payload()`, `colisiones_exactas_controladas` |
| Documentacion | La arquitectura hibrida necesitaba explicacion sustentable. | Se agrego documentacion especifica de arquitectura, pruebas, seguridad, metricas y comandos. | `docs/ASISTENTE_HIBRIDO.md` |

## Arquitectura resultante

```text
App movil / Panel / Cliente autenticado
  -> Django REST Framework
  -> Throttle por usuario
  -> Motor local verificado
     -> Respuesta local
     -> Aclaracion
     -> Respuesta segura
     -> Escalamiento controlado a Gemini/Anthropic
  -> Log tecnico
  -> Conversacion persistente en PostgreSQL
```

## Politica de uso de IA generativa

El asistente no llama a IA generativa en preguntas frecuentes con respuesta local suficiente. La IA solo se usa cuando:

1. La consulta pertenece al dominio de Remansos del Norte o CommuSafe.
2. El motor local detecta baja confianza, pero no determina que sea una pregunta fuera de contexto.
3. Existe proveedor configurado correctamente.
4. El sistema puede enviar contexto verificado y una ventana compacta de historial.

Si el proveedor falla, devuelve una respuesta segura y registra el error de forma controlada.

## Control de tokens

El historial persistente no se recorta en base de datos. La compactacion aplica solo al contexto enviado al LLM:

| Limite | Valor |
|---|---:|
| Mensajes maximos enviados a IA | 12 |
| Caracteres maximos de historial enviado a IA | 6000 |
| Salida maxima configurada Gemini/Anthropic | 700 tokens |

Esto reduce costo, latencia y riesgo de enviar contexto innecesario.

## Seguridad y concurrencia

- Todos los endpoints Django del asistente requieren autenticacion.
- Cada usuario solo accede a sus propias conversaciones.
- El motor local no guarda estado por usuario.
- El cache se indexa por mensaje normalizado y rol.
- Las respuestas no exponen credenciales ni datos privados.
- El servicio Flask auxiliar no reemplaza el backend principal y queda protegido para uso local o con clave.

## Pruebas ejecutadas

Comandos:

```powershell
cd backend
python manage.py check
python -m pytest asistente/tests.py -q
python -m pytest -q
python manage.py generar_dataset_asistente
python manage.py evaluar_asistente_local
python manage.py evaluar_modelos_asistente --json ..\docs\evidencias\asistente_modelos.json --markdown ..\docs\evidencias\asistente_modelos.md
```

Resultados verificados:

```text
asistente/tests.py: 38 passed, 5 subtests passed
suite completa backend: 163 passed, 11 subtests passed
manage.py check: sin problemas
makemigrations --check --dry-run: sin cambios pendientes
validar_base_conocimiento: ok
generar_dataset_asistente: ok, 720 ejemplos, 0 errores
```

Estado de base de conocimiento:

| Indicador | Valor |
|---|---:|
| Preguntas principales diferentes | 108 |
| Intenciones principales | 20 |
| Subintenciones FAQ | 108 |
| Categorias | 12 |
| Entradas verificadas | 100 |
| Pendientes de validacion administrativa | 8 |
| Entradas vigentes | 108 |
| Entradas vencidas | 0 |

Dataset profesional:

| Indicador | Valor |
|---|---:|
| Ejemplos totales | 720 |
| Train | 480 |
| Validation | 120 |
| Test | 120 |
| Estilos por intencion | 6 |
| Duplicados entre particiones | 0 |
| Intenciones ambiguas por frase repetida | 0 |

Distribucion de estilos:

| Particion | Formal | Informal | Corta | Larga | Error ortografico | No tecnico |
|---|---:|---:|---:|---:|---:|---:|
| Train | 80 | 80 | 80 | 80 | 80 | 80 |
| Validation | 20 | 20 | 20 | 20 | 20 | 20 |
| Test | 20 | 20 | 20 | 20 | 20 | 20 |

Umbrales calibrados:

| Decision | Valor |
|---|---:|
| Respuesta local directa | `>= 0.52` sin ambiguedad |
| Aclaracion | `>= 0.28` o candidatos cercanos |
| Margen de ambiguedad | `0.04` entre intenciones principales |
| Respaldo generativo | Menor a `0.28`, solo si pertenece al dominio |
| Respuesta segura | Fuera de dominio, dato no verificado o falla del proveedor |

Metricas del motor local:

| Split | F1 |
|---|---:|
| Train | 0.8771 |
| Validation | 0.8583 |
| Test | 0.9000 |
| Challenge | 0.5714 |

Comparacion de modelos locales:

| Estrategia | Validation F1 | Test F1 | Challenge F1 |
|---|---:|---:|---:|
| Baseline por palabras clave | 0.6000 | 0.6500 | 0.5714 |
| TF-IDF centroides por palabra | 0.6583 | 0.6667 | 0.5714 |
| TF-IDF centroides por caracteres | 0.6500 | 0.7000 | 0.5714 |
| Ensamble palabra/caracter 0.35/0.65 | 0.6500 | 0.7083 | 0.5714 |
| Hibrido local de produccion | 0.8583 | 0.9000 | 0.5714 |

Comportamiento en test:

| Resultado | Porcentaje |
|---|---:|
| Respuesta local directa | 66.67% |
| Aclaracion | 26.67% |
| Candidato a Gemini/Anthropic | 4.17% |
| Respuesta segura | 2.50% |

Evidencia exportada:

- `docs/evidencias/asistente_modelos.json`
- `docs/evidencias/asistente_modelos.md`

Confusiones residuales identificadas:

- Clasificacion de incidentes frente a avisos cuando la frase solo menciona una categoria.
- Gestion de avisos frente a navegacion de la app cuando la consulta solo indica que desea abrir algo.
- Frases demasiado cortas sin terminos del dominio, que se rechazan de forma segura antes de arriesgar una respuesta incorrecta.

## Riesgos residuales reales

- Las metricas locales se calculan sobre la base registrada y deben complementarse con pruebas de usuarios reales.
- Algunas respuestas marcadas como pendientes de validacion necesitan confirmacion administrativa si el conjunto cambia horarios, telefonos o reglas.
- El LLM sigue siendo un respaldo externo: puede fallar por cuota, red o proveedor; el sistema ya responde de forma segura en esos casos.
- El servicio Flask auxiliar es opcional; si se publica fuera de localhost debe usarse `COMMUSAFE_NLP_SERVICE_KEY`.

## Conclusion

El asistente queda defendible como modulo profesional del sistema: conserva 108 respuestas preparadas sin convertirlas en 108 clases fragmentadas, reduce dependencia de IA generativa, conserva memoria conversacional, mantiene control por rol, evita consumo innecesario de tokens, registra trazabilidad y cuenta con pruebas y documentacion verificables.
