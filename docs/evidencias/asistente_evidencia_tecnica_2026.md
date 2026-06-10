# Evidencia tecnica del asistente hibrido CommuSafe

Generada: `2026-06-10T17:20:42.003079+00:00`
Semilla reproducible: `42`
IA externa utilizada durante la evaluacion: **No**

## Resumen para jurado

La evaluacion demuestra que CommuBot resuelve la mayoria de consultas mediante conocimiento local verificable. Gemini queda como respaldo para consultas del dominio que no alcanzan confianza suficiente. Esto reduce dependencia externa y mantiene respuestas repetibles.

| Indicador | Resultado medido | Interpretacion simple |
|---|---:|---|
| Precision micro en split test reservado | 90.00% | Proporcion total de clasificaciones correctas |
| Recall macro en split test reservado | 90.00% | Capacidad promedio de reconocer cada intencion |
| F1 macro en split test reservado | 91.82% | Equilibrio promedio entre precision y recall |
| Cobertura de respuesta local directa | 61.67% | Preguntas respondidas directamente sin Gemini |
| Dependencia de Gemini evitada | 95.00% | Respuestas locales, aclaraciones o rechazo seguro |
| Tasa candidata a Gemini | 5.00% | Casos que podrian requerir respaldo externo |
| Consistencia en 3 repeticiones | 100.00% | Misma pregunta produce la misma decision y respuesta |
| Respuestas directas incorrectas | 0 | Riesgo de afirmar algo equivocado directamente |
| Latencia local promedio | 0.3421 ms | Tiempo medio del motor local en este equipo, con motor cargado |
| Tokens externos ahorrados estimados | 348612 | Estimacion frente a enviar todas las consultas a Gemini |
| Ahorro estimado promedio por consulta evitada | 3058.00 tokens | Promedio estimado, no facturacion real |

## Metodo

- Dataset profesional: **720** ejemplos, **20** intenciones y **108** FAQ representadas.
- Split test reservado: **120** preguntas no usadas para entrenar modelos supervisados.
- Conjunto desafio: **7** preguntas ambiguas, externas o que requieren validacion.
- Los splits no comparten frases; la validacion automatica del dataset debe producir una lista vacia.
- La evaluacion no llama a Gemini, por lo que no consume tokens externos ni depende de disponibilidad de red.

## Calidad de clasificacion

| Metrica | Split test reservado | Desafio |
|---|---:|---:|
| Precision micro | 90.00% | 42.86% |
| Recall micro | 90.00% | 42.86% |
| F1 micro | 90.00% | 42.86% |
| Precision macro | 95.33% | 25.00% |
| Recall macro | 90.00% | 25.00% |
| F1 macro | 91.82% | 25.00% |

El resultado del conjunto desafio debe interpretarse por separado: contiene deliberadamente preguntas que el sistema debe aclarar, rechazar de forma segura o remitir a administracion, no responder con seguridad artificial.

## Reduccion de dependencia generativa

| Decision del motor en test | Casos | Tasa |
|---|---:|---:|
| Respuesta local directa | 74 | 61.67% |
| Solicita aclaracion | 35 | 29.17% |
| Respuesta segura sin inventar | 5 | 4.17% |
| Candidata a respaldo Gemini | 6 | 5.00% |
| Llamadas reales a Gemini en esta prueba | 0 | 0.00% |

## Evidencia operativa en produccion

El endpoint protegido de diagnostico fue consultado el `2026-06-10T15:52:45.2727977Z`. En su ventana real de 24 horas reporto:

| Indicador operativo | Resultado |
|---|---:|
| Consultas registradas | 3 |
| Resueltas sin Gemini | 3 |
| Uso real de Gemini | 0 |
| Tokens de IA externa estimados | 0 |
| Tokens ahorrados estimados | 9281 |
| Porcentaje sin Gemini | 100.00% |

Esta evidencia confirma que la politica local primero funciona en produccion, pero la muestra es pequena. No debe usarse por si sola para afirmar un porcentaje general de uso futuro.

## Comparacion con alternativas

Modelo seleccionado: **Hibrido local de produccion** (`hibrido_produccion_kb`).

| Modelo | Validation F1 | Test F1 | Challenge F1 | Puntaje generalizacion |
|---|---:|---:|---:|---:|
| Hibrido local de produccion | 0.8583 | 0.9000 | 0.5714 | 0.8053 |
| Ensamble TF-IDF palabra/caracter 0.35/0.65 | 0.6500 | 0.7083 | 0.5714 | 0.6566 |
| TF-IDF centroides por caracteres | 0.6583 | 0.7000 | 0.5714 | 0.6553 |
| Ensamble TF-IDF palabra/caracter 0.50/0.50 | 0.6583 | 0.6917 | 0.5714 | 0.6516 |
| TF-IDF centroides por palabra | 0.6583 | 0.6667 | 0.5714 | 0.6394 |
| Ensamble TF-IDF palabra/caracter 0.65/0.35 | 0.6583 | 0.7000 | 0.4286 | 0.6196 |
| Baseline por palabras clave | 0.6000 | 0.6500 | 0.5714 | 0.6154 |

## Concurrencia y multiples roles

- Solicitudes concurrentes: **600** con **20** workers.
- Solicitudes exitosas: **600**.
- Errores: **0**.
- Contaminaciones de cache entre solicitudes: **0**.
- Throughput aproximado: **12305.4 solicitudes/s**.
- Latencia p95: **0.0409 ms**.
- Calentamiento previo separado: **4.87 ms**.
- Roles simulados: `{'RESIDENTE': 450, 'VIGILANTE': 75, 'ADMINISTRADOR': 75}`.

La prueba verifica que solicitudes simultaneas de residentes, vigilancia y administracion no comparten resultados mutables. La persistencia y propiedad de conversaciones se valida adicionalmente mediante pruebas automatizadas del backend.

## Pruebas automatizadas de aislamiento y persistencia

- Modulo asistente: **79 pruebas + 14 subpruebas**, 0 fallos.
- Regresion backend completa: **208 pruebas + 20 subpruebas**, 0 fallos.
- Casos especificos aprobados:
  - `test_conversacion_persiste_y_se_recupera_completa`
  - `test_dos_usuarios_no_mezclan_conversaciones_mensajes_ni_logs`
  - `test_lista_solo_conversaciones_del_usuario_autenticado`
  - `test_no_permite_acceder_conversaciones_de_otro_usuario`
  - `test_cache_local_es_aislado_en_solicitudes_concurrentes`

## Intenciones con menor F1 en split test

| Intencion | Precision | Recall | F1 | Soporte |
|---|---:|---:|---:|---:|
| `gestion_avisos` | 0.6250 | 0.8333 | 0.7143 | 6 |
| `clasificacion_incidente` | 1.0000 | 0.6667 | 0.8000 | 6 |
| `reportar_incidente` | 1.0000 | 0.6667 | 0.8000 | 6 |
| `tramites_administrativos` | 1.0000 | 0.6667 | 0.8000 | 6 |
| `funcionamiento_asistente` | 0.8333 | 0.8333 | 0.8333 | 6 |

## Errores observados

| Pregunta | Esperada | Predicha | Accion |
|---|---|---|---|
| Me ayudas con esto: como solicito un paz y salvo? | `tramites_administrativos` | `funcionamiento_asistente` | `fallback_allowed` |
| tengo deuda | `tramites_administrativos` | `sin_intencion_confiable` | `safe` |
| aclaracion duda confianza | `funcionamiento_asistente` | `sin_intencion_confiable` | `safe` |
| bolsas tiradas | `convivencia_entorno` | `sin_intencion_confiable` | `safe` |
| Que incidentes van como Convivencia? en incidentes | `clasificacion_incidente` | `gestion_avisos` | `clarify` |
| poste apagado en incidentes | `clasificacion_incidente` | `gestion_avisos` | `clarify` |
| Como redacto bien un reporte? en incidentes | `reportar_incidente` | `gestion_avisos` | `clarify` |
| No entiendo lo de registrado y estado, que hago? | `seguimiento_incidente` | `sin_intencion_confiable` | `safe` |
| comunicado arriba en notificaciones | `gestion_avisos` | `gestion_notificaciones` | `clarify` |
| q hago si veo una persona sospechosa | `seguridad_control` | `sin_intencion_confiable` | `safe` |

## Limitaciones declaradas

- El dataset fue construido a partir del dominio de CommuSafe; puede representar mejor preguntas previstas que lenguaje completamente inesperado de usuarios reales.
- El conjunto desafio es pequeno y debe ampliarse con consultas reales anonimizadas despues de la puesta en uso.
- El test usa frases separadas, pero generadas desde el mismo dominio y las mismas FAQ; por ello puede sobreestimar el comportamiento ante lenguaje completamente nuevo.
- El ahorro de tokens es estimado con el estimador interno; no representa una factura exacta de Google.
- La evidencia operativa de produccion contiene solo tres consultas en su ventana de 24 horas y se presenta como observacion complementaria.
- La prueba concurrente mide el motor local y el equipo actual; no reemplaza pruebas distribuidas de larga duracion sobre produccion.
- Una tasa baja de Gemini no significa que Gemini sea innecesario: conserva valor como respaldo controlado para consultas no cubiertas.

## Reproduccion

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py generar_evidencia_tecnica_asistente
.\.venv\Scripts\python.exe -m pytest asistente -q
```

La matriz de confusion completa, metricas por intencion y errores detallados se encuentran en el JSON generado junto a este informe.
