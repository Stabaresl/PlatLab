import base64
import hashlib
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings

from modules.authentication.application.dtos import OAuthProfileDTO
from modules.shared.domain.exceptions import UnauthenticatedError

_REQUEST_TIMEOUT_SECONDS = 10


def generar_par_pkce() -> tuple[str, str]:
    """
    Genera el `code_verifier` y su `code_challenge` (S256) para el flujo
    Authorization Code + PKCE (seguridad.md §3). El verifier se guarda
    server-side (`OAuthStateStore`) y nunca viaja al proveedor hasta el
    intercambio del `code`.
    """
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


class GoogleOAuthAdapter:
    """
    Adapter sobre la API OAuth2 de Google (estructura-carpetas.md). Traduce
    la respuesta real de Google a `OAuthProfileDTO` — el resto del sistema
    nunca sabe que existe un proveedor "Google" ni conoce su forma de API.
    """

    _AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    _TOKEN_URL = "https://oauth2.googleapis.com/token"
    _USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def build_authorize_url(self, state: str, code_challenge: str) -> str:
        params = {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "online",
        }
        return f"{self._AUTHORIZE_URL}?{urlencode(params)}"

    def fetch_profile(self, code: str, code_verifier: str) -> OAuthProfileDTO:
        token_response = requests.post(
            self._TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            },
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        if not token_response.ok:
            raise UnauthenticatedError("No se pudo validar la autenticación con Google.")
        access_token = token_response.json().get("access_token")

        userinfo_response = requests.get(
            self._USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        if not userinfo_response.ok:
            raise UnauthenticatedError("No se pudo obtener el perfil de Google.")
        data = userinfo_response.json()

        return OAuthProfileDTO(
            proveedor="google",
            proveedor_uid=data["sub"],
            email=data["email"],
            nombre_completo=data.get("name") or data["email"],
            email_verificado=bool(data.get("email_verified", False)),
        )


class GitHubOAuthAdapter:
    """
    Adapter sobre la API OAuth de GitHub. GitHub no expone `email` en
    `/user` si el usuario lo marcó privado — se recurre a `/user/emails`
    para obtener el correo primario verificado.
    """

    _AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    _TOKEN_URL = "https://github.com/login/oauth/access_token"
    _USER_URL = "https://api.github.com/user"
    _EMAILS_URL = "https://api.github.com/user/emails"

    def build_authorize_url(self, state: str, code_challenge: str) -> str:
        params = {
            "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
            "scope": "read:user user:email",
            "state": state,
            # Las OAuth Apps clásicas de GitHub no exigen PKCE, pero se
            # envía igual por defensa en profundidad (seguridad.md §3) — un
            # parámetro desconocido no rompe el flujo del lado de GitHub.
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{self._AUTHORIZE_URL}?{urlencode(params)}"

    def fetch_profile(self, code: str, code_verifier: str) -> OAuthProfileDTO:
        token_response = requests.post(
            self._TOKEN_URL,
            data={
                "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
                "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
                "code_verifier": code_verifier,
            },
            headers={"Accept": "application/json"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        token_data = token_response.json() if token_response.ok else {}
        access_token = token_data.get("access_token")
        if not access_token:
            raise UnauthenticatedError("No se pudo validar la autenticación con GitHub.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        user_response = requests.get(
            self._USER_URL, headers=headers, timeout=_REQUEST_TIMEOUT_SECONDS
        )
        if not user_response.ok:
            raise UnauthenticatedError("No se pudo obtener el perfil de GitHub.")
        user_data = user_response.json()

        email = user_data.get("email")
        if not email:
            emails_response = requests.get(
                self._EMAILS_URL, headers=headers, timeout=_REQUEST_TIMEOUT_SECONDS
            )
            emails = emails_response.json() if emails_response.ok else []
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            email = primary["email"] if primary else None

        if not email:
            raise UnauthenticatedError(
                "Tu cuenta de GitHub no tiene un correo verificado disponible."
            )

        return OAuthProfileDTO(
            proveedor="github",
            proveedor_uid=str(user_data["id"]),
            email=email,
            nombre_completo=user_data.get("name") or user_data.get("login"),
            email_verificado=True,
        )
