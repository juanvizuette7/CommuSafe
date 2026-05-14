# Despliegue y calidad de CommuSafe

## Objetivo

Documentar las evidencias relacionadas con el despliegue, configuración de producción, pruebas de calidad y aseguramiento técnico del proyecto CommuSafe.

## Despliegue en Render

CommuSafe fue preparado para despliegue en Render, configurando el backend, rutas de producción, archivos multimedia, variables de entorno y ajustes necesarios para permitir el funcionamiento del sistema en un entorno real.

El despliegue permite validar que el backend pueda responder fuera del entorno local y que la aplicación móvil y el panel web puedan comunicarse con el servicio publicado.

## Uso de render.yaml

El archivo `render.yaml` se mantiene versionado en el repositorio como archivo de configuración de despliegue.

Este archivo puede estar en GitHub siempre que no contenga credenciales reales, tokens, claves privadas, contraseñas o valores sensibles.

Los secretos del sistema deben gestionarse mediante variables de entorno en Render o archivos locales no versionados.

## Variables de entorno

Las variables de entorno permiten separar la configuración sensible del código fuente.

Entre las variables gestionadas se encuentran:

- Configuración de Django.
- URL de base de datos.
- Claves secretas.
- Configuración de Firebase.
- Configuración de Gemini API.
- Configuración de correo.
- Parámetros de producción.

## Evidencias de calidad

El proyecto incluye actividades relacionadas con aseguramiento de calidad, tales como:

- Pruebas unitarias del backend.
- Pruebas funcionales del sistema.
- Validación de rendimiento con Loader.io.
- Corrección de rutas multimedia en producción.
- Optimización del despliegue en Render.
- Validación de comunicación entre backend, web y móvil.
- Documentación metodológica y de calidad.

## Relación con Sprint 5

Esta documentación se relaciona directamente con el Sprint 5 — QA, pruebas, despliegue y documentación, donde se consolidaron las actividades finales de validación, pruebas, despliegue y evidencias académicas del proyecto.

## Buenas prácticas aplicadas

- No versionar archivos `.env` con credenciales reales.
- No subir llaves privadas al repositorio.
- Mantener `render.yaml` solo como configuración.
- Gestionar secretos desde Render.
- Documentar ajustes de producción.
- Registrar pruebas y evidencias dentro de GitHub Projects.
