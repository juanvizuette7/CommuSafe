# Plan de pruebas de CommuSafe

## Objetivo

Documentar las pruebas aplicadas al proyecto CommuSafe para validar la calidad, estabilidad, seguridad, disponibilidad y correcto funcionamiento del sistema.

## Alcance

El plan de pruebas contempla los componentes principales del sistema: backend, panel web administrativo, aplicación móvil, integraciones, despliegue y documentación metodológica.

## Tipos de pruebas consideradas

- Pruebas funcionales
- Pruebas exploratorias
- Validación W3C
- Pruebas de accesibilidad
- Pruebas de disponibilidad
- Pruebas de latencia y tiempos de respuesta
- Pruebas de conectividad mediante tracert
- Pruebas de rendimiento
- Pruebas de carga
- Pruebas de usabilidad
- Pruebas de compatibilidad entre navegadores y dispositivos
- Pruebas de seguridad básicas
- Pruebas de despliegue

## Estructura de casos de prueba

Cada caso de prueba debe contener:

- Identificador y nombre de la prueba
- Objetivo de la prueba
- Precondiciones
- Datos de entrada
- Pasos de ejecución
- Resultado esperado
- Resultado obtenido
- Estado de la prueba
- Evidencia mediante pantallazos, capturas o video demostrativo

## Gestión de incidencias

Cuando una prueba no sea superada, se debe registrar el fallo como incidencia dentro del tablero de GitHub Projects. La actividad debe retornar al estado To Do, Product Backlog o Sprint Backlog para que el desarrollador responsable pueda corregir el error y posteriormente realizar una nueva validación.

## Relación con GitHub Projects

Los casos de prueba se gestionan en GitHub Projects dentro del Sprint 5 — QA, pruebas, despliegue y documentación, permitiendo mantener trazabilidad entre pruebas, resultados, responsables, evidencias y estado de avance.
