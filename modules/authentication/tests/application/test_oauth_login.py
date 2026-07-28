import uuid

import pytest
from django.contrib.auth.hashers import make_password

from modules.authentication.application.dtos import OAuthCallbackDTO, OAuthProfileDTO
from modules.authentication.application.use_cases.oauth_login import OAuthLoginUseCase
from modules.authentication.domain.events import UserLoggedIn, UserRegistered
from modules.authentication.domain.exceptions import AccountLinkingRequiresConfirmationError
from modules.authentication.domain.services import VinculadorDeCuenta
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.oauth_link_store import OAuthLinkStore
from modules.authentication.infrastructure.oauth_state_store import OAuthStateStore
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.domain.exceptions import ForbiddenError, UnauthenticatedError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import ProveedorAutenticacion, ProveedorTipo, User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


class _FakeAdapter:
    """Reemplaza al adapter real (sin llamadas HTTP) para aislar la lógica del use case."""

    def __init__(self, profile: OAuthProfileDTO):
        self._profile = profile

    def fetch_profile(self, code: str, code_verifier: str) -> OAuthProfileDTO:
        return self._profile


def _profile(email, uid, proveedor="google", verificado=True):
    return OAuthProfileDTO(
        proveedor=proveedor,
        proveedor_uid=uid,
        email=email,
        nombre_completo="OAuth Test",
        email_verificado=verificado,
    )


def _build_use_case(profile, dispatcher=None):
    state_store = OAuthStateStore()
    state = f"state-{uuid.uuid4()}"
    state_store.save(state=state, code_verifier="verifier-x", proveedor=profile.proveedor)

    use_case = OAuthLoginUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=dispatcher or EventDispatcher(),
        user_repository=UserRepository(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
        oauth_state_store=state_store,
        oauth_link_store=OAuthLinkStore(),
        oauth_adapter=_FakeAdapter(profile),
        vinculador_de_cuenta=VinculadorDeCuenta(),
    )
    return use_case, state


@pytest.mark.django_db
def test_oauth_login_usuario_nuevo_crea_cuenta_y_retorna_tokens():
    profile = _profile(email="oauth_nuevo1@uni.edu", uid="google-uid-nuevo1")
    use_case, state = _build_use_case(profile)

    result = use_case.execute(OAuthCallbackDTO(proveedor="google", code="code-x", state=state))

    assert result.tokens.access
    assert result.tokens.rol == "estudiante"

    repo = UserRepository()
    user = repo.get_by_email("oauth_nuevo1@uni.edu")
    assert user is not None
    assert user.password_hash is None

    proveedores = repo.get_proveedores_by_user_id(user.id)
    assert len(proveedores) == 1
    assert proveedores[0].proveedor == ProveedorTipo.GOOGLE
    assert proveedores[0].proveedor_uid == "google-uid-nuevo1"


@pytest.mark.django_db
def test_oauth_login_usuario_ya_vinculado_hace_login_directo_sin_duplicar():
    profile = _profile(email="oauth_vinculado@uni.edu", uid="google-uid-vinculado")
    repo = UserRepository()
    user = repo.add(User(email=Email("oauth_vinculado@uni.edu"), nombre_completo="Ya Vinculado"))
    repo.add_proveedor(
        ProveedorAutenticacion(
            user_id=user.id, proveedor=ProveedorTipo.GOOGLE, proveedor_uid="google-uid-vinculado"
        )
    )

    use_case, state = _build_use_case(profile)
    result = use_case.execute(OAuthCallbackDTO(proveedor="google", code="code-x", state=state))

    assert result.tokens.access
    assert len(repo.get_proveedores_by_user_id(user.id)) == 1


@pytest.mark.django_db
def test_oauth_login_colision_de_email_requiere_confirmacion():
    UserRepository().add(
        User(
            email=Email("oauth_colision@uni.edu"),
            nombre_completo="Password Owner",
            password_hash=make_password("Segura123"),
        )
    )
    profile = _profile(email="oauth_colision@uni.edu", uid="google-uid-colision")
    use_case, state = _build_use_case(profile)

    with pytest.raises(AccountLinkingRequiresConfirmationError) as exc_info:
        use_case.execute(OAuthCallbackDTO(proveedor="google", code="code-x", state=state))

    assert exc_info.value.details[0]["link_token"]


@pytest.mark.django_db
def test_oauth_login_email_no_verificado_lanza_unauthenticated():
    profile = _profile(email="oauth_noverif@uni.edu", uid="google-uid-noverif", verificado=False)
    use_case, state = _build_use_case(profile)

    with pytest.raises(UnauthenticatedError):
        use_case.execute(OAuthCallbackDTO(proveedor="google", code="code-x", state=state))


@pytest.mark.django_db
def test_oauth_login_state_invalido_lanza_unauthenticated():
    profile = _profile(email="oauth_state@uni.edu", uid="google-uid-state")
    _build_use_case(profile)  # emite y descarta un state válido, no lo usamos
    use_case, _ = _build_use_case(profile)

    with pytest.raises(UnauthenticatedError):
        use_case.execute(
            OAuthCallbackDTO(proveedor="google", code="code-x", state="state-que-nunca-existio")
        )


@pytest.mark.django_db
def test_oauth_login_usuario_inactivo_lanza_forbidden():
    repo = UserRepository()
    user = repo.add(
        User(email=Email("oauth_inactivo@uni.edu"), nombre_completo="Inactivo", is_active=False)
    )
    repo.add_proveedor(
        ProveedorAutenticacion(
            user_id=user.id, proveedor=ProveedorTipo.GOOGLE, proveedor_uid="google-uid-inactivo"
        )
    )
    profile = _profile(email="oauth_inactivo@uni.edu", uid="google-uid-inactivo")
    use_case, state = _build_use_case(profile)

    with pytest.raises(ForbiddenError):
        use_case.execute(OAuthCallbackDTO(proveedor="google", code="code-x", state=state))


@pytest.mark.django_db
def test_oauth_login_dispara_user_registered_solo_en_alta_nueva():
    profile = _profile(email="oauth_evento@uni.edu", uid="google-uid-evento")
    dispatcher = EventDispatcher()
    registrados = []
    logins = []
    dispatcher.subscribe(UserRegistered, lambda e: registrados.append(e))
    dispatcher.subscribe(UserLoggedIn, lambda e: logins.append(e))

    use_case, state = _build_use_case(profile, dispatcher)
    use_case.execute(OAuthCallbackDTO(proveedor="google", code="code-x", state=state))

    assert len(registrados) == 1
    assert len(logins) == 1
