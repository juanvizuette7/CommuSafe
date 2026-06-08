# Evidencia de resiliencia y concurrencia del asistente

Fecha de ejecucion: 2026-06-08  
Entorno: backend Django local, motor local del asistente, sin uso de IA externa.

## Objetivo

Verificar que el asistente de CommuSafe pueda atender varias solicitudes simultaneas sin mezclar respuestas, historiales, estado cacheado ni datos entre usuarios o roles. La prueba se concentra en el motor local porque es la primera linea de respuesta del asistente y debe seguir funcionando aunque Gemini, Anthropic o el servicio Flask auxiliar no esten disponibles.

## Comando ejecutado

```powershell
cd backend
python manage.py probar_resiliencia_asistente --requests 80 --workers 8
```

## Resultado real

```json
{
  "estado": "ok",
  "solicitudes": 80,
  "workers": 8,
  "exitosas": 80,
  "errores": [],
  "contaminaciones_cache": 0,
  "duracion_total_ms": 14.776,
  "throughput_aprox_req_s": 5414.22,
  "latencia_ms": {
    "min": 0.013,
    "p50": 0.028,
    "p95": 0.817,
    "max": 1.179,
    "promedio": 0.115
  },
  "acciones": {
    "clarify": 33,
    "answer": 35,
    "safe": 6,
    "fallback_allowed": 6
  },
  "roles": {
    "VIGILANTE": 6,
    "RESIDENTE": 68,
    "ADMINISTRADOR": 6
  },
  "ia_externa_usada": false
}
```

## Interpretacion tecnica

- `contaminaciones_cache = 0`: no se detecto mezcla de respuestas aunque cada hilo intento modificar deliberadamente el resultado recibido.
- `errores = []`: no hubo excepciones bajo concurrencia.
- `ia_externa_usada = false`: las preguntas de la prueba fueron resueltas o clasificadas por el motor local sin consumo de Gemini.
- `p95 = 0.817 ms`: el motor local responde por debajo de un milisegundo en el 95% de las solicitudes medidas en esta ejecucion.
- Las acciones `answer`, `clarify`, `safe` y `fallback_allowed` reflejan la politica esperada: responder cuando hay confianza, pedir aclaracion si la pregunta es ambigua, protegerse ante consultas fuera de dominio y permitir respaldo solo cuando corresponde.

## Correccion aplicada

El motor local ya era stateless, pero `lru_cache` devolvia el mismo diccionario mutable para llamadas repetidas. Se agrego una copia defensiva en `resolve_local_answer()` para que cada request reciba un objeto independiente. Esto evita que metadatos agregados por fallback, errores de proveedor o trazas internas se filtren a otra solicitud concurrente.

## Pruebas automatizadas relacionadas

```powershell
cd backend
python -m pytest asistente/tests.py -q
```

Resultado:

```text
50 passed, 5 subtests passed
```
