from modules.authentication.application.dtos import SolicitarRecuperacionDTO
from modules.authentication.domain.events import PasswordResetRequested
from modules.authentication.infrastructure.password_reset_store import (
    PasswordResetTokenStore,
)
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.users.domain.repositories import IUserRepository
from modules.users.domain.value_objects import Email


class SolicitarRecuperacionUseCase(BaseUseCase[SolicitarRecuperacionDTO, None]):
    """
    UC-01, flujo A3, pasos 1-2. La respuesta es siempre exitosa (None) sin
    importar si el correo existe o no en el sistema — evitar enumeración de
    usuarios aquí es más importante todavía que en login/registro, ya que
    este endpoint no exige estar autenticado ni conocer una contraseña.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        user_repository: IUserRepository,
        password_reset_store: PasswordResetTokenStore,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository
        self._password_reset_store = password_reset_store

    def _validate(self, input_dto: SolicitarRecuperacionDTO) -> None:
        Email(input_dto.email)  # lanza ValidationError si el formato es inválido

    def _execute_domain_logic(
        self, input_dto: SolicitarRecuperacionDTO
    ) -> tuple[None, list[DomainEvent]]:
        user = self._user_repository.get_by_email(input_dto.email)

        if user is None or not user.is_active:
            # Silenciosamente no hace nada — misma respuesta que el caso
            # exitoso, a propósito (anti-enumeración).
            return None, []

        token = self._password_reset_store.create_token(user.id)
        event = PasswordResetRequested(
            user_id=user.id,
            email=str(user.email),
            nombre_completo=user.nombre_completo,
            token=token,
        )
        return None, [event]
