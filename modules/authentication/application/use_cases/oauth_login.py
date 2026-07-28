from datetime import datetime, timezone

from modules.authentication.application.dtos import (
    OAuthCallbackDTO,
    OAuthLoginResultDTO,
    OAuthProfileDTO,
)
from modules.authentication.domain.events import UserLoggedIn, UserRegistered
from modules.authentication.domain.exceptions import AccountLinkingRequiresConfirmationError
from modules.authentication.domain.services import VinculadorDeCuenta
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.oauth_link_store import OAuthLinkStore
from modules.authentication.infrastructure.oauth_state_store import OAuthStateStore
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, UnauthenticatedError
from modules.users.domain.entities import ProveedorAutenticacion, ProveedorTipo, User
from modules.users.domain.repositories import IUserRepository
from modules.users.domain.value_objects import Email, Rol

_ESTADO_INVALIDO_MSG = "El estado de la autenticación OAuth es inválido o expiró."


class OAuthLoginUseCase(BaseUseCase[OAuthCallbackDTO, OAuthLoginResultDTO]):
    """
    UC-01 A1/A2 vía OAuth (HV-04). Valida `state` (CSRF) + PKCE, intercambia
    el `code` por el perfil verificado del proveedor y resuelve tres
    caminos:

    1. El proveedor ya está vinculado a un `User` → login directo.
    2. El email no existe en el sistema → alta de cuenta nueva, verificada
       automáticamente (el proveedor ya validó el email), rol Estudiante.
    3. El email ya existe por otro medio → `VinculadorDeCuenta` rechaza la
       vinculación automática (UC-01 E4); este caso de uso adjunta un
       `link_token` de un solo uso a la excepción para que el usuario
       confirme reautenticándose con su password actual
       (`ConfirmarVinculacionOAuthUseCase`).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        user_repository: IUserRepository,
        jwt_service: JWTService,
        refresh_token_store: RefreshTokenStore,
        oauth_state_store: OAuthStateStore,
        oauth_link_store: OAuthLinkStore,
        oauth_adapter,
        vinculador_de_cuenta: VinculadorDeCuenta,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository
        self._jwt_service = jwt_service
        self._refresh_token_store = refresh_token_store
        self._state_store = oauth_state_store
        self._link_store = oauth_link_store
        self._adapter = oauth_adapter
        self._vinculador = vinculador_de_cuenta
        self._profile: OAuthProfileDTO | None = None
        self._usuario_vinculado: User | None = None

    def _validate(self, input_dto: OAuthCallbackDTO) -> None:
        estado = self._state_store.consume(state=input_dto.state)
        if estado is None or estado["proveedor"] != input_dto.proveedor:
            raise UnauthenticatedError(_ESTADO_INVALIDO_MSG)

        self._profile = self._adapter.fetch_profile(
            code=input_dto.code, code_verifier=estado["code_verifier"]
        )
        if not self._profile.email_verificado:
            raise UnauthenticatedError("El proveedor no reporta un correo verificado.")

        self._usuario_vinculado = self._user_repository.get_by_proveedor(
            self._profile.proveedor, self._profile.proveedor_uid
        )
        if self._usuario_vinculado is not None:
            return

        usuario_existente = self._user_repository.get_by_email(self._profile.email)
        try:
            self._vinculador.validar_vinculacion(usuario_existente)
        except AccountLinkingRequiresConfirmationError as exc:
            link_token = self._link_store.create_token(
                user_id=usuario_existente.id,
                proveedor=self._profile.proveedor,
                proveedor_uid=self._profile.proveedor_uid,
            )
            raise AccountLinkingRequiresConfirmationError(
                exc.message, details=[{"link_token": link_token}]
            ) from None

    def _execute_domain_logic(
        self, input_dto: OAuthCallbackDTO
    ) -> tuple[OAuthLoginResultDTO, list[DomainEvent]]:
        events: list[DomainEvent] = []

        if self._usuario_vinculado is not None:
            user = self._usuario_vinculado
        else:
            user = self._user_repository.add(
                User(
                    email=Email(self._profile.email),
                    nombre_completo=self._profile.nombre_completo,
                    rol=Rol.ESTUDIANTE,
                    password_hash=None,
                    is_active=True,
                )
            )
            self._user_repository.add_proveedor(
                ProveedorAutenticacion(
                    user_id=user.id,
                    proveedor=ProveedorTipo(self._profile.proveedor),
                    proveedor_uid=self._profile.proveedor_uid,
                )
            )
            events.append(
                UserRegistered(
                    user_id=user.id,
                    email=str(user.email),
                    nombre_completo=user.nombre_completo,
                )
            )

        if not user.is_active:
            raise ForbiddenError("Esta cuenta está deshabilitada.")

        user.last_login = datetime.now(timezone.utc)
        self._user_repository.update(user)

        tokens = self._jwt_service.generate_token_pair(user_id=user.id, rol=user.rol.value)
        refresh_claims = self._jwt_service.decode_refresh_token(tokens.refresh)
        self._refresh_token_store.register_family(user_id=user.id, jti=refresh_claims["jti"])

        events.append(UserLoggedIn(user_id=user.id))

        return OAuthLoginResultDTO(tokens=tokens), events
