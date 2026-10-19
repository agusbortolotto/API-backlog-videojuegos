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

## Observabilidad con Grafana Cloud

La API emite logs HTTP en formato JSON con timestamp UTC, nivel,
mensaje, ruta, código de respuesta, método y duración en milisegundos.

Grafana Alloy recoge los logs del contenedor identificado con
`telemetry.service=api-backlog` y los envía a Grafana Cloud Logs (Loki).

### Configuración

Crear una política de acceso en Grafana Cloud, limitada al stack
del proyecto y con permiso `logs:write`. Generar un token asociado.

En una instalación nueva, copiar el archivo de ejemplo:

```bash
cp .env.example .env
```

Completar `.env` con el endpoint de envío de Loki, su usuario numérico
y el token. Si `.env` ya existe, editarlo sin sobrescribirlo.

`.env` queda excluido de Git y del contexto de construcción Docker.

### Ejecutar con monitoreo

```bash
docker compose --profile observabilidad up --build -d
docker compose --profile observabilidad ps
docker compose logs --tail=50 alloy
```

Sin el perfil `observabilidad`, el comando habitual levanta solo la API.

Alloy utiliza el socket de Docker para descubrir el contenedor y leer
sus logs. El acceso al socket permite operaciones sobre el motor;
el montaje `:ro` no restringe los métodos de la API de Docker.

### Verificar recepción

Generar peticiones a `/` y `/no-existe`.

En Grafana, abrir Explore, seleccionar la fuente de Loki y consultar:

```logql
{service_name="api-backlog"}
```

Para mostrar únicamente los eventos JSON de peticiones:

```logql
{service_name="api-backlog"} | json | __error__="" | status_code != ""
```

Esto excluye los registros de texto de Uvicorn y evita contar
una petición dos veces al construir gráficos.

### Detener el entorno

```bash
docker compose --profile observabilidad down
```

Sin `-v`, se conservan los volúmenes de SQLite y del recolector.
Los registros ya enviados permanecen en Grafana Cloud según su retención.