# backend_python/test.py
import requests
from fastapi import FastAPI, HTTPException

BASE = "http://localhost:8181/ords/lf12"
app = FastAPI()

@app.get("/api/countries")
def countries():
    try:
        r = requests.get(f"{BASE}/wf_countries/", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}")
