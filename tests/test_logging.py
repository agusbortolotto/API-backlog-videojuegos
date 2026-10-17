import io
import json
import logging
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import main
from app.logging_config import JsonFormatter


@pytest.fixture
def salida_logs(monkeypatch):
    salida = io.StringIO()
    handler = logging.StreamHandler(salida)
    handler.setFormatter(JsonFormatter())

    monkeypatch.setattr(main.logger, "handlers", [handler])

    return salida


@pytest.mark.parametrize(
    ("path", "status_code", "level"),
    [
        ("/", 200, "INFO"),
        ("/no-existe", 404, "WARNING"),
    ],
)
def test_log_peticion(salida_logs, path, status_code, level):
    with TestClient(main.app) as cliente:
        respuesta = cliente.get(path)

    assert respuesta.status_code == status_code

    evento = json.loads(salida_logs.getvalue().strip())

    assert datetime.fromisoformat(evento["timestamp"]).tzinfo is not None
    assert evento["level"] == level
    assert evento["path"] == path
    assert evento["status_code"] == status_code
    assert evento["method"] == "GET"
    assert evento["duration_ms"] >= 0


def test_log_error_interno(salida_logs, monkeypatch, tmp_path):
    with TestClient(
        main.app, raise_server_exceptions=False
    ) as cliente:
        monkeypatch.setattr(
            main,
            "RUTA_DB",
            tmp_path / "carpeta_inexistente" / "prueba.db",
        )

        respuesta = cliente.get("/juegos")

    assert respuesta.status_code == 500

    evento = json.loads(salida_logs.getvalue().strip())

    assert evento["level"] == "ERROR"
    assert evento["path"] == "/juegos"
    assert evento["status_code"] == 500
    assert evento["method"] == "GET"
    assert evento["duration_ms"] >= 0