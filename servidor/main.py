from fastapi import FastAPI

app = FastAPI(title="Agenda de Citas - Cypherstudios")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "agenda-api"}
