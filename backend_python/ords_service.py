import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests
from fastapi import HTTPException, status


class OrdsService:
    """Kapselt alle REST-Calls zu ORDS (auto-REST + custom Modul lf12.v1)."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _handle(self, resp: requests.Response) -> Any:
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            try:
                body = resp.json()
                msg = body.get("message") or body.get("error") or resp.text[:300]
            except Exception:
                msg = resp.text[:300]
            raise HTTPException(
                status_code=resp.status_code if 400 <= resp.status_code < 600 else 502,
                detail=f"ORDS {resp.status_code}: {msg}",
            ) from e
        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _items(self, data: Any) -> List[Dict]:
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        if isinstance(data, list):
            return data
        return [data]

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        try:
            return self._handle(self.session.get(self._url(path), params=params, timeout=self.timeout))
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}") from e

    def _post(self, path: str, payload: Dict) -> Any:
        try:
            return self._handle(self.session.post(self._url(path), json=payload, timeout=self.timeout))
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}") from e

    def _put(self, path: str, payload: Dict) -> Any:
        try:
            return self._handle(self.session.put(self._url(path), json=payload, timeout=self.timeout))
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}") from e

    def _delete(self, path: str) -> Any:
        try:
            return self._handle(self.session.delete(self._url(path), timeout=self.timeout))
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}") from e

    @staticmethod
    def _to_iso(s: Optional[str]) -> Optional[str]:
        """Convert any date/datetime string to ISO-8601 with Z suffix (required by ORDS)."""
        if not s:
            return None
        s = s.replace(" ", "T")
        if len(s) == 10:  # bare YYYY-MM-DD
            s += "T00:00:00"
        if not s.endswith("Z") and "+" not in s[10:]:
            s += "Z"
        return s

    # ------------------------------------------------------------------ FIRMA
    def list_firmen(self) -> List[Dict]:
        return self._items(self._get("firma/"))

    def get_firma(self, firma_id: int) -> Dict:
        return self._get(f"firma/{firma_id}")

    def create_firma_komplett(self, payload: Dict) -> Dict:
        firma = self._post("firma/", {k: v for k, v in {
            "firma_name": payload.get("firma_name"),
            "rechnungsadresse": payload.get("rechnungsadresse"),
            "email_rechnungsversand": payload.get("email_rechnungsversand"),
            "kommentar": payload.get("kommentar"),
        }.items() if v is not None})
        firma_id = firma.get("firma_id")
        self._post("ansprechpartner/", {k: v for k, v in {
            "firma_id": firma_id,
            "vorname": payload.get("ap_vorname"),
            "nachname": payload.get("ap_nachname"),
            "email": payload.get("ap_email"),
            "telefonnummer": payload.get("ap_telefon"),
            "positionfirma": payload.get("ap_position"),
        }.items() if v is not None})
        return {"firma_id": firma_id}

    def update_firma(self, firma_id: int, payload: Dict) -> Dict:
        return self._put(f"firma/{firma_id}", payload)

    def delete_firma(self, firma_id: int) -> Any:
        return self._delete(f"firma/{firma_id}")

    # --------------------------------------------------------- ANSPRECHPARTNER
    def list_ansprechpartner(self, firma_id: Optional[int] = None) -> List[Dict]:
        params = {"q": f'{{"firma_id":{firma_id}}}'} if firma_id else None
        return self._items(self._get("ansprechpartner/", params=params))

    # ------------------------------------------------------------------ KURS
    def list_kurse(self) -> List[Dict]:
        return self._items(self._get("kurs/"))

    def get_kurs(self, kurs_id: int) -> Dict:
        return self._get(f"kurs/{kurs_id}")

    def get_kurs_detail(self, kurs_id: int) -> Dict:
        kurs = self._get(f"kurs/{kurs_id}")
        termine_raw = self._items(self._get("kurs_termine/", params={"q": f'{{"kurs_id":{kurs_id}}}'}))
        kurs["termine"] = termine_raw
        return kurs

    def create_kurs_komplett(self, payload: Dict) -> Dict:
        termine = payload.get("termine", [])
        kurs = self._post("kurs/", {k: v for k, v in {
            "kurs_name": payload.get("kurs_name"),
            "kurs_typ": payload.get("kurs_typ"),
            "kurs_ort": payload.get("kurs_ort") or "online (MS Teams)",
            "kurs_datum_beginn": self._to_iso(payload.get("kurs_datum_beginn")),
            "kurs_datum_ende": self._to_iso(payload.get("kurs_datum_ende")),
            "kurs_zeitraum": payload.get("kurs_zeitraum"),
            "kurs_tage": payload.get("kurs_tage"),
            "kommentar": payload.get("kommentar"),
            "seminaragenda_id": payload.get("seminaragenda_id"),
        }.items() if v is not None})
        kurs_id = kurs.get("kurs_id")
        for t in termine:
            self._post("kurs_termine/", {k: v for k, v in {
                "kurs_id": kurs_id,
                "datum": self._to_iso(t.get("datum")),
                "uhrzeit_start": self._to_iso(t.get("start")),
                "uhrzeit_ende": self._to_iso(t.get("ende")),
            }.items() if v is not None})
        return {"kurs_id": kurs_id}

    def update_kurs(self, kurs_id: int, payload: Dict) -> Dict:
        return self._put(f"kurs/{kurs_id}", payload)

    def delete_kurs(self, kurs_id: int) -> Any:
        return self._delete(f"kurs/{kurs_id}")

    # --------------------------------------------------------------- TEILNEHMER
    def list_teilnehmer(self) -> List[Dict]:
        return self._items(self._get("teilnehmer/"))

    def get_teilnehmer(self, teilnehmer_id: int) -> Dict:
        return self._get(f"teilnehmer/{teilnehmer_id}")

    def create_teilnehmer(self, payload: Dict) -> Dict:
        return self._post("teilnehmer/", {"status_id": 1, **payload})

    def update_teilnehmer_status(self, teilnehmer_id: int, status_id: int) -> Dict:
        return self._put(f"api/v1/teilnehmer/{teilnehmer_id}/status", {"status_id": status_id})

    # ----------------------------------------------------------------- ANGEBOT
    def list_angebote(self) -> List[Dict]:
        return self._items(self._get("angebot/"))

    def get_angebot(self, angebot_id: int) -> Dict:
        return self._get(f"angebot/{angebot_id}")

    def create_angebot(self, payload: Dict) -> Dict:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self._post("angebot/", {"angebot_datum": now, "angebot_status": "offen", **payload})

    def update_angebot_status(self, angebot_id: int, neuer_status: str, zahltermin_tage: int = 30) -> Dict:
        return self._put(
            f"api/v1/angebote/{angebot_id}/status",
            {"status": neuer_status, "zahltermin_tage": zahltermin_tage},
        )

    # --------------------------------------------------------------- RECHNUNG
    def list_rechnungen(self) -> List[Dict]:
        return self._items(self._get("rechnung/"))

    def get_rechnung(self, rechnungsnummer: int) -> Dict:
        return self._get(f"rechnung/{rechnungsnummer}")

    def zahlung_erfassen(self, rechnungsnummer: int, betrag: float, zahlungsmethode: str) -> Dict:
        return self._post(
            f"api/v1/rechnungen/{rechnungsnummer}/zahlung/",
            {"betrag": betrag, "zahlungsmethode": zahlungsmethode},
        )

    # --------------------------------------------------------- BENACHRICHTIGUNG
    def list_benachrichtigungen(self) -> List[Dict]:
        return self._items(self._get("benachrichtigung/"))

    def create_benachrichtigung(self, payload: Dict) -> Dict:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self._post("benachrichtigung/", {"versanddatum": now, **payload})

    # --------------------------------------------------------- TEILNEHMER STATUS
    def list_teilnehmer_status(self) -> List[Dict]:
        return self._items(self._get("teilnehmer_status/"))


def build_ords_service() -> OrdsService:
    base = os.getenv("ORDS_BASE_URL", "http://ords:8080/ords/projekt_lf12")
    timeout = float(os.getenv("ORDS_TIMEOUT", "10"))
    return OrdsService(base_url=base, timeout=timeout)
