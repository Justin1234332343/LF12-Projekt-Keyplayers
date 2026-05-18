import os
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
            raise HTTPException(
                status_code=resp.status_code if 400 <= resp.status_code < 600 else 502,
                detail={"error": "ORDS error", "status_code": resp.status_code, "text": resp.text[:2000]},
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

    # ------------------------------------------------------------------ FIRMA
    def list_firmen(self) -> List[Dict]:
        return self._items(self._get("firma/"))

    def get_firma(self, firma_id: int) -> Dict:
        return self._get(f"firma/{firma_id}")

    def create_firma_komplett(self, payload: Dict) -> Dict:
        return self._post("api/v1/firmen/komplett/", payload)

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
        return self._get(f"api/v1/kurse/{kurs_id}/detail")

    def create_kurs_komplett(self, payload: Dict) -> Dict:
        return self._post("api/v1/kurse/komplett/", payload)

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
        return self._post("teilnehmer/", payload)

    def update_teilnehmer_status(self, teilnehmer_id: int, status_id: int) -> Dict:
        return self._put(f"api/v1/teilnehmer/{teilnehmer_id}/status", {"status_id": status_id})

    # ----------------------------------------------------------------- ANGEBOT
    def list_angebote(self) -> List[Dict]:
        return self._items(self._get("angebot/"))

    def get_angebot(self, angebot_id: int) -> Dict:
        return self._get(f"angebot/{angebot_id}")

    def create_angebot(self, payload: Dict) -> Dict:
        return self._post("angebot/", payload)

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
        return self._post("benachrichtigung/", payload)

    # --------------------------------------------------------- TEILNEHMER STATUS
    def list_teilnehmer_status(self) -> List[Dict]:
        return self._items(self._get("teilnehmer_status/"))


def build_ords_service() -> OrdsService:
    base = os.getenv("ORDS_BASE_URL", "http://ords:8080/ords/projekt_lf12")
    timeout = float(os.getenv("ORDS_TIMEOUT", "10"))
    return OrdsService(base_url=base, timeout=timeout)
