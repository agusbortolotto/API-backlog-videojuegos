from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def raiz():
    return {"mensaje": "API funcionando correctamente"}
