# API Backlog de Videojuegos

API desarrollada con FastAPI y SQLite para registrar videojuegos,
consultarlos, actualizar su estado y eliminarlos.

## Ejecutar con Docker

Requisitos: Docker y Docker Compose disponibles.
En macOS, Docker Desktop debe estar iniciado.

Desde la raíz del repositorio:

```bash
docker compose up --build -d
```

- API: http://127.0.0.1:8001
- Documentación interactiva: http://127.0.0.1:8001/docs
- Listado de juegos: http://127.0.0.1:8001/juegos

SQLite se inicializa automáticamente al arrancar la aplicación.

## Consultar estado y logs

```bash
docker compose ps
docker compose logs -f api
```

## Detener el entorno

```bash
docker compose down
```

Este comando elimina el contenedor y conserva los datos en el volumen
`backlog_data`. Al levantar el entorno nuevamente, se reutiliza ese volumen.

Para eliminar también el volumen y todos los datos:

```bash
docker compose down -v
```

## Imagen Docker

El Dockerfile utiliza dos etapas:

- `builder`: instala las dependencias en un entorno virtual.
- `runtime`: incorpora ese entorno, el código y el esquema SQL.

La base es `python:3.13.16-slim-bookworm`.
La aplicación se ejecuta con un usuario sin privilegios.
Las dependencias se copian antes que el código para aprovechar la caché.
`.dockerignore` excluye el entorno virtual local y las bases de datos.