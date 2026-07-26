from django.contrib.auth.hashers import make_password

from modules.authentication.application.dtos import ConfirmarRecuperacionDTO
from modules.authentication.domain.password_policy import validate_password_policy
from modules.authentication.infrastructure.password_reset_store import (
    PasswordResetTokenStore,
)
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ValidationError
from modules.users.domain.repositories import IUserRepository

_TOKEN_INVALIDO_MSG = "El enlace de recuperación es inválido o ya expiró. Solicita uno nuevo."


class ConfirmarRecuperacionUseCase(BaseUseCase[ConfirmarRecuperacionDTO, None]):
    """
    UC-01, flujo A3, paso 3c. Valida el token de un solo uso y la nueva
    contraseña, actualiza el usuario, y por seguridad cierra todas las
    sesiones activas (mismo efecto que Logout All) — un cambio de
    contraseña es una señal fuerte de que las sesiones anteriores ya no
    deben confiarse (por ejemplo, si el motivo del reseteo fue una cuenta
    comprometida).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        user_repository: IUserRepository,
        password_reset_store: PasswordResetTokenStore,
        refresh_token_store: RefreshTokenStore,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository
        self._password_reset_store = password_reset_store
        self._refresh_token_store = refresh_token_store
        self._validated_user_id = None

    def _validate(self, input_dto: ConfirmarRecuperacionDTO) -> None:
        if input_dto.password != input_dto.password_confirm:
            raise ValidationError(
                "Las contraseñas no coinciden.",
                details=[
                    {"field": "password_confirm", "message": "Las contraseñas no coinciden."}
                ],
            )

        validate_password_policy(input_dto.password)

        user_id = self._password_reset_store.peek_token(input_dto.token)
        if user_id is None:
            raise ValidationError(
                _TOKEN_INVALIDO_MSG,
                details=[{"field": "token", "message": _TOKEN_INVALIDO_MSG}],
            )
        self._validated_user_id = user_id

    def _execute_domain_logic(
        self, input_dto: ConfirmarRecuperacionDTO
    ) -> tuple[None, list[DomainEvent]]:
        # Consumir aquí (no en _validate) porque es la acción que
        # efectivamente "gasta" el token de un solo uso.
        user_id = self._password_reset_store.consume_token(input_dto.token)
        if user_id is None:
            # Caso borde: el token expiró/fue usado justo entre _validate y
            # este punto (carrera muy poco probable, pero no se asume).
            raise ValidationError(
                _TOKEN_INVALIDO_MSG,
                details=[{"field": "token", "message": _TOKEN_INVALIDO_MSG}],
            )

        user = self._user_repository.get_by_id(user_id)
        user.password_hash = make_password(input_dto.password)
        self._user_repository.update(user)

        self._refresh_token_store.revoke_all_for_user(user_id)

        return None, []
