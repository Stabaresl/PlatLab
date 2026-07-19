from datetime import datetime, timezone

from django.contrib.auth.hashers import check_password

from modules.authentication.application.dtos import LoginDTO, TokenPairDTO
from modules.authentication.domain.events import UserLoggedIn
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, UnauthenticatedError
from modules.users.domain.entities import User
from modules.users.domain.repositories import IUserRepository

_CREDENCIALES_INVALIDAS_MSG = "Credenciales inválidas."


class LoginUseCase(BaseUseCase[LoginDTO, TokenPairDTO]):
    """
    UC-01, flujo alternativo A2 (login). El mensaje de error ante
    credenciales inválidas es siempre el mismo genérico
    ("Credenciales inválidas"), sin distinguir si el correo no existe o si
    la contraseña es incorrecta — evita enumeración de usuarios, mismo
    criterio que el registro (UC-01 E1).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        user_repository: IUserRepository,
        jwt_service: JWTService,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository
        self._jwt_service = jwt_service
        self._validated_user: User | None = None

    def _validate(self, input_dto: LoginDTO) -> None:
        user = self._user_repository.get_by_email(input_dto.email)

        if user is None or user.password_hash is None:
            raise UnauthenticatedError(_CREDENCIALES_INVALIDAS_MSG)

        if not check_password(input_dto.password, user.password_hash):
            raise UnauthenticatedError(_CREDENCIALES_INVALIDAS_MSG)

        if not user.is_active:
            raise ForbiddenError("Esta cuenta está deshabilitada.")

        self._validated_user = user

    def _execute_domain_logic(
        self, input_dto: LoginDTO
    ) -> tuple[TokenPairDTO, list[DomainEvent]]:
        user = self._validated_user
        user.last_login = datetime.now(timezone.utc)
        self._user_repository.update(user)

        tokens = self._jwt_service.generate_token_pair(user_id=user.id, rol=user.rol.value)
        event = UserLoggedIn(user_id=user.id)

        return tokens, [event]
