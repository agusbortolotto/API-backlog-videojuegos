import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)

RUTA_SCHEMA = (
    Path(__file__).resolve().parent.parent / "database" / "schema.sql"
)

@pytest.fixture
def base_datos_prueba(tmp_path, monkeypatch):
    ruta_db = tmp_path / "test.db"

    schema = RUTA_SCHEMA.read_text()

    conexion = sqlite3.connect(ruta_db)
    conexion.executescript(schema)
    conexion.close()

    monkeypatch.setattr(main, "RUTA_DB", ruta_db)

    return ruta_db

def test_raiz():
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "mensaje": "API funcionando correctamente"
    }

def test_obtener_juegos_base_vacia(base_datos_prueba):
    respuesta = client.get("/juegos")

    assert respuesta.status_code == 200
    assert respuesta.json() == []

def test_crear_juego_y_persistirlo(base_datos_prueba):
    juego = {
        "titulo": "Hades",
        "plataforma": "PC",
        "tienda": "Steam",
        "estado": "jugando",
    }

    respuesta_post = client.post("/juegos", json=juego)

    assert respuesta_post.status_code == 201

    juego_creado = respuesta_post.json()

    assert juego_creado["id"] == 1
    assert juego_creado["titulo"] == "Hades"
    assert juego_creado["plataforma"] == "PC"
    assert juego_creado["tienda"] == "Steam"
    assert juego_creado["estado"] == "jugando"

def test_rechaza_juego_duplicado(base_datos_prueba):
    juego = {
        "titulo": "Hades",
        "plataforma": "PC",
        "tienda": "Steam",
        "estado": "jugando",
    }

    primera_respuesta = client.post("/juegos", json=juego)
    segunda_respuesta = client.post("/juegos", json=juego)

    assert primera_respuesta.status_code == 201
    assert segunda_respuesta.status_code == 409
    assert segunda_respuesta.json() == {
        "detail": "El juego ya existe"
    }

    respuesta_get = client.get("/juegos")

    assert respuesta_get.status_code == 200
    assert len(respuesta_get.json()) == 1

def test_actualizar_estado_juego(base_datos_prueba):
    juego = {
        "titulo": "Hades",
        "plataforma": "PC",
        "tienda": "Steam",
        "estado": "jugando",
    }

    respuesta_post = client.post("/juegos", json=juego)
    id_juego = respuesta_post.json()["id"]

    respuesta_patch = client.patch(
        f"/juegos/{id_juego}",
        json={"estado": "terminado"},
    )

    assert respuesta_patch.status_code == 200

    juego_actualizado = respuesta_patch.json()

    assert juego_actualizado["id"] == id_juego
    assert juego_actualizado["titulo"] == "Hades"
    assert juego_actualizado["estado"] == "terminado"

    respuesta_get = client.get("/juegos")

    juegos = respuesta_get.json()

    assert len(juegos) == 1
    assert juegos[0]["estado"] == "terminado"

def test_actualizar_juego_inexistente(base_datos_prueba):
    respuesta = client.patch(
        "/juegos/9999",
        json={"estado": "terminado"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json() == {
        "detail": "Juego no encontrado"
    }

def test_eliminar_juego(base_datos_prueba):
    juego = {
        "titulo": "Hades",
        "plataforma": "PC",
        "tienda": "Steam",
        "estado": "jugando",
    }

    respuesta_post = client.post("/juegos", json=juego)
    id_juego = respuesta_post.json()["id"]

    respuesta_delete = client.delete(f"/juegos/{id_juego}")

    assert respuesta_delete.status_code == 200
    assert respuesta_delete.json() == {
        "mensaje": "Juego eliminado correctamente"
    }

    respuesta_get = client.get("/juegos")

    assert respuesta_get.status_code == 200
    assert respuesta_get.json() == []

def test_eliminar_juego_inexistente(base_datos_prueba):
    respuesta = client.delete("/juegos/9999")

    assert respuesta.status_code == 404
    assert respuesta.json() == {
        "detail": "Juego no encontrado"
    }

def test_filtrar_juegos_por_estado(base_datos_prueba):
    juegos = [
        {
            "titulo": "Hades",
            "plataforma": "PC",
            "tienda": "Steam",
            "estado": "jugando",
        },
        {
            "titulo": "God of War",
            "plataforma": "PlayStation",
            "tienda": None,
            "estado": "terminado",
        },
        {
            "titulo": "Cyberpunk 2077",
            "plataforma": "PC",
            "tienda": "GOG",
            "estado": "jugando",
        },
    ]

    for juego in juegos:
        client.post("/juegos", json=juego)

    respuesta = client.get("/juegos?estado=jugando")

    assert respuesta.status_code == 200

    juegos_filtrados = respuesta.json()

    assert len(juegos_filtrados) == 2
    assert all(
        juego["estado"] == "jugando"
        for juego in juegos_filtrados
    )

def test_rechaza_filtro_estado_invalido(base_datos_prueba):
    respuesta = client.get("/juegos?estado=pausado")

    assert respuesta.status_code == 422
