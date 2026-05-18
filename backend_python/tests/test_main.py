import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    import main
    mock_ords = MagicMock()
    mock_ollama = MagicMock()
    with patch.object(main, "ords", mock_ords), patch.object(main, "ollama", mock_ollama):
        yield TestClient(main.app), mock_ords, mock_ollama


# ------------------------------------------------------------------ HEALTH

def test_health(client):
    tc, _, _ = client
    resp = tc.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ------------------------------------------------------------------ FIRMEN

def test_list_firmen(client):
    tc, ords, _ = client
    ords.list_firmen.return_value = [{"firma_id": 1, "firma_name": "Test GmbH"}]
    resp = tc.get("/firmen/")
    assert resp.status_code == 200
    assert resp.json()[0]["firma_name"] == "Test GmbH"


def test_get_firma(client):
    tc, ords, _ = client
    ords.get_firma.return_value = {"firma_id": 1, "firma_name": "Test GmbH"}
    resp = tc.get("/firmen/1")
    assert resp.status_code == 200
    ords.get_firma.assert_called_once_with(1)


def test_create_firma_komplett(client):
    tc, ords, _ = client
    ords.create_firma_komplett.return_value = {"firma_id": 42}
    payload = {
        "firma_name": "Neu GmbH", "rechnungsadresse": "Musterstr. 1",
        "email_rechnungsversand": "rechnung@neu.de",
        "ap_vorname": "Max", "ap_nachname": "Muster", "ap_email": "max@neu.de"
    }
    resp = tc.post("/firmen/komplett/", json=payload)
    assert resp.status_code == 201
    assert resp.json()["firma_id"] == 42


def test_create_firma_validierung_fehlt_pflichtfeld(client):
    tc, _, _ = client
    resp = tc.post("/firmen/komplett/", json={"firma_name": "Unvollständig"})
    assert resp.status_code == 422


def test_delete_firma(client):
    tc, ords, _ = client
    ords.delete_firma.return_value = None
    resp = tc.delete("/firmen/1")
    assert resp.status_code == 204


# ------------------------------------------------------------------ KURSE

def test_list_kurse(client):
    tc, ords, _ = client
    ords.list_kurse.return_value = [{"kurs_id": 1, "kurs_name": "Python"}]
    resp = tc.get("/kurse/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_kurs_detail(client):
    tc, ords, _ = client
    ords.get_kurs_detail.return_value = {"kurs_id": 3, "kurs_name": "SQL", "termine": []}
    resp = tc.get("/kurse/3/detail")
    assert resp.status_code == 200
    ords.get_kurs_detail.assert_called_once_with(3)


def test_create_kurs_komplett(client):
    tc, ords, _ = client
    ords.create_kurs_komplett.return_value = {"kurs_id": 7}
    payload = {
        "kurs_name": "Excel", "kurs_typ": "Webinar",
        "kurs_datum_beginn": "2026-06-01", "kurs_datum_ende": "2026-06-02",
        "kurs_zeitraum": "09:00-17:00", "kurs_tage": 2,
        "termine": [{"datum": "2026-06-01", "start": "2026-06-01 09:00:00", "ende": "2026-06-01 17:00:00"}]
    }
    resp = tc.post("/kurse/komplett/", json=payload)
    assert resp.status_code == 201


# ------------------------------------------------------------------ TEILNEHMER

def test_list_teilnehmer(client):
    tc, ords, _ = client
    ords.list_teilnehmer.return_value = [{"teilnehmerid": 1, "vorname": "Anna", "nachname": "Schmidt"}]
    resp = tc.get("/teilnehmer/")
    assert resp.status_code == 200


def test_create_teilnehmer(client):
    tc, ords, _ = client
    ords.create_teilnehmer.return_value = {"teilnehmerid": 5}
    resp = tc.post("/teilnehmer/", json={"firma_id": 1, "vorname": "Tom", "nachname": "Müller", "email": "tom@test.de"})
    assert resp.status_code == 201


def test_update_teilnehmer_status(client):
    tc, ords, _ = client
    ords.update_teilnehmer_status.return_value = {"success": True}
    resp = tc.put("/teilnehmer/1/status", json={"status_id": 3})
    assert resp.status_code == 200
    ords.update_teilnehmer_status.assert_called_once_with(1, 3)


# ------------------------------------------------------------------ ANGEBOTE

def test_update_angebot_status_angenommen(client):
    tc, ords, _ = client
    ords.update_angebot_status.return_value = {"success": True, "rechnungsnummer": 10}
    resp = tc.put("/angebote/1/status", json={"status": "angenommen"})
    assert resp.status_code == 200
    ords.update_angebot_status.assert_called_once_with(1, "angenommen", 30)


def test_create_angebot(client):
    tc, ords, _ = client
    ords.create_angebot.return_value = {"angebot_id": 3}
    resp = tc.post("/angebote/", json={"firma_id": 1, "kurs_id": 2, "angebot_betrag": 1500.0})
    assert resp.status_code == 201


# ------------------------------------------------------------------ RECHNUNGEN

def test_zahlung_erfassen(client):
    tc, ords, _ = client
    ords.zahlung_erfassen.return_value = {"zahlung_id": 99}
    resp = tc.post("/rechnungen/5/zahlung/", json={"betrag": 1500.0, "zahlungsmethode": "Überweisung"})
    assert resp.status_code == 201
    ords.zahlung_erfassen.assert_called_once_with(5, 1500.0, "Überweisung")


# ------------------------------------------------------------------ OLLAMA

def test_ollama_health(client):
    tc, _, ollama = client
    ollama.is_available.return_value = True
    ollama.model = "mistral"
    resp = tc.get("/ollama/health")
    assert resp.status_code == 200
    assert resp.json()["available"] is True


def test_ollama_kurs_beschreibung(client):
    tc, _, ollama = client
    ollama.generate_kurs_beschreibung.return_value = "Ein toller Kurs über Python..."
    resp = tc.post("/ollama/kurs-beschreibung", json={"kurs_name": "Python", "kurs_typ": "Webinar", "kurs_tage": 2})
    assert resp.status_code == 200
    assert "text" in resp.json()


def test_ollama_angebot_text(client):
    tc, _, ollama = client
    ollama.generate_angebot_text.return_value = "Sehr geehrte Damen und Herren..."
    resp = tc.post("/ollama/angebot-text", json={
        "firma_name": "Test GmbH", "kurs_name": "Python", "kurs_typ": "Webinar",
        "kurs_datum_beginn": "2026-06-01", "kurs_datum_ende": "2026-06-02", "betrag": 1500.0
    })
    assert resp.status_code == 200
    assert resp.json()["text"] == "Sehr geehrte Damen und Herren..."
