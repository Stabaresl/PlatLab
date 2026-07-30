import re

from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, ValidationError
from modules.users.application.dtos import SolicitarInstructorDTO, SolicitudInstructorResultDTO
from modules.users.domain.entities import SolicitudInstructor
from modules.users.domain.events import InstructorVerificationRequested
from modules.users.domain.repositories import ISolicitudInstructorRepository, IUserRepository
from modules.users.domain.value_objects import Rol

_ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")

_SOLO_ESTUDIANTES_MSG = "Solo un estudiante puede solicitar convertirse en instructor."
_ORCID_INVALIDO_MSG = "El ORCID no tiene un formato válido (esperado 0000-0000-0000-0000)."
_SOLICITUD_PENDIENTE_MSG = "Ya tienes una solicitud de instructor en verificación."


class SolicitarConvertirseEnInstructorUseCase(
    BaseUseCase[SolicitarInstructorDTO, SolicitudInstructorResultDTO]
):
    """
    Crea la solicitud en estado `pendiente` y emite
    `InstructorVerificationRequested` — la verificación contra OpenAlex
    corre en un worker de Celery (ver `infrastructure/event_listeners.py`),
    nunca dentro de este mismo request/response.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        user_repository: IUserRepository,
        solicitud_repository: ISolicitudInstructorRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository
        self._solicitud_repository = solicitud_repository

    def _validate(self, input_dto: SolicitarInstructorDTO) -> None:
        if input_dto.actor_rol != Rol.ESTUDIANTE.value:
            raise ForbiddenError(_SOLO_ESTUDIANTES_MSG)

        if not _ORCID_REGEX.match(input_dto.orcid):
            raise ValidationError(
                _ORCID_INVALIDO_MSG,
                details=[{"field": "orcid", "message": _ORCID_INVALIDO_MSG}],
            )

        pendiente = self._solicitud_repository.get_pendiente_by_user_id(input_dto.actor_id)
        if pendiente is not None:
            raise ConflictError(_SOLICITUD_PENDIENTE_MSG)

        self._usuario = self._user_repository.get_by_id(input_dto.actor_id)

    def _execute_domain_logic(
        self, input_dto: SolicitarInstructorDTO
    ) -> tuple[SolicitudInstructorResultDTO, list[DomainEvent]]:
        solicitud = SolicitudInstructor(
            user_id=input_dto.actor_id,
            orcid=input_dto.orcid,
            nombre_declarado=self._usuario.nombre_completo,
            tipo=input_dto.tipo,
            institucion=input_dto.institucion,
            especialidades=input_dto.especialidades,
            motivacion=input_dto.motivacion,
        )
        creada = self._solicitud_repository.add(solicitud)

        result = SolicitudInstructorResultDTO(
            id=creada.id,
            estado=creada.estado.value,
            orcid=creada.orcid,
            created_at=creada.created_at,
        )
        event = InstructorVerificationRequested(
            solicitud_id=creada.id,
            user_id=creada.user_id,
            orcid=creada.orcid,
            nombre_declarado=creada.nombre_declarado,
        )
        return result, [event]
