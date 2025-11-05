from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .ords_service import OrdsService

app = FastAPI(title="LF12 Python Backend")

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ords = OrdsService(base_url=settings.ORDS_BASE_URL)

@app.get("/health")
def health():
    return {"status": "ok"}

# Beispiel: Countries-Liste via ORDS (GET /api/countries -> ORDS /wf_countries/)
@app.get("/api/countries")
def list_countries():
    try:
        data = ords.get("wf_countries/")
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ORDS upstream error: {e}")

# Allgemeiner, sicherer Read-Through (nur GET) auf erlaubte Ressourcen
ALLOWED_READ_PATHS = {
    "wf_countries/": "wf_countries/",
    # weitere erlaubte Ressourcen hier whitelisten...
}

@app.get("/api/{resource}")
def passthrough(resource: str):
    path = f"{resource.strip('/')}/"
    if path not in ALLOWED_READ_PATHS:
        raise HTTPException(status_code=404, detail="Resource not allowed")
    try:
        return ords.get(ALLOWED_READ_PATHS[path])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ORDS upstream error: {e}")
