# Seleccion de modelo local del asistente CommuSafe

Este reporte es generado por `python manage.py evaluar_modelos_asistente`.

## Dataset

| Split | Ejemplos |
|---|---:|
| train | 480 |
| validation | 120 |
| test | 120 |
| challenge | 7 |
| intenciones | 20 |

## Criterio de seleccion

El modelo se selecciona por puntaje de generalizacion ponderado (validation, test y challenge), penalizando sobreajuste y respuestas directas incorrectas. La precision de entrenamiento no decide la seleccion.

## Ranking

| Modelo | Validation F1 | Test F1 | Challenge F1 | Puntaje | Directas incorrectas test |
|---|---:|---:|---:|---:|---:|
| Hibrido local de produccion | 0.8667 | 0.9167 | 0.5714 | 0.8154 | 0 |
| Ensamble TF-IDF palabra/caracter 0.35/0.65 | 0.6417 | 0.7083 | 0.5714 | 0.6541 | 0 |
| TF-IDF centroides por caracteres | 0.6500 | 0.7000 | 0.5714 | 0.6529 | 0 |
| Ensamble TF-IDF palabra/caracter 0.50/0.50 | 0.6500 | 0.7000 | 0.5714 | 0.6529 | 0 |
| TF-IDF centroides por palabra | 0.6417 | 0.6833 | 0.5714 | 0.6428 | 0 |
| Baseline por palabras clave | 0.6000 | 0.6583 | 0.5714 | 0.6191 | 0 |
| Ensamble TF-IDF palabra/caracter 0.65/0.35 | 0.6500 | 0.7000 | 0.4286 | 0.6171 | 0 |

## Modelo seleccionado

- **Modelo:** Hibrido local de produccion
- **ID:** `hibrido_produccion_kb`
- **Puntaje de generalizacion:** 0.8154
- **Configuracion:** `{'high_threshold': 0.52, 'medium_threshold': 0.28, 'ambiguity_margin': 0.04}`

## Limitaciones observadas

- El dataset es controlado y debe complementarse con preguntas reales de usuarios despues de la sustentacion.
- El split challenge muestra que preguntas muy ambiguas o fuera de dominio deben resolverse con aclaracion o respuesta segura, no con respuesta directa.
- No se uso un modelo neuronal externo para clasificacion local porque el tamano del dataset no justifica una dependencia pesada en produccion.
- En test quedaron 10 errores operacionales revisables; los primeros casos quedan en el JSON de evidencia.
- En challenge quedaron 3 errores o rechazos seguros esperados por ambiguedad o falta de informacion verificable.
