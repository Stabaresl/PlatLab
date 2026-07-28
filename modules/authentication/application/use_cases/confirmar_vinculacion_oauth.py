from datetime import datetime, timezone

from django.contrib.auth.hashers import check_password

from modules.authentication.application.dtos import ConfirmarVinculacionDTO, TokenPairDTO
from modules.authentication.domain.events import OAuthAccountLinked, UserLoggedIn
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.oauth_link_store import OAuthLinkStore
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, UnauthenticatedError
from modules.users.domain.entities import ProveedorAutenticacion, ProveedorTipo, User
from modules.users.domain.repositories import IUserRepository

_CREDENCIALES_INVALIDAS_MSG = "Credenciales inválidas."
_ENLACE_INVALIDO_MSG = "El enlace de vinculación es inválido o expiró."


class ConfirmarVinculacionOAuthUseCase(BaseUseCase[ConfirmarVinculacionDTO, TokenPairDTO]):
    """
    UC-01 E4, segundo paso: el usuario reautentica con su password actual
    para autorizar la vinculación del proveedor OAuth que quedó pendiente
    en `OAuthLoginUseCase` (`VinculadorDeCuenta`). Solo aquí, tras probar
    que controla la cuenta existente, se persiste el nuevo
    `ProveedorAutenticacion`.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        user_repository: IUserRepository,
        jwt_service: JWTService,
        refresh_token_store: RefreshTokenStore,
        oauth_link_store: OAuthLinkStore,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository
        self._jwt_service = jwt_service
        self._refresh_token_store = refresh_token_store
        self._link_store = oauth_link_store
        self._pendiente: dict | None = None
        self._user: User | None = None

    def _validate(self, input_dto: ConfirmarVinculacionDTO) -> None:
        self._pendiente = self._link_store.consume_token(input_dto.link_token)
        if self._pendiente is None:
            raise UnauthenticatedError(_ENLACE_INVALIDO_MSG)

        user = self._user_repository.get_by_id(self._pendiente["user_id"])
        if user is None or user.password_hash is None:
            raise UnauthenticatedError(_CREDENCIALES_INVALIDAS_MSG)
        if not check_password(input_dto.password, user.password_hash):
            raise UnauthenticatedError(_CREDENCIALES_INVALIDAS_MSG)
        if not user.is_active:
            raise ForbiddenError("Esta cuenta está deshabilitada.")

        self._user = user

    def _execute_domain_logic(
        self, input_dto: ConfirmarVinculacionDTO
    ) -> tuple[TokenPairDTO, list[DomainEvent]]:
        user = self._user

        self._user_repository.add_proveedor(
            ProveedorAutenticacion(
                user_id=user.id,
                proveedor=ProveedorTipo(self._pendiente["proveedor"]),
                proveedor_uid=self._pendiente["proveedor_uid"],
            )
        )

        user.last_login = datetime.now(timezone.utc)
        self._user_repository.update(user)

        tokens = self._jwt_service.generate_token_pair(user_id=user.id, rol=user.rol.value)
        refresh_claims = self._jwt_service.decode_refresh_token(tokens.refresh)
        self._refresh_token_store.register_family(user_id=user.id, jti=refresh_claims["jti"])

        events = [
            OAuthAccountLinked(user_id=user.id, proveedor=self._pendiente["proveedor"]),
            UserLoggedIn(user_id=user.id),
        ]
        return tokens, events
