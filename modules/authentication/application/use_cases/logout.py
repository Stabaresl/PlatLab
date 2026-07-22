import uuid

from modules.authentication.application.dtos import LogoutDTO
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent


class LogoutUseCase(BaseUseCase[LogoutDTO, None]):
    """
    RF-02: invalida únicamente la sesión (familia de tokens) a la que
    pertenece el refresh token recibido — el resto de sesiones activas del
    usuario en otros dispositivos no se ven afectadas.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        jwt_service: JWTService,
        refresh_token_store: RefreshTokenStore,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._jwt_service = jwt_service
        self._refresh_token_store = refresh_token_store
        self._validated_claims: dict | None = None

    def _validate(self, input_dto: LogoutDTO) -> None:
        self._validated_claims = self._jwt_service.decode_refresh_token(input_dto.refresh)

    def _execute_domain_logic(self, input_dto: LogoutDTO) -> tuple[None, list[DomainEvent]]:
        jti = self._validated_claims["jti"]
        family_id = self._refresh_token_store.get_family_id(jti)

        if family_id:
            self._refresh_token_store.revoke_family(family_id)

        return None, []


class LogoutAllUseCase(BaseUseCase[LogoutDTO, None]):
    """
    HE-14: invalida TODAS las sesiones activas del usuario (todos los
    dispositivos), no solo la que envió la petición. Identifica al usuario
    a partir del `sub` del propio refresh token recibido — no depende de
    `JWTAuthenticationMiddleware` (aún no construido en el Sprint 1).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        jwt_service: JWTService,
        refresh_token_store: RefreshTokenStore,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._jwt_service = jwt_service
        self._refresh_token_store = refresh_token_store
        self._validated_claims: dict | None = None

    def _validate(self, input_dto: LogoutDTO) -> None:
        self._validated_claims = self._jwt_service.decode_refresh_token(input_dto.refresh)

    def _execute_domain_logic(self, input_dto: LogoutDTO) -> tuple[None, list[DomainEvent]]:
        user_id = uuid.UUID(self._validated_claims["sub"])
        self._refresh_token_store.revoke_all_for_user(user_id)

        return None, []
