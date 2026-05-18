import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from ords_service import OrdsService


@pytest.fixture
def svc():
    return OrdsService(base_url="http://ords-test/ords/projekt_lf12")


def mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = status_code < 400
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ------------------------------------------------------------------ FIRMEN

def test_list_firmen_returns_items(svc):
    svc.session.get = MagicMock(return_value=mock_response(
        {"items": [{"firma_id": 1, "firma_name": "TestFirma GmbH"}]}
    ))
    result = svc.list_firmen()
    assert len(result) == 1
    assert result[0]["firma_name"] == "TestFirma GmbH"
    svc.session.get.assert_called_once_with(
        "http://ords-test/ords/projekt_lf12/firma/", params=None, timeout=10.0
    )


def test_list_firmen_leere_liste(svc):
    svc.session.get = MagicMock(return_value=mock_response({"items": []}))
    assert svc.list_firmen() == []


def test_get_firma(svc):
    svc.session.get = MagicMock(return_value=mock_response({"firma_id": 5, "firma_name": "Muster AG"}))
    result = svc.get_firma(5)
    assert result["firma_id"] == 5


def test_create_firma_komplett_sendet_post(svc):
    payload = {"firma_name": "Neu GmbH", "ap_vorname": "Max"}
    svc.session.post = MagicMock(return_value=mock_response({"firma_id": 42}))
    result = svc.create_firma_komplett(payload)
    assert result["firma_id"] == 42
    svc.session.post.assert_called_once()
    url = svc.session.post.call_args[0][0]
    assert "api/v1/firmen/komplett/" in url


def test_delete_firma(svc):
    svc.session.delete = MagicMock(return_value=mock_response(None, 204))
    svc.session.delete.return_value.status_code = 204
    svc.session.delete.return_value.raise_for_status = MagicMock()
    svc.session.delete.return_value.json.side_effect = ValueError
    svc.session.delete.return_value.text = ""
    svc.delete_firma(1)
    svc.session.delete.assert_called_once()


# ------------------------------------------------------------------ KURSE

def test_list_kurse(svc):
    svc.session.get = MagicMock(return_value=mock_response(
        {"items": [{"kurs_id": 1, "kurs_name": "Python Grundlagen"}]}
    ))
    result = svc.list_kurse()
    assert result[0]["kurs_name"] == "Python Grundlagen"


def test_create_kurs_komplett(svc):
    payload = {"kurs_name": "Excel", "kurs_typ": "Webinar", "termine": []}
    svc.session.post = MagicMock(return_value=mock_response({"kurs_id": 7}))
    result = svc.create_kurs_komplett(payload)
    assert result["kurs_id"] == 7
    url = svc.session.post.call_args[0][0]
    assert "api/v1/kurse/komplett/" in url


def test_get_kurs_detail(svc):
    svc.session.get = MagicMock(return_value=mock_response(
        {"kurs_id": 3, "kurs_name": "SQL", "termine": []}
    ))
    result = svc.get_kurs_detail(3)
    assert result["kurs_id"] == 3
    url = svc.session.get.call_args[0][0]
    assert "api/v1/kurse/3/detail" in url


# ------------------------------------------------------------------ ANGEBOTE

def test_update_angebot_status_angenommen(svc):
    svc.session.put = MagicMock(return_value=mock_response(
        {"success": True, "rechnungsnummer": 10}
    ))
    result = svc.update_angebot_status(1, "angenommen", zahltermin_tage=30)
    assert result["rechnungsnummer"] == 10
    url = svc.session.put.call_args[0][0]
    assert "api/v1/angebote/1/status" in url


def test_update_angebot_status_abgelehnt(svc):
    svc.session.put = MagicMock(return_value=mock_response({"success": True}))
    result = svc.update_angebot_status(2, "abgelehnt")
    assert result["success"] is True


# ------------------------------------------------------------------ RECHNUNGEN

def test_zahlung_erfassen(svc):
    svc.session.post = MagicMock(return_value=mock_response({"zahlung_id": 99}))
    result = svc.zahlung_erfassen(5, 1500.0, "Überweisung")
    assert result["zahlung_id"] == 99
    url = svc.session.post.call_args[0][0]
    assert "api/v1/rechnungen/5/zahlung/" in url


# ------------------------------------------------------------------ TEILNEHMER

def test_update_teilnehmer_status(svc):
    svc.session.put = MagicMock(return_value=mock_response({"success": True}))
    result = svc.update_teilnehmer_status(3, status_id=3)
    assert result["success"] is True
    url = svc.session.put.call_args[0][0]
    assert "api/v1/teilnehmer/3/status" in url


# ------------------------------------------------------------------ FEHLERBEHANDLUNG

def test_http_fehler_wirft_http_exception(svc):
    import requests as req
    error_resp = MagicMock()
    error_resp.status_code = 404
    error_resp.reason = "Not Found"
    error_resp.text = "not found"
    error_resp.raise_for_status.side_effect = req.HTTPError(response=error_resp)
    svc.session.get = MagicMock(return_value=error_resp)
    with pytest.raises(HTTPException) as exc:
        svc.get_firma(999)
    assert exc.value.status_code == 404


def test_verbindungsfehler_wirft_502(svc):
    import requests as req
    svc.session.get = MagicMock(side_effect=req.ConnectionError("refused"))
    with pytest.raises(HTTPException) as exc:
        svc.list_firmen()
    assert exc.value.status_code == 502
