# Seleccion de modelo local del asistente CommuSafe

Este reporte es generado por `python manage.py evaluar_modelos_asistente`.

## Dataset

| Split | Ejemplos |
|---|---:|
| train | 480 |
| validation | 120 |
| test | 120 |
| challenge | 24 |
| intenciones | 20 |

## Criterio de seleccion

El modelo se selecciona por un puntaje interno ponderado de validation, test controlado y challenge de desarrollo, penalizando sobreajuste y respuestas directas incorrectas. Este puntaje sirve para comparar candidatos, pero no reemplaza el holdout final independiente.

## Ranking

| Modelo | Validation F1 | Test F1 | Challenge desarrollo | Puntaje interno | Directas incorrectas test |
|---|---:|---:|---:|---:|---:|
| Hibrido local de produccion | 0.8583 | 0.9000 | 0.9583 | 0.9021 | 0 |
| Ensamble TF-IDF palabra/caracter 0.35/0.65 | 0.6583 | 0.7167 | 0.3750 | 0.6138 | 0 |
| TF-IDF centroides por caracteres | 0.6667 | 0.7083 | 0.3750 | 0.6125 | 0 |
| Ensamble TF-IDF palabra/caracter 0.65/0.35 | 0.6667 | 0.7083 | 0.3750 | 0.6125 | 0 |
| Ensamble TF-IDF palabra/caracter 0.50/0.50 | 0.6667 | 0.7000 | 0.3750 | 0.6088 | 0 |
| TF-IDF centroides por palabra | 0.6667 | 0.6750 | 0.4167 | 0.6067 | 0 |
| Baseline por palabras clave | 0.6083 | 0.6583 | 0.4167 | 0.5829 | 0 |

## Modelo seleccionado

- **Modelo:** Hibrido local de produccion
- **ID:** `hibrido_produccion_kb`
- **Puntaje de comparacion interna:** 0.9021
- **Configuracion:** `{'high_threshold': 0.52, 'medium_threshold': 0.28, 'ambiguity_margin': 0.04}`

## Limitaciones observadas

- El dataset es controlado y debe complementarse con preguntas reales de usuarios despues de la sustentacion.
- El split challenge muestra que preguntas muy ambiguas o fuera de dominio deben resolverse con aclaracion o respuesta segura, no con respuesta directa.
- No se uso un modelo neuronal externo para clasificacion local porque el tamano del dataset no justifica una dependencia pesada en produccion.
- En test quedaron 12 errores operacionales revisables; los primeros casos quedan en el JSON de evidencia.
- En challenge quedaron 1 errores o rechazos seguros esperados por ambiguedad o falta de informacion verificable.
