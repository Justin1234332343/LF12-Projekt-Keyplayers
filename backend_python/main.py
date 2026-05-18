from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ords_service import build_ords_service

app = FastAPI(title="LF12 Keyplayers API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ords = build_ords_service()


# ------------------------------------------------------------------ SCHEMAS

class FirmaKomplettRequest(BaseModel):
    firma_name: str
    rechnungsadresse: str
    email_rechnungsversand: str
    kommentar: Optional[str] = None
    ap_vorname: str
    ap_nachname: str
    ap_email: str
    ap_telefon: Optional[str] = None
    ap_position: Optional[str] = None


class KursKomplettRequest(BaseModel):
    kurs_name: str
    kurs_typ: str
    kurs_ort: Optional[str] = "online (MS Teams)"
    kurs_datum_beginn: str
    kurs_datum_ende: str
    kurs_zeitraum: str
    kurs_tage: int
    kommentar: Optional[str] = None
    seminaragenda_id: Optional[int] = None
    termine: List[Dict[str, str]]


class TeilnehmerRequest(BaseModel):
    firma_id: int
    vorname: str
    nachname: str
    email: str


class TeilnehmerStatusRequest(BaseModel):
    status_id: int


class AngebotRequest(BaseModel):
    firma_id: int
    kurs_id: int
    angebot_betrag: float


class AngebotStatusRequest(BaseModel):
    status: str
    zahltermin_tage: Optional[int] = 30


class ZahlungRequest(BaseModel):
    betrag: float
    zahlungsmethode: str


class BenachrichtigungRequest(BaseModel):
    empfaenger_id: int
    empfaenger_typ: str
    betreff: str
    inhalt: str


# ------------------------------------------------------------------ HEALTH

@app.get("/health")
def health() -> Dict:
    return {"status": "ok"}


# ------------------------------------------------------------------ FIRMEN

@app.get("/firmen/", response_model=List[Any])
def list_firmen():
    return ords.list_firmen()


@app.get("/firmen/{firma_id}")
def get_firma(firma_id: int):
    return ords.get_firma(firma_id)


@app.post("/firmen/komplett/", status_code=201)
def create_firma_komplett(body: FirmaKomplettRequest):
    return ords.create_firma_komplett(body.model_dump())


@app.put("/firmen/{firma_id}")
def update_firma(firma_id: int, body: Dict[str, Any]):
    return ords.update_firma(firma_id, body)


@app.delete("/firmen/{firma_id}", status_code=204)
def delete_firma(firma_id: int):
    ords.delete_firma(firma_id)


@app.get("/firmen/{firma_id}/ansprechpartner/")
def list_ansprechpartner(firma_id: int):
    return ords.list_ansprechpartner(firma_id=firma_id)


# ------------------------------------------------------------------ KURSE

@app.get("/kurse/", response_model=List[Any])
def list_kurse():
    return ords.list_kurse()


@app.get("/kurse/{kurs_id}")
def get_kurs(kurs_id: int):
    return ords.get_kurs(kurs_id)


@app.get("/kurse/{kurs_id}/detail")
def get_kurs_detail(kurs_id: int):
    return ords.get_kurs_detail(kurs_id)


@app.post("/kurse/komplett/", status_code=201)
def create_kurs_komplett(body: KursKomplettRequest):
    return ords.create_kurs_komplett(body.model_dump())


@app.put("/kurse/{kurs_id}")
def update_kurs(kurs_id: int, body: Dict[str, Any]):
    return ords.update_kurs(kurs_id, body)


@app.delete("/kurse/{kurs_id}", status_code=204)
def delete_kurs(kurs_id: int):
    ords.delete_kurs(kurs_id)


# --------------------------------------------------------------- TEILNEHMER

@app.get("/teilnehmer/", response_model=List[Any])
def list_teilnehmer():
    return ords.list_teilnehmer()


@app.get("/teilnehmer/{teilnehmer_id}")
def get_teilnehmer(teilnehmer_id: int):
    return ords.get_teilnehmer(teilnehmer_id)


@app.post("/teilnehmer/", status_code=201)
def create_teilnehmer(body: TeilnehmerRequest):
    return ords.create_teilnehmer(body.model_dump())


@app.put("/teilnehmer/{teilnehmer_id}/status")
def update_teilnehmer_status(teilnehmer_id: int, body: TeilnehmerStatusRequest):
    return ords.update_teilnehmer_status(teilnehmer_id, body.status_id)


@app.get("/teilnehmer-status/")
def list_teilnehmer_status():
    return ords.list_teilnehmer_status()


# ----------------------------------------------------------------- ANGEBOTE

@app.get("/angebote/", response_model=List[Any])
def list_angebote():
    return ords.list_angebote()


@app.get("/angebote/{angebot_id}")
def get_angebot(angebot_id: int):
    return ords.get_angebot(angebot_id)


@app.post("/angebote/", status_code=201)
def create_angebot(body: AngebotRequest):
    return ords.create_angebot(body.model_dump())


@app.put("/angebote/{angebot_id}/status")
def update_angebot_status(angebot_id: int, body: AngebotStatusRequest):
    return ords.update_angebot_status(angebot_id, body.status, body.zahltermin_tage)


# --------------------------------------------------------------- RECHNUNGEN

@app.get("/rechnungen/", response_model=List[Any])
def list_rechnungen():
    return ords.list_rechnungen()


@app.get("/rechnungen/{rechnungsnummer}")
def get_rechnung(rechnungsnummer: int):
    return ords.get_rechnung(rechnungsnummer)


@app.post("/rechnungen/{rechnungsnummer}/zahlung/", status_code=201)
def zahlung_erfassen(rechnungsnummer: int, body: ZahlungRequest):
    return ords.zahlung_erfassen(rechnungsnummer, body.betrag, body.zahlungsmethode)


# --------------------------------------------------------- BENACHRICHTIGUNGEN

@app.get("/benachrichtigungen/", response_model=List[Any])
def list_benachrichtigungen():
    return ords.list_benachrichtigungen()


@app.post("/benachrichtigungen/", status_code=201)
def create_benachrichtigung(body: BenachrichtigungRequest):
    return ords.create_benachrichtigung(body.model_dump())
