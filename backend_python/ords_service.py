# backend_python/ords_service.py
from typing import Any, Dict, List, Optional
import os
import requests
from fastapi import HTTPException, status

class OrdsService:
    """
    Kapselt REST-Calls zu ORDS.
    Nutzt ein requests.Session-Objekt (Keep-Alive, weniger Overhead).
    """
    def __init__(
            self,
            base_url: str,
            api_key: Optional[str] = None,
            timeout: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if api_key:
            # Beispiel für Header-basierten Key; bei Bedarf anpassen
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _full(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self.base_url}/{path}"

    def _handle(self, resp: requests.Response) -> Any:
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            # ORDS-Fehler schön nach vorne reichen
            detail = {
                "status_code": resp.status_code,
                "reason": resp.reason,
                "text": resp.text[:4000],  # Log/Antwort kürzen
            }
            raise HTTPException(
                status_code=resp.status_code if 400 <= resp.status_code < 600 else status.HTTP_502_BAD_GATEWAY,
                detail={"error": "ORDS error", **detail},
            ) from e
        try:
            return resp.json()
        except ValueError:
            return resp.text

    # ---------- WF_COUNTRIES (READ) ----------
    def list_countries(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = self._full("wf_countries/")
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            data = self._handle(resp)
            # ORDS liefert oft {"items": [...], "hasMore": ...}
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            if isinstance(data, list):
                return data
            return [data]
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ORDS nicht erreichbar: {e}",
            ) from e

    def get_country(self, country_id: str) -> Dict[str, Any]:
        url = self._full(f"wf_countries/{country_id}")
        try:
            resp = self.session.get(url, timeout=self.timeout)
            data = self._handle(resp)
            # Manche ORDS-Handler liefern bei Einzelobjekt direkt das Dict, andere in "items"
            if isinstance(data, dict) and "items" in data and data["items"]:
                return data["items"][0]
            if isinstance(data, dict):
                return data
            raise HTTPException(status_code=404, detail="Country nicht gefunden")
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ORDS nicht erreichbar: {e}",
            ) from e

    # ---------- (Optional) CREATE/UPDATE/DELETE ----------
    def create_country(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self._full("wf_countries/")
        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            return self._handle(resp)
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}") from e

    def update_country(self, country_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self._full(f"wf_countries/{country_id}")
        try:
            resp = self.session.put(url, json=payload, timeout=self.timeout)
            return self._handle(resp)
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}") from e

    def delete_country(self, country_id: str) -> Dict[str, Any]:
        url = self._full(f"wf_countries/{country_id}")
        try:
            resp = self.session.delete(url, timeout=self.timeout)
            return self._handle(resp)
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"ORDS nicht erreichbar: {e}") from e


def build_ords_service() -> OrdsService:
    """
    Baut den Service aus ENV-Variablen.
    Fallbacks sind so gewählt, dass dein Setup sofort läuft.
    """
    base = os.getenv("ORDS_BASE", "http://localhost:8181/ords/lf12")
    api_key = os.getenv("ORDS_API_KEY")  # falls du Header-Auth nutzt
    timeout = float(os.getenv("ORDS_TIMEOUT", "5"))
    return OrdsService(base_url=base, api_key=api_key, timeout=timeout)
