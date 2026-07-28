import pytest

from modules.authentication.infrastructure import oauth_adapters
from modules.authentication.infrastructure.oauth_adapters import (
    GitHubOAuthAdapter,
    GoogleOAuthAdapter,
    generar_par_pkce,
)
from modules.shared.domain.exceptions import UnauthenticatedError


class _FakeResponse:
    def __init__(self, json_data, ok=True):
        self._json = json_data
        self.ok = ok

    def json(self):
        return self._json


def test_generar_par_pkce_produce_verifier_y_challenge_distintos():
    verifier, challenge = generar_par_pkce()
    assert verifier != challenge
    assert len(verifier) >= 43


def test_google_build_authorize_url_incluye_pkce_y_state():
    url = GoogleOAuthAdapter().build_authorize_url(state="abc", code_challenge="xyz")
    assert "state=abc" in url
    assert "code_challenge=xyz" in url
    assert "code_challenge_method=S256" in url


def test_google_fetch_profile_retorna_perfil_normalizado(monkeypatch):
    def fake_post(url, data, timeout):
        return _FakeResponse({"access_token": "tok-123"})

    def fake_get(url, headers, timeout):
        return _FakeResponse(
            {"sub": "google-uid-1", "email": "test@uni.edu", "name": "Test", "email_verified": True}
        )

    monkeypatch.setattr(oauth_adapters.requests, "post", fake_post)
    monkeypatch.setattr(oauth_adapters.requests, "get", fake_get)

    profile = GoogleOAuthAdapter().fetch_profile(code="code-x", code_verifier="verifier-x")

    assert profile.proveedor == "google"
    assert profile.proveedor_uid == "google-uid-1"
    assert profile.email == "test@uni.edu"
    assert profile.email_verificado is True


def test_google_fetch_profile_token_exchange_fallido_lanza_unauthenticated(monkeypatch):
    monkeypatch.setattr(
        oauth_adapters.requests, "post", lambda url, data, timeout: _FakeResponse({}, ok=False)
    )

    with pytest.raises(UnauthenticatedError):
        GoogleOAuthAdapter().fetch_profile(code="code-x", code_verifier="verifier-x")


def test_github_fetch_profile_usa_user_emails_si_email_es_privado(monkeypatch):
    def fake_post(url, data, headers, timeout):
        return _FakeResponse({"access_token": "tok-gh"})

    def fake_get(url, headers, timeout):
        if url.endswith("/user"):
            return _FakeResponse({"id": 42, "login": "octocat", "email": None, "name": "Octo Cat"})
        return _FakeResponse([{"email": "octo@uni.edu", "primary": True, "verified": True}])

    monkeypatch.setattr(oauth_adapters.requests, "post", fake_post)
    monkeypatch.setattr(oauth_adapters.requests, "get", fake_get)

    profile = GitHubOAuthAdapter().fetch_profile(code="code-x", code_verifier="verifier-x")

    assert profile.proveedor == "github"
    assert profile.proveedor_uid == "42"
    assert profile.email == "octo@uni.edu"
    assert profile.email_verificado is True


def test_github_fetch_profile_sin_email_verificado_lanza_unauthenticated(monkeypatch):
    def fake_post(url, data, headers, timeout):
        return _FakeResponse({"access_token": "tok-gh"})

    def fake_get(url, headers, timeout):
        if url.endswith("/user"):
            return _FakeResponse({"id": 42, "login": "octocat", "email": None, "name": "Octo Cat"})
        return _FakeResponse([])

    monkeypatch.setattr(oauth_adapters.requests, "post", fake_post)
    monkeypatch.setattr(oauth_adapters.requests, "get", fake_get)

    with pytest.raises(UnauthenticatedError):
        GitHubOAuthAdapter().fetch_profile(code="code-x", code_verifier="verifier-x")
