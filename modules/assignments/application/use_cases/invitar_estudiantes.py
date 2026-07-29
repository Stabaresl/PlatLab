from modules.assignments.application.dtos import (
    InvitacionResultDTO,
    InvitarEstudiantesDTO,
    InvitarEstudiantesResultDTO,
)
from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.events import AssignmentInvited
from modules.assignments.domain.exceptions import InvalidExpirationError
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.assignments.domain.value_objects import VentanaVencimiento
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ForbiddenError,
    NotFoundError,
)
from modules.users.domain.repositories import IUserRepository

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "Solo el instructor dueño del laboratorio puede invitar estudiantes."
_LAB_NO_PUBLICADO_MSG = "El laboratorio debe estar publicado para asignarlo."
_VENCIMIENTO_INVALIDO_MSG = "La fecha de vencimiento debe ser posterior al momento actual."


class InvitarEstudiantesUseCase(
    BaseUseCase[InvitarEstudiantesDTO, InvitarEstudiantesResultDTO]
):
    """
    UC-06, api.md §6 `POST /assignments/invitations/`: invita uno o más
    estudiantes (por email o username) a un laboratorio publicado y
    propio del instructor. No falla completo si algún identificador no
    existe o ya tiene asignación vigente (UC-06 E1/E2) — informa el
    resultado por estudiante en la respuesta.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        asignacion_repository: IAsignacionRepository,
        laboratorio_repository: ILaboratorioRepository,
        user_repository: IUserRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._asignacion_repository = asignacion_repository
        self._laboratorio_repository = laboratorio_repository
        self._user_repository = user_repository

    def _validate(self, input_dto: InvitarEstudiantesDTO) -> None:
        if input_dto.actor_rol != "instructor":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)
        if laboratorio.instructor_id != input_dto.actor_id:
            raise ForbiddenError(_SIN_PERMISO_MSG)
        if laboratorio.estado != EstadoLaboratorio.PUBLICADO:
            raise BusinessRuleViolationError(_LAB_NO_PUBLICADO_MSG)

        if input_dto.fecha_vencimiento is not None:
            ventana = VentanaVencimiento(fecha=input_dto.fecha_vencimiento)
            if ventana.ya_vencio():
                raise InvalidExpirationError(_VENCIMIENTO_INVALIDO_MSG)

    def _execute_domain_logic(
        self, input_dto: InvitarEstudiantesDTO
    ) -> tuple[InvitarEstudiantesResultDTO, list[DomainEvent]]:
        resultados = []
        eventos: list[DomainEvent] = []

        for identificador in input_dto.estudiantes:
            estudiante = self._user_repository.get_by_email(
                identificador
            ) or self._user_repository.get_by_username(identificador)

            if estudiante is None:
                resultados.append(
                    InvitacionResultDTO(identificador=identificador, resultado="no_encontrado")
                )
                continue

            if self._asignacion_repository.existe_vigente(
                estudiante.id, input_dto.laboratorio_id
            ):
                resultados.append(
                    InvitacionResultDTO(identificador=identificador, resultado="ya_vigente")
                )
                continue

            asignacion = Asignacion(
                estudiante_id=estudiante.id,
                laboratorio_id=input_dto.laboratorio_id,
                instructor_id=input_dto.actor_id,
                fecha_vencimiento=input_dto.fecha_vencimiento,
            )
            guardada = self._asignacion_repository.add(asignacion)
            resultados.append(
                InvitacionResultDTO(
                    identificador=identificador, resultado="invitado", asignacion_id=guardada.id
                )
            )
            eventos.append(
                AssignmentInvited(
                    asignacion_id=guardada.id,
                    estudiante_id=guardada.estudiante_id,
                    laboratorio_id=guardada.laboratorio_id,
                )
            )

        return InvitarEstudiantesResultDTO(invitaciones=resultados), eventos
