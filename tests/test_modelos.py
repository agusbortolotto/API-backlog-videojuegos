import pytest
from pydantic import ValidationError

from app.main import JuegoCrear


def test_rechaza_titulo_vacio():
    with pytest.raises(ValidationError):
        JuegoCrear(
            titulo="   ",
            plataforma="PC",
            tienda="Steam",
            estado="jugando",
        )

def test_acepta_juego_valido_y_limpia_titulo():
    juego = JuegoCrear(
        titulo="   Hades   ",
        plataforma="PC",
        tienda="Steam",
        estado="jugando",
    )

    assert juego.titulo == "Hades"
    assert juego.plataforma == "PC"
    assert juego.tienda == "Steam"
    assert juego.estado == "jugando"

def test_rechaza_pc_sin_tienda():
    with pytest.raises(ValidationError):
        JuegoCrear(
            titulo="Cyberpunk 2077",
            plataforma="PC",
            tienda=None,
            estado="jugando",
        )

def test_rechaza_consola_con_tienda():
    with pytest.raises(ValidationError):
        JuegoCrear(
            titulo="God of War",
            plataforma="PlayStation",
            tienda="Steam",
            estado="terminado",
        )
