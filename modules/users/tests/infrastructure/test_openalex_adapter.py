import pytest
import requests

from modules.users.infrastructure import openalex_adapter
from modules.users.infrastructure.openalex_adapter import OpenAlexAdapter


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_verificar_orcid_no_encontrado_retorna_no_encontrado_sin_excepcion(monkeypatch):
    monkeypatch.setattr(
        openalex_adapter.requests, "get", lambda url, params, timeout: _FakeResponse(404)
    )

    resultado = OpenAlexAdapter().verificar(orcid="0000-0000-0000-0000", nombre_declarado="Alguien")

    assert resultado.encontrado is False
    assert resultado.coincide_nombre is False
    assert resultado.works_count == 0


def test_verificar_nombre_coincide_ignorando_tildes_y_orden(monkeypatch):
    monkeypatch.setattr(
        openalex_adapter.requests,
        "get",
        lambda url, params, timeout: _FakeResponse(
            200, {"display_name": "María Tabarés Santiago", "works_count": 3}
        ),
    )

    resultado = OpenAlexAdapter().verificar(
        orcid="0000-0000-0000-0000", nombre_declarado="Santiago Tabares Maria"
    )

    assert resultado.encontrado is True
    assert resultado.coincide_nombre is True
    assert resultado.works_count == 3


def test_verificar_nombre_distinto_no_coincide(monkeypatch):
    monkeypatch.setattr(
        openalex_adapter.requests,
        "get",
        lambda url, params, timeout: _FakeResponse(
            200, {"display_name": "Otra Persona Distinta", "works_count": 5}
        ),
    )

    resultado = OpenAlexAdapter().verificar(orcid="0000-0000-0000-0000", nombre_declarado="Juan Perez")

    assert resultado.encontrado is True
    assert resultado.coincide_nombre is False


def test_verificar_error_de_red_se_propaga_para_que_celery_reintente(monkeypatch):
    def fake_get(url, params, timeout):
        raise requests.ConnectionError("sin conexión")

    monkeypatch.setattr(openalex_adapter.requests, "get", fake_get)

    with pytest.raises(requests.ConnectionError):
        OpenAlexAdapter().verificar(orcid="0000-0000-0000-0000", nombre_declarado="Alguien")


def test_verificar_error_5xx_se_propaga(monkeypatch):
    monkeypatch.setattr(
        openalex_adapter.requests, "get", lambda url, params, timeout: _FakeResponse(500)
    )

    with pytest.raises(requests.HTTPError):
        OpenAlexAdapter().verificar(orcid="0000-0000-0000-0000", nombre_declarado="Alguien")
