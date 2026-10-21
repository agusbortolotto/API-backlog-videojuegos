# API Backlog de Videojuegos

API desarrollada con FastAPI y SQLite para registrar videojuegos,
consultarlos, actualizar su estado y eliminarlos.

## Desarrollo local y pruebas

Requisito: Python 3.13.

Clonar el repositorio y entrar en su carpeta:

```bash
git clone https://github.com/agusbortolotto/API-backlog-videojuegos.git
cd API-backlog-videojuegos
```

Crear y activar un entorno virtual en macOS o Linux:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Comprobar la versión e instalar las dependencias de desarrollo:

```bash
python --version
python -m pip install -r requirements-dev.txt
```

La versión mostrada debe ser Python 3.13.x. En macOS, `python3`
puede apuntar a otra versión; por eso se utiliza `python3.13`
al crear el entorno.

Ejecutar los controles:

```bash
ruff check app tests
python -m pytest -q
git diff --check
```

La suite actual contiene 18 tests que cubren validaciones de datos,
operaciones de la API, inicialización de SQLite y logs JSON.

Para iniciar la API localmente:

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

La aplicación crea automáticamente la base y su esquema al arrancar.
No se necesitan credenciales de Grafana para ejecutar la API ni los tests.

Detener el servidor con Ctrl+C.

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

## Ejecutar la imagen publicada en Docker Hub

Las imágenes se publican en el repositorio público:

https://hub.docker.com/r/agusbortolotto/api-backlog-videojuegos

Para descargar la versión 1.1.0:

```bash
docker pull agusbortolotto/api-backlog-videojuegos:1.1.0
```

Ejecutarla:

```bash
docker run --rm --name api-backlog-release \
  -p 127.0.0.1:8002:8000 \
  agusbortolotto/api-backlog-videojuegos:1.1.0
```

- API: http://127.0.0.1:8002
- Swagger: http://127.0.0.1:8002/docs
- Listado: http://127.0.0.1:8002/juegos

No es necesario clonar el repositorio ni instalar Python para esta
ejecución. Docker Desktop debe estar iniciado si se utiliza macOS.

La base SQLite se crea automáticamente dentro del contenedor.
Este comando no monta un volumen: al detenerlo con Ctrl+C, el
contenedor y sus datos se eliminan. Para conservar datos, utilizar
la configuración de Compose documentada anteriormente.

### Versionado y publicación

Se utiliza Semantic Versioning: MAJOR.MINOR.PATCH.

Al publicar una release en GitHub, por ejemplo `v1.1.0`, se ejecuta
el workflow de publicación:

1. Valida el código mediante Ruff, pytest y construcción Docker.
2. Si las validaciones pasan, construye y publica la imagen
   con la etiqueta `1.1.0`.
3. Publica soporte para linux/amd64 y linux/arm64.

El tag Git identifica el código de la release y los metadatos
de la imagen incluyen información de su origen. El workflow
no genera la etiqueta `latest`.

La versión 1.1.0 incorpora los logs HTTP estructurados en JSON.
La configuración de Alloy y el dashboard se encuentran en el
repositorio. Alloy se ejecuta mediante Compose y el dashboard se importa
en Grafana siguiendo las instrucciones de observabilidad.

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

## Dashboard HTTP

El dashboard propio incluye tráfico, latencia p50/p95 y errores HTTP 4xx/5xx.
La definición exportada, las consultas, las instrucciones de importación y la
prueba de fallo controlado están en [observability/README.md](observability/README.md).

## Informe técnico

El [informe técnico](docs/informe-tecnico.md) describe la arquitectura
del pipeline, las decisiones de diseño, la aplicación de DevOps y Lean,
los experimentos controlados y los resultados de validación.
