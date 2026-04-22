## Frontend Web de CommuSafe

Esta carpeta centraliza el frontend web del proyecto para separar la capa visual del backend Django.

### Estructura

- `templates/`: plantillas HTML renderizadas por Django.
- `templates/panel/`: vistas del panel administrativo y operativo.
- `static/`: archivos estaticos propios del frontend web.

### Integracion con Django

El backend esta configurado para cargar plantillas desde `frontend/templates/` y archivos estaticos desde `frontend/static/`.

### Estado actual

El panel web sigue usando Django Templates, Tailwind CSS por CDN y Alpine.js. La separacion en esta carpeta mejora la organizacion del repositorio sin cambiar la arquitectura ya implementada.
