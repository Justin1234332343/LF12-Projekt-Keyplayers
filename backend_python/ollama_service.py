import os
from typing import Any, Dict, Generator, List, Optional
import requests
from fastapi import HTTPException


class OllamaService:
    """Kapselt alle Calls zur Ollama REST-API."""

    def __init__(self, base_url: str, model: str = "mistral", timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def is_available(self) -> bool:
        try:
            r = self.session.get(self._url("/api/tags"), timeout=3)
            return r.ok
        except requests.RequestException:
            return False

    def list_models(self) -> List[str]:
        try:
            r = self.session.get(self._url("/api/tags"), timeout=5)
            r.raise_for_status()
            return [m.get("name") for m in r.json().get("models", [])]
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Ollama nicht erreichbar: {e}") from e

    def _check_model_ready(self, r: requests.Response) -> None:
        if r.status_code == 404:
            raise HTTPException(
                status_code=503,
                detail=f"Modell '{self.model}' wird noch geladen. Bitte kurz warten und erneut versuchen.",
            )
        r.raise_for_status()

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            r = self.session.post(self._url("/api/generate"), json=payload, timeout=self.timeout)
            self._check_model_ready(r)
            return r.json().get("response", "").strip()
        except HTTPException:
            raise
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Ollama Fehler: {e}") from e

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            r = self.session.post(self._url("/api/chat"), json=payload, timeout=self.timeout)
            self._check_model_ready(r)
            data = r.json()
            return (data.get("message") or {}).get("content", "").strip()
        except HTTPException:
            raise
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Ollama Fehler: {e}") from e

    # ---------------------------------------------------------------- Prompts

    def generate_angebot_text(
        self,
        firma_name: str,
        kurs_name: str,
        kurs_typ: str,
        kurs_datum_beginn: str,
        kurs_datum_ende: str,
        betrag: float,
    ) -> str:
        prompt = f"""Schreibe einen professionellen deutschen Angebotstext für folgendes Seminar-Angebot.
Der Text soll höflich, präzise und geschäftsmäßig sein (ca. 3-4 Sätze).

Empfänger: {firma_name}
Seminar: {kurs_name}
Format: {kurs_typ}
Zeitraum: {kurs_datum_beginn} bis {kurs_datum_ende}
Betrag: {betrag:.2f} EUR (netto)

Schreibe nur den Angebotstext, keine Betreffzeile oder Anrede."""
        return self.generate(prompt)

    def generate_benachrichtigung(
        self,
        empfaenger_name: str,
        betreff_typ: str,
        kontext: Dict[str, Any],
    ) -> str:
        kontext_str = "\n".join(f"- {k}: {v}" for k, v in kontext.items())
        prompt = f"""Schreibe eine professionelle deutsche E-Mail für folgenden Anlass.
Nur den E-Mail-Text (ohne Betreff), höflich und prägnant.

Empfänger: {empfaenger_name}
Anlass: {betreff_typ}
Kontext:
{kontext_str}"""
        return self.generate(prompt)

    def generate_kurs_beschreibung(
        self,
        kurs_name: str,
        kurs_typ: str,
        kurs_tage: int,
        themen_stichworte: Optional[str] = None,
    ) -> str:
        themen = f"\nThemen/Stichworte: {themen_stichworte}" if themen_stichworte else ""
        prompt = f"""Schreibe eine ansprechende deutsche Kursbeschreibung für einen Seminar-Katalog.
Ca. 4-6 Sätze, professionell und motivierend.

Kursname: {kurs_name}
Format: {kurs_typ}
Dauer: {kurs_tage} Tag(e){themen}

Schreibe nur die Kursbeschreibung."""
        return self.generate(prompt)

    def generate_mahnung(
        self,
        firma_name: str,
        rechnungsnummer: int,
        betrag: float,
        zahltermin: str,
        mahnstufe: int = 1,
    ) -> str:
        stufen = {1: "erste freundliche Zahlungserinnerung", 2: "zweite Mahnung", 3: "letzte Mahnung vor rechtlichen Schritten"}
        stufe_text = stufen.get(mahnstufe, "Zahlungserinnerung")
        prompt = f"""Schreibe eine professionelle deutsche {stufe_text}.
Nur den E-Mail-Text (ohne Betreff), sachlich und klar.

Empfänger: {firma_name}
Rechnungsnummer: {rechnungsnummer}
Offener Betrag: {betrag:.2f} EUR
Ursprünglicher Zahltermin: {zahltermin}"""
        return self.generate(prompt)


def build_ollama_service() -> OllamaService:
    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "mistral")
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "120"))
    return OllamaService(base_url=base, model=model, timeout=timeout)
