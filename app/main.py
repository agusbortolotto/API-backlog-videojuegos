import sqlite3
from pathlib import Path
from typing import Literal

EstadoJuego = Literal["sin jugar", "jugando", "terminado", "abandonado"]

from fastapi import FastAPI

RUTA_DB = Path(__file__).resolve().parent.parent / "database" / "backlog.db"

app = FastAPI()


@app.get("/")
def raiz():
    return {"mensaje": "API funcionando correctamente"}


@app.get("/juegos")
def obtener_juegos(estado: EstadoJuego | None = None):
    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row

    if estado is None:
        filas = conexion.execute("SELECT * FROM juegos").fetchall()
    else:
        filas = conexion.execute("SELECT * FROM juegos WHERE estado = ?",
                                  (estado,)
                                  ).fetchall()

    conexion.close()

    return [dict(fila) for fila in filas]

