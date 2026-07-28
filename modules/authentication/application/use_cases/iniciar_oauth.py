import secrets

from modules.authentication.application.dtos import (
    OAuthAuthorizeDTO,
    OAuthAuthorizeResultDTO,
)
from modules.authentication.infrastructure.oauth_adapters import generar_par_pkce
from modules.authentication.infrastructure.oauth_state_store import OAuthStateStore
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent


class IniciarOAuthUseCase(BaseUseCase[OAuthAuthorizeDTO, OAuthAuthorizeResultDTO]):
    """
    UC-01 A1, paso 1a (HV-04): genera `state` (CSRF) + par PKCE, los guarda
    server-side y construye la URL de autorización del proveedor. No toca
    Postgres — el commit de `BaseUseCase` sobre `unit_of_work` es un no-op,
    igual criterio que `RefreshTokenUseCase` (mismo patrón ya usado para
    operaciones que solo tocan Redis).
    """

    def __init__(
        self, unit_of_work, event_dispatcher, oauth_adapter, oauth_state_store: OAuthStateStore
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._adapter = oauth_adapter
        self._state_store = oauth_state_store

    def _validate(self, input_dto: OAuthAuthorizeDTO) -> None:
        pass  # el proveedor ya fue resuelto por la vista al elegir el adapter

    def _execute_domain_logic(
        self, input_dto: OAuthAuthorizeDTO
    ) -> tuple[OAuthAuthorizeResultDTO, list[DomainEvent]]:
        state = secrets.token_urlsafe(24)
        code_verifier, code_challenge = generar_par_pkce()
        self._state_store.save(
            state=state, code_verifier=code_verifier, proveedor=input_dto.proveedor
        )
        authorize_url = self._adapter.build_authorize_url(
            state=state, code_challenge=code_challenge
        )
        result = OAuthAuthorizeResultDTO(authorize_url=authorize_url, state=state)
        return result, []
