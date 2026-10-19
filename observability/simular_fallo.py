"""Servidor temporal para simular un 500 sin modificar la aplicación habitual."""

import uvicorn

from app import main


def fallo_controlado():
    raise RuntimeError("Fallo 500 controlado para validar observabilidad del TP")


if __name__ == "__main__":
    main.app.add_api_route(
        "/__prueba_500", fallo_controlado,
        methods=["GET"], include_in_schema=False,
    )
    uvicorn.run(main.app, host="0.0.0.0", port=8000, access_log=False)
