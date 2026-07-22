import uuid

from modules.authentication.application.dtos import RefreshRequestDTO, TokenPairDTO
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent


class RefreshTokenUseCase(BaseUseCase[RefreshRequestDTO, TokenPairDTO]):
    """
    RF-07: rota el refresh token en cada uso y entrega un par de tokens
    nuevo. Si el refresh recibido ya no es el vigente de su familia (fue
    rotado antes — posible robo/replay), `RefreshTokenStore` detecta el
    reuso y revoca toda la sesión (ver seguridad.md §2).
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

    def _validate(self, input_dto: RefreshRequestDTO) -> None:
        # Verifica firma y expiración del token (lanza UnauthenticatedError
        # si es inválido) — la validación de que sea el "vigente" de su
        # familia ocurre en _execute_domain_logic, ya que esa comprobación
        # muta el estado en Redis (rotación), no es una simple lectura.
        self._validated_claims = self._jwt_service.decode_refresh_token(input_dto.refresh)

    def _execute_domain_logic(
        self, input_dto: RefreshRequestDTO
    ) -> tuple[TokenPairDTO, list[DomainEvent]]:
        old_jti = self._validated_claims["jti"]
        user_id = uuid.UUID(self._validated_claims["sub"])
        rol = self._validated_claims["rol"]

        new_tokens = self._jwt_service.generate_token_pair(user_id=user_id, rol=rol)
        new_claims = self._jwt_service.decode_refresh_token(new_tokens.refresh)

        # Puede lanzar TokenReuseDetectedError o InvalidCredentialsError —
        # en ese caso los tokens recién generados simplemente se descartan,
        # no hay nada que revertir (esto no toca Postgres/UnitOfWork).
        self._refresh_token_store.validate_and_rotate(jti=old_jti, new_jti=new_claims["jti"])

        return new_tokens, []
