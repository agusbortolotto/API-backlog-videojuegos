import sqlite3
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, field_validator, model_validator

EstadoJuego = Literal["sin jugar", "jugando", "terminado", "abandonado"]
PlataformaJuego = Literal["PlayStation", "Xbox", "Switch", "PC"]
TiendaJuego = Literal["Steam", "Epic Games", "GOG"]

RUTA_DB = Path(__file__).resolve().parent.parent / "database" / "backlog.db"


class JuegoCrear(BaseModel):
    titulo: str
    plataforma: PlataformaJuego
    tienda: TiendaJuego | None = None
    estado: EstadoJuego

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, valor: str):
        if not valor.strip():
            raise ValueError("El título no puede estar vacío")

        return valor.strip()

    @model_validator(mode="after")
    def validar_tienda_segun_plataforma(self):
        if self.plataforma == "PC" and self.tienda is None:
            raise ValueError("Los juegos de PC deben especificar una tienda")

        if self.plataforma != "PC" and self.tienda is not None:
            raise ValueError(
                "Los juegos de consola no deben especificar una tienda"
            )

        return self


class JuegoActualizarEstado(BaseModel):
    estado: EstadoJuego


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
        filas = conexion.execute(
            "SELECT * FROM juegos WHERE estado = ?",
            (estado,),
        ).fetchall()

    conexion.close()

    return [dict(fila) for fila in filas]


@app.post("/juegos", status_code=status.HTTP_201_CREATED)
def crear_juego(juego: JuegoCrear):
    conexion = sqlite3.connect(RUTA_DB)

    try:
        cursor = conexion.execute(
            "INSERT INTO juegos (titulo, plataforma, tienda, estado) "
            "VALUES (?, ?, ?, ?)",
            (juego.titulo, juego.plataforma, juego.tienda, juego.estado),
        )
        conexion.commit()
        id_juego = cursor.lastrowid

    except sqlite3.IntegrityError:
        conexion.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El juego ya existe",
        )

    finally:
        conexion.close()

    return {
        "id": id_juego,
        "titulo": juego.titulo,
        "plataforma": juego.plataforma,
        "tienda": juego.tienda,
        "estado": juego.estado,
    }


@app.patch("/juegos/{id}")
def actualizar_estado_juego(id: int, datos: JuegoActualizarEstado):
    conexion = sqlite3.connect(RUTA_DB)

    cursor = conexion.execute(
        "UPDATE juegos SET estado = ? WHERE id = ?",
        (datos.estado, id),
    )

    if cursor.rowcount == 0:
        conexion.rollback()
        conexion.close()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Juego no encontrado",
        )

    conexion.commit()

    conexion.row_factory = sqlite3.Row

    fila = conexion.execute(
        "SELECT * FROM juegos WHERE id = ?",
        (id,),
    ).fetchone()

    conexion.close()

    return dict(fila)


@app.delete("/juegos/{id}")
def eliminar_juego(id: int):
    conexion = sqlite3.connect(RUTA_DB)

    cursor = conexion.execute(
        "DELETE FROM juegos WHERE id = ?",
        (id,),
    )

    if cursor.rowcount == 0:
        conexion.rollback()
        conexion.close()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Juego no encontrado",
        )

    conexion.commit()
    conexion.close()

    return {
        "mensaje": "Juego eliminado correctamente"
    }
