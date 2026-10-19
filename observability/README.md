# Dashboard de observabilidad

El tablero se construyó desde cero en Grafana Cloud, sin importar plantillas. La definición exportada está en `dashboard.json`.

## Arquitectura

API FastAPI → salida estándar del contenedor → Grafana Alloy → Grafana Cloud Logs (Loki) → dashboard. Las tres señales HTTP se calculan desde logs JSON; no hay instrumentación Prometheus adicional en esta etapa.

## Importar el tablero

1. Configurar el envío de logs siguiendo el README principal.
2. En Grafana, abrir **Dashboards → New → Import**.
3. Cargar `observability/dashboard.json`. Es una exportación de Grafana Cloud con formato `dashboard.grafana.app/v2`; se necesita una instancia compatible con ese formato.
4. Asociar la fuente Loki solicitada por la importación con la fuente de logs de la instancia de destino. Si conserva la referencia del origen, editar las consultas y seleccionar esa fuente.
5. Guardar, seleccionar **Last 15 minutes** y generar tráfico sobre la API.

La exportación se realizó con **Share dashboard with another instance** habilitado. No contiene tokens ni la configuración de autenticación de la fuente de datos.

## Paneles y consultas

Cada punto usa una ventana móvil de un minuto. La fuente de datos es Loki, con consultas de tipo Range.

### Tráfico HTTP

Peticiones HTTP por segundo, promediadas sobre una ventana de un minuto. Cuenta solo los eventos JSON de la API.

**A**

```logql
sum(rate({service_name="api-backlog"} | json | __error__="" | status_code != "" [1m]))
```

### Latencia HTTP — p50 y p95

Percentiles p50 y p95 de duration_ms en ventanas de un minuto. Tiempo de procesamiento hasta obtener la respuesta; no incluye el viaje de red al cliente.

**p50**

```logql
quantile_over_time(0.50, {service_name="api-backlog"} | json | status_code != "" | unwrap duration_ms | __error__="" [1m]) by (service_name)
```

**p95**

```logql
quantile_over_time(0.95, {service_name="api-backlog"} | json | status_code != "" | unwrap duration_ms | __error__="" [1m]) by (service_name)
```

### Errores HTTP — 4xx y 5xx (último minuto)

Cantidad de respuestas 4xx y 5xx en ventanas móviles de un minuto. Solo eventos JSON. Cero significa que no se encontraron errores en los logs recibidos; no verifica disponibilidad.

**4xx**

```logql
sum(count_over_time({service_name="api-backlog"} | json | status_code >= 400 | status_code < 500 | __error__="" [1m])) or vector(0)
```

**5xx**

```logql
sum(count_over_time({service_name="api-backlog"} | json | status_code >= 500 | status_code < 600 | __error__="" [1m])) or vector(0)
```

## Interpretación y límites

- Tráfico: peticiones por segundo, promediadas en el último minuto.
- Latencia: p50 y p95 de `duration_ms`, en milisegundos y agrupados por servicio. Es tiempo hasta obtener la respuesta dentro del middleware; no mide el viaje de red al cliente ni la transferencia completa de respuestas en streaming.
- Errores: conteo de respuestas 4xx y 5xx en el último minuto; no es un porcentaje. `or vector(0)` dibuja cero si no hay coincidencias, por lo que no debe utilizarse para inferir disponibilidad o salud del recolector.
- `json` y `__error__` excluyen los registros de texto de Uvicorn y evitan duplicar peticiones.
- Con pocas peticiones, los percentiles son poco representativos. Sin logs recientes, tráfico y latencia pueden mostrar huecos.
- Los eventos se consultan en UTC internamente y Grafana los presenta en la zona horaria del navegador.

## Prueba controlada de error 500

El 19 de octubre de 2026 se inició un contenedor temporal con la misma imagen local, sin montar el volumen SQLite habitual. En ese proceso se agregó una ruta que lanza una excepción. Se verificaron respuestas 200, 404 y 500; la curva 5xx mostró un evento y la API habitual siguió respondiendo 200. El contenedor temporal se detuvo y eliminó después.

Para repetir la prueba, mantener API y Alloy activos y construir primero la imagen local:

```bash
docker compose --profile observabilidad up --build -d
```

Luego ejecutar, desde la raíz del repositorio:

```bash
docker run --detach --rm \
  --name api-backlog-prueba-500 \
  --label telemetry.service=api-backlog \
  --publish 127.0.0.1:8004:8000 \
  --mount "type=bind,source=$PWD/observability/simular_fallo.py,target=/tmp/simular_fallo.py,readonly" \
  api-backlog:local \
  python -c 'exec(compile(open("/tmp/simular_fallo.py").read(), "/tmp/simular_fallo.py", "exec"))'
```

Esperar a que arranque y generar el error:

```bash
curl -i http://127.0.0.1:8004/__prueba_500
```

La respuesta esperada es HTTP 500. Alloy debe descubrir el contenedor; puede tardar alrededor de un minuto. Mantenerlo activo hasta ver el evento en Explore y el gráfico 5xx. Consulta de verificación:

```logql
{service_name="api-backlog"} | json | path="/__prueba_500" | status_code=500 | __error__=""
```

Comprobar también `http://127.0.0.1:8001/` y luego retirar la prueba:

```bash
docker stop api-backlog-prueba-500
```

La ruta de fallo existe solo en ese proceso temporal; no se agrega a los endpoints de la API habitual. No se modifican sus datos.

## Evidencias

- [Tráfico HTTP](evidencias/grafana-trafico.jpg).
- [Latencia p50/p95](evidencias/grafana-latencia.jpg).
- [Cinco respuestas 404](evidencias/grafana-errores.jpg).
- [Error 500 controlado visible en la curva 5xx](evidencias/grafana-fallo-500.jpg).

Estas capturas muestran actividad real del entorno local enviada a Grafana Cloud. El experimento amplía el feedback de fallos desde CI hacia la observabilidad en ejecución; no se configuró una alerta automática en esta etapa.
