import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from ollama_service import OllamaService


@pytest.fixture
def svc():
    return OllamaService(base_url="http://ollama-test:11434", model="mistral")


def mock_response(json_data, status_code=200, ok=True):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = ok
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ------------------------------------------------------------------ VERFÜGBARKEIT

def test_is_available_true(svc):
    svc.session.get = MagicMock(return_value=mock_response({"models": []}))
    assert svc.is_available() is True


def test_is_available_false_bei_fehler(svc):
    import requests as req
    svc.session.get = MagicMock(side_effect=req.ConnectionError())
    assert svc.is_available() is False


def test_is_available_false_bei_nicht_ok(svc):
    svc.session.get = MagicMock(return_value=mock_response({}, ok=False))
    assert svc.is_available() is False


# ------------------------------------------------------------------ MODELLE

def test_list_models(svc):
    svc.session.get = MagicMock(return_value=mock_response(
        {"models": [{"name": "mistral:latest"}, {"name": "llama2:latest"}]}
    ))
    result = svc.list_models()
    assert "mistral:latest" in result
    assert len(result) == 2


def test_list_models_leer(svc):
    svc.session.get = MagicMock(return_value=mock_response({"models": []}))
    assert svc.list_models() == []


def test_list_models_verbindungsfehler(svc):
    import requests as req
    svc.session.get = MagicMock(side_effect=req.ConnectionError())
    with pytest.raises(HTTPException) as exc:
        svc.list_models()
    assert exc.value.status_code == 502


# ------------------------------------------------------------------ GENERATE

def test_generate_gibt_text_zurueck(svc):
    svc.session.post = MagicMock(return_value=mock_response(
        {"response": "  Docker Compose wird genutzt um mehrere Container zu starten.  "}
    ))
    result = svc.generate("Was ist Docker Compose?")
    assert "Docker" in result
    assert result == result.strip()


def test_generate_nutzt_konfigurierten_model(svc):
    svc.session.post = MagicMock(return_value=mock_response({"response": "ok"}))
    svc.generate("test")
    body = svc.session.post.call_args[1]["json"]
    assert body["model"] == "mistral"


def test_generate_model_override(svc):
    svc.session.post = MagicMock(return_value=mock_response({"response": "ok"}))
    svc.generate("test", model="llama2")
    body = svc.session.post.call_args[1]["json"]
    assert body["model"] == "llama2"


def test_generate_stream_ist_false(svc):
    svc.session.post = MagicMock(return_value=mock_response({"response": "ok"}))
    svc.generate("test")
    body = svc.session.post.call_args[1]["json"]
    assert body["stream"] is False


# ------------------------------------------------------------------ CHAT

def test_chat_gibt_content_zurueck(svc):
    svc.session.post = MagicMock(return_value=mock_response(
        {"message": {"content": "Hallo! Wie kann ich helfen?"}}
    ))
    result = svc.chat([{"role": "user", "content": "Hallo"}])
    assert "Hallo" in result


def test_chat_sendet_messages(svc):
    svc.session.post = MagicMock(return_value=mock_response({"message": {"content": "ok"}}))
    messages = [{"role": "user", "content": "Test"}]
    svc.chat(messages)
    body = svc.session.post.call_args[1]["json"]
    assert body["messages"] == messages


# ------------------------------------------------------------------ BUSINESS PROMPTS

def test_generate_angebot_text_enthaelt_firmenname(svc):
    svc.session.post = MagicMock(return_value=mock_response({"response": "Sehr geehrte Damen und Herren der Muster GmbH"}))
    result = svc.generate_angebot_text(
        firma_name="Muster GmbH", kurs_name="Python", kurs_typ="Webinar",
        kurs_datum_beginn="2026-06-01", kurs_datum_ende="2026-06-02", betrag=1500.0
    )
    assert isinstance(result, str)
    prompt = svc.session.post.call_args[1]["json"]["prompt"]
    assert "Muster GmbH" in prompt
    assert "1500.00 EUR" in prompt


def test_generate_kurs_beschreibung_enthaelt_kursname(svc):
    svc.session.post = MagicMock(return_value=mock_response({"response": "Ein spannender Kurs..."}))
    svc.generate_kurs_beschreibung(kurs_name="Excel Profi", kurs_typ="Präsenz", kurs_tage=2)
    prompt = svc.session.post.call_args[1]["json"]["prompt"]
    assert "Excel Profi" in prompt


def test_generate_mahnung_stufe_1(svc):
    svc.session.post = MagicMock(return_value=mock_response({"response": "Freundliche Erinnerung..."}))
    svc.generate_mahnung("ABC GmbH", rechnungsnummer=7, betrag=800.0, zahltermin="2026-05-01", mahnstufe=1)
    prompt = svc.session.post.call_args[1]["json"]["prompt"]
    assert "ABC GmbH" in prompt
    assert "800.00 EUR" in prompt
