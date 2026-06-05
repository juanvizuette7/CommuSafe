# Auditoria tecnica del asistente virtual de CommuSafe

## Alcance

Esta auditoria revisa exclusivamente el asistente virtual de CommuSafe a nivel backend. No modifica la interfaz movil, navegacion, diseno del chat ni componentes visuales existentes. El objetivo fue evaluar y corregir riesgos que podrian ser cuestionados en sustentacion: dependencia excesiva de IA generativa, consumo innecesario de tokens, respuestas inconsistentes, falta de conocimiento local, concurrencia, seguridad, documentacion y pruebas.

## Hallazgos y correcciones

| Area auditada | Riesgo identificado | Correccion aplicada | Evidencia |
|---|---|---|---|
| Dependencia de IA generativa | El asistente podia depender demasiado de Gemini/Anthropic para preguntas frecuentes. | Se mantiene arquitectura local-first con base de conocimiento de 108 entradas, coincidencia exacta, palabras clave, TF-IDF y respuesta segura. | `backend/asistente/local_knowledge.py`, `backend/asistente/local_engine.py` |
| Consumo de tokens | El historial persistente podia crecer y aumentar el costo si se enviaba completo al LLM. | Se agrego compactacion de historial antes de IA: maximo 12 mensajes y 6000 caracteres. La base de datos conserva el historial completo. | `MAX_LLM_HISTORY_MESSAGES`, `MAX_LLM_HISTORY_CHARS`, `_compactar_historial_para_ia()` |
| Respuestas inconsistentes | La IA podria usar formato Markdown excesivo, inventar informacion o salir del dominio. | Prompt restringido al dominio, limpieza de Markdown decorativo, fallback seguro y logs de modo/intencion/confianza. | `SYSTEM_PROMPT`, `_limpiar_respuesta_ia()`, `AsistenteRespuestaLog` |
| Falta de conocimiento local | El asistente necesitaba respuestas preparadas para normas, procedimientos y uso del sistema. | Base local con preguntas, variaciones, categorias, keywords, roles, estado de verificacion y trazabilidad. | `local_knowledge.py` |
| Concurrencia | Multiples usuarios no deben mezclar conversaciones ni estados. | Motor local stateless con cache por texto/rol, conversaciones filtradas por usuario autenticado y mensajes persistidos por conversacion. | `ConversacionAsistenteViewSet.get_queryset()`, `resolve_local_answer_cached()` |
| Abuso del endpoint | No habia limite especifico para mensajes del asistente. | Se agregaron throttles por usuario: 30 mensajes/minuto para chat y 120 lecturas/minuto. | `backend/asistente/throttles.py`, `views.py` |
| Seguridad del servicio Flask | El servicio auxiliar podia quedar escuchando en todas las interfaces sin clave. | Por defecto escucha en `127.0.0.1`; si no hay `COMMUSAFE_NLP_SERVICE_KEY`, bloquea inferencia remota. | `backend/asistente/nlp_flask_service.py` |
| Exposicion de informacion | El servicio `/knowledge` no debe exponerse remotamente sin control. | La misma proteccion de clave/local-only aplica a `/knowledge` e `/infer`. | Prueba `test_servicio_flask_restringe_acceso_remoto_sin_clave` |
| Observabilidad | No habia medicion suficiente del comportamiento por respuesta. | Logs tecnicos con modo, proveedor, modelo, intencion, categoria, confianza, latencia, tokens estimados y metadatos. | Modelo `AsistenteRespuestaLog` |
| Evaluacion | Faltaba comparacion clara entre estrategias locales. | Se agrego comando de evaluacion con baseline de palabras clave, TF-IDF puro e hibrido seleccionado. | `python manage.py evaluar_asistente_local` |
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
python manage.py evaluar_asistente_local
```

Resultados verificados:

```text
asistente/tests.py: 26 passed
suite completa backend: 148 passed, 6 subtests passed
manage.py check: sin problemas
makemigrations --check --dry-run: sin cambios pendientes
```

Metricas del motor local:

| Split | F1 |
|---|---:|
| Train | 0.9921 |
| Validation | 0.9756 |
| Test | 0.9438 |

Comparacion de estrategias:

| Estrategia | Validation F1 | Test F1 |
|---|---:|---:|
| Palabras clave baseline | 0.1829 | 0.1124 |
| TF-IDF semantico puro | 0.3780 | 0.3483 |
| Hibrido seleccionado | 0.9756 | 0.9438 |

## Riesgos residuales reales

- Las metricas locales se calculan sobre la base registrada; deben complementarse con pruebas de usuarios reales.
- Algunas respuestas marcadas como pendientes de validacion necesitan confirmacion administrativa si el conjunto cambia horarios, telefonos o reglas.
- El LLM sigue siendo un respaldo externo: puede fallar por cuota, red o proveedor; el sistema ya responde de forma segura en esos casos.
- El servicio Flask auxiliar es opcional; si se publica fuera de localhost debe usarse `COMMUSAFE_NLP_SERVICE_KEY`.

## Conclusion

El asistente queda defendible como modulo profesional del sistema: reduce dependencia de IA generativa, conserva memoria conversacional, mantiene control por rol, limita abuso, evita consumo innecesario de tokens, registra trazabilidad y cuenta con pruebas y documentacion verificables.
